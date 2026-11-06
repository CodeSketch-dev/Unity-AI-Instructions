import pytest

from app.automation.meshy_worker import MeshyWebWorker, WorkerResult, WorkerState
from app.core.database import Database
from app.core.pipeline import PipelineService, acquire_runner_lock, runner_lock_held


class FakeWorker(MeshyWebWorker):
    def __init__(self, script):
        self.script = dict(script)
        self.calls = []

    def run_one(self, account_id, image_path, *, account_key=None, wait_for_login_ms=120_000):
        self.calls.append((account_id, account_key))
        return WorkerResult(self.script.get(account_id, WorkerState.GENERATING), account_id, "msg")


def make(tmp_path, script, n=2):
    db = Database(tmp_path / "t.sqlite3")
    for i in range(n):
        db.add_account(f"a{i}@x.com", None, i + 1, str(tmp_path / f"p{i}"))
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    return db, PipelineService(db, FakeWorker(script)), img


def test_enqueue_rejects_bad_files(tmp_path):
    db, svc, img = make(tmp_path, {})
    (tmp_path / "n.txt").write_text("x")
    for bad in (tmp_path / "n.txt", tmp_path / "missing.png"):
        with pytest.raises(ValueError):
            svc.enqueue(str(bad))
    assert svc.enqueue(str(img)) == 1


def test_success_completes_job_with_email_key(tmp_path):
    db, svc, img = make(tmp_path, {})
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1
    assert db.get_job(jid).status == "Completed"
    assert svc.worker.calls[0][1].endswith("@x.com")  # key is the email, never the password


def test_quota_rotates_and_marks_cooldown(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    accounts = {a.id: a for a in db.list_accounts()}
    assert accounts[1].status == "Quota Limited" and accounts[1].cooldown_until
    assert db.get_job(jid).status == "Completed" and db.get_job(jid).account_id == 2


def test_all_exhausted_keeps_job_pending_without_spinning(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1
    job = db.get_job(jid)
    assert job.status == "Pending" and "waiting" in job.error
    calls = len(svc.worker.calls)
    assert svc.run_pending() == 0 and len(svc.worker.calls) == calls


def test_invalid_credentials_and_verification_mark_accounts(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.INVALID_CREDENTIALS, 2: WorkerState.MANUAL_VERIFICATION})
    svc.enqueue(str(img))
    svc.run_pending()
    a = {x.id: x for x in db.list_accounts()}
    assert a[1].authorized is False and a[1].status == "Invalid credentials"
    assert a[2].status == "Needs verification"


def test_ordinary_failure_retries_then_fails(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.FAILED, 2: WorkerState.FAILED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status == "Failed" and db.get_job(jid).retries == 2


def test_interrupted_job_recovers_to_pending(tmp_path):
    db, svc, img = make(tmp_path, {})
    jid = svc.enqueue(str(img))
    db.update_job(jid, status="Generating")
    svc.run_pending()
    assert db.get_job(jid).status == "Completed"


def test_runner_lock_acquired_once_per_process(tmp_path):
    lock = tmp_path / "r.lock"
    assert acquire_runner_lock(lock) is True
    assert runner_lock_held(lock) is False  # we own it


def test_browser_closed_when_queue_becomes_empty(tmp_path):
    db, svc, img = make(tmp_path, {})
    released = []
    svc.worker.release_account = lambda account_id: released.append(account_id)
    svc.enqueue(str(img)); svc.enqueue(str(img))
    svc.run_pending()
    assert len(released) == 1  # only after the last job, not between jobs
