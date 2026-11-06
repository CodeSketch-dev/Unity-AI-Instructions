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
