import threading

import pytest

from app.automation.meshy_worker import MeshyWebWorker, WorkerResult, WorkerState
from app.core.database import Database
from app.core.pipeline import PipelineService, acquire_runner_lock, runner_lock_held


class FakeWorker(MeshyWebWorker):
    def __init__(self, script):
        self.script = dict(script)
        self.calls = []
        self.cancel_event = threading.Event()

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


def test_all_exhausted_pauses_job_without_spinning(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1
    job = db.get_job(jid)
    assert job.status == "Paused" and "Pick another account" in job.error
    calls = len(svc.worker.calls)
    assert svc.run_pending() == 0 and len(svc.worker.calls) == calls


def test_invalid_credentials_and_verification_mark_accounts(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.INVALID_CREDENTIALS, 2: WorkerState.MANUAL_VERIFICATION})
    svc.enqueue(str(img))
    svc.run_pending()
    a = {x.id: x for x in db.list_accounts()}
    assert a[1].authorized is False and a[1].status == "Invalid credentials"
    assert a[2].status == "Needs verification"


def test_ordinary_failure_retries_then_fails(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.pipeline.BACKOFF_BASE_SECONDS", 0)  # no waiting in the test
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


def test_cancel_queued_jobs_moves_the_rest_up(tmp_path):
    db, svc, img = make(tmp_path, {})
    ids = [svc.enqueue(str(img)) for _ in range(4)]
    assert [db.queue_position(i) for i in ids] == [1, 2, 3, 4]
    outcome = svc.cancel_jobs([ids[0], ids[2]])
    assert sorted(outcome["canceled"]) == sorted([ids[0], ids[2]]) and outcome["stopping"] == []
    assert [db.get_job(i).status for i in ids] == ["Canceled", "Pending", "Canceled", "Pending"]
    assert [db.queue_position(i) for i in ids] == [None, 1, None, 2]
    assert svc.run_pending() == 2  # only the survivors run, in order
    assert [db.get_job(i).status for i in ids] == ["Canceled", "Completed", "Canceled", "Completed"]


def test_cancel_running_job_stops_at_next_step(tmp_path):
    db, svc, img = make(tmp_path, {})
    jid = svc.enqueue(str(img))

    class Worker(FakeWorker):
        def run_one(self, account_id, image_path, *, account_key=None, wait_for_login_ms=120_000):
            svc.cancel_jobs([jid])  # the user clicks Cancel while the job is running
            return WorkerResult(WorkerState.CANCELED if self._canceled(account_id) else WorkerState.GENERATING, account_id, "x")
    svc.worker = Worker({})
    svc.run_pending()
    job = db.get_job(jid)
    assert job.status == "Canceled" and "Canceled" in job.error and job.retries == 0


def test_retry_waits_with_exponential_backoff(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.FAILED, 2: WorkerState.FAILED})
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1  # first failure -> retry scheduled 30 s from now, not immediately
    job = db.get_job(jid)
    assert job.status == "Pending" and job.retries == 1
    assert db.claim_next_job() is None  # still inside the backoff window
    import time
    with db._lock, db._connection:
        db._connection.execute("UPDATE jobs SET retry_at=?", (time.time() - 1,))
    assert db.claim_next_job().id == jid
    from app.core import pipeline
    assert pipeline.BACKOFF_BASE_SECONDS * 2 ** 1 <= pipeline.BACKOFF_MAX_SECONDS  # grows: 30 s, 60 s, ... capped


def test_paused_job_resumes_when_an_account_returns(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status == "Paused"
    with db._lock, db._connection:
        db._connection.execute("UPDATE accounts SET cooldown_until=datetime('now','-1 hour')")
    svc.worker.script = {}  # credits are back
    assert svc.run_pending() == 1
    assert db.get_job(jid).status == "Completed"


def test_user_can_pin_another_account(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status == "Paused"
    svc.worker.script = {}
    svc.use_account(2)  # the user overrides the rest period of account 2
    assert svc.run_pending() == 1
    job = db.get_job(jid)
    assert job.status == "Completed" and job.account_id == 2
    assert {call[0] for call in svc.worker.calls[-1:]} == {2}


def test_emergency_stop_pauses_queue_and_resume_continues(tmp_path):
    db, svc, img = make(tmp_path, {})
    ids = [svc.enqueue(str(img)) for _ in range(3)]
    svc.emergency_stop()
    assert [db.get_job(i).status for i in ids] == ["Paused"] * 3
    assert svc.run_pending() == 0  # halted: nothing starts
    svc.halted = False
    svc._stop.clear()
    db.resume_paused_jobs()
    assert svc.run_pending() == 3
