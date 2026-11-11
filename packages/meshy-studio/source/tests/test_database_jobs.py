from pathlib import Path

from app.core.database import Database
from app.core.models import JobStatus


def test_active_jobs_are_recovered_after_restart(tmp_path: Path):
    path = tmp_path / "studio.db"
    first = Database(path)
    job_id = first.create_job(str(tmp_path / "input.png"), "note")
    first.update_job(job_id, status=JobStatus.GENERATING.value, meshy_task_id="task-1")
    first.close()

    second = Database(path)
    recovered = second.recover_jobs()
    assert recovered == 1
    job = second.get_job(job_id)
    assert job.status == JobStatus.PENDING.value
    assert job.meshy_task_id == "task-1"


def test_submitted_job_cannot_be_requeued_before_server_reconciliation(tmp_path: Path):
    db = Database(tmp_path / "jobs.sqlite3")
    image = tmp_path / "source.png"; image.write_bytes(b"x")
    job_id = db.create_job(str(image))
    db.update_job(job_id, status=JobStatus.FAILED.value, submitted=1, meshy_task_id="remote-42")
    assert db.requeue_jobs([job_id]) == 0
    saved = db.get_job(job_id)
    assert saved.status == JobStatus.FAILED.value and saved.submitted == 1 and saved.meshy_task_id == "remote-42"



def test_account_cooldown_and_claim_next_job(tmp_path):
    from app.core.database import Database
    db = Database(tmp_path / "t.sqlite3")
    aid = db.add_account("a@x.com", None, 1, str(tmp_path / "p"))
    db.mark_account(aid, "Quota Limited", cooldown_hours=24)
    acc = db.list_accounts()[0]
    assert acc.status == "Quota Limited" and acc.cooldown_until
    assert db.release_expired_cooldowns() == 0
    with db._lock, db._connection:
        db._connection.execute("UPDATE accounts SET cooldown_until=datetime('now','-1 hour')")
    assert db.release_expired_cooldowns() == 1
    assert db.list_accounts()[0].status == "Ready"
    j1 = db.create_job("a.png"); db.create_job("b.png")
    assert db.claim_next_job().id == j1
    assert db.get_job(j1).status == "Checking Account"
    assert db.claim_next_job().image_path == "b.png"
    assert db.claim_next_job() is None


def test_existing_db_gets_cooldown_column(tmp_path):
    import sqlite3
    from app.core.database import Database
    path = tmp_path / "old.sqlite3"
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, recovery_email TEXT, priority INTEGER NOT NULL DEFAULT 100, profile_path TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'Not connected', session_valid INTEGER NOT NULL DEFAULT 0, authorized INTEGER NOT NULL DEFAULT 1, active_jobs INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    c.commit(); c.close()
    Database(path).add_account("z@x.com", None, 1, "p")


LEGACY_SCHEMA = """
CREATE TABLE accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE COLLATE NOCASE, recovery_email TEXT,
  priority INTEGER NOT NULL DEFAULT 100, profile_path TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'Not connected',
  session_valid INTEGER NOT NULL DEFAULT 0, authorized INTEGER NOT NULL DEFAULT 1, active_jobs INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, image_path TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', status TEXT NOT NULL,
  account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL, meshy_task_id TEXT, progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
  retries INTEGER NOT NULL DEFAULT 0, error TEXT, result_path TEXT, meshy_url TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE models (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE, name TEXT NOT NULL,
  source_image TEXT NOT NULL, account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL, status TEXT NOT NULL, file_path TEXT, meshy_task_id TEXT,
  meshy_url TEXT, thumbnail_path TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
INSERT INTO accounts(email, profile_path, status) VALUES ('old@x.com', 'p1', 'Ready');
INSERT INTO jobs(image_path, status) VALUES ('old.png', 'Pending');
"""


def test_legacy_database_is_migrated_without_losing_data(tmp_path):
    import sqlite3
    from app.core.database import MIGRATIONS, Database
    path = tmp_path / "legacy.sqlite3"
    raw = sqlite3.connect(path)
    raw.executescript(LEGACY_SCHEMA)
    raw.commit(); raw.close()
    db = Database(path)
    assert db.schema_version() == len(MIGRATIONS)
    assert [a.email for a in db.list_accounts()] == ["old@x.com"] and db.get_job(1).image_path == "old.png"
    assert db.get_job(1).submitted == 0 and db.list_accounts()[0].credit_balance is None  # unknown, not 0
    db.close()
    again = Database(path)  # opening twice is a no-op
    assert again.schema_version() == len(MIGRATIONS) and len(again.list_jobs()) == 1
    again.add_model(1, "m", "old.png", None, "f.glb", "folder", "GLB", 3, 4, None)  # new columns work after migration
    assert again.list_models()[0]["triangles"] == 3


def test_everything_survives_closing_and_reopening(tmp_path):
    from app.core.database import Database
    db = Database(tmp_path / "t.sqlite3")
    account = db.add_account("a@x.com", None, 1, str(tmp_path / "p"))
    db.set_credit(account, 0)  # a real zero must be stored as 0, distinct from NULL (unknown)
    job = db.create_job("a.png", "note")
    db.update_job(job, status="Paused", submitted=1, progress=40)
    db.upsert_mailbox("m@purelymail.com", "purelymail", "2027-01-01 00:00:00")
    db.close()
    db = Database(tmp_path / "t.sqlite3")
    assert db.list_accounts()[0].credit_balance == 0 and db.list_accounts()[0].credit_checked_at
    saved = db.get_job(job)
    assert (saved.status, saved.submitted, saved.progress, saved.note) == ("Paused", 1, 40, "note")
    assert db.list_mailboxes()[0]["expires_at"] == "2027-01-01 00:00:00"


def test_wal_mode_and_concurrent_threads_do_not_corrupt_the_queue(tmp_path):
    import threading
    from app.core.database import Database
    db = Database(tmp_path / "t.sqlite3")
    assert db._connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    ids = [db.create_job(f"{i}.png") for i in range(60)]
    claimed, lock = [], threading.Lock()

    def worker():
        while (job := db.claim_next_job()) is not None:
            with lock:
                claimed.append(job.id)
    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert sorted(claimed) == ids  # every job claimed exactly once, none twice
