import threading
import time
from pathlib import Path

import pytest

from app.automation.meshy_worker import WorkerResult, WorkerState
from app.core import pipeline as pipeline_module
from app.core.database import Database
from app.core.pipeline import PipelineService, acquire_runner_lock, runner_lock_held, validate_image
from glb_fixture import make_mesh_glb


class FakeWorker:
    """Scripted worker. script[account_id] = state or callable(job_image) -> WorkerResult. Writes real GLBs on success."""

    def __init__(self, out_dir: Path, script=None, *, submit_before: set | None = None):
        self.out_dir, self.script = out_dir, dict(script or {})
        self.submit_before = submit_before or set()  # account ids whose failures happen AFTER Generate was clicked
        self.calls, self.released, self.released_all = [], [], False
        self.cancel_event = threading.Event()
        self.cancel_probe = self.on_credits = self.on_submitted = self.on_progress = self.deadline = None
        self.lock = threading.Lock()

    def request_cancel(self):
        self.cancel_event.set()

    def release_account(self, account_id):
        self.released.append(account_id)

    def release_all(self):
        self.released_all = True

    def run_one(self, account_id, image_path, *, account_key=None, wait_for_login_ms=0):
        with self.lock:
            self.calls.append((account_id, account_key, Path(image_path).name))
        action = self.script.get(account_id, WorkerState.COMPLETED)
        if callable(action):
            return action(self, account_id, image_path)
        if account_id in self.submit_before and self.on_submitted:
            self.on_submitted(account_id)
        if action == WorkerState.COMPLETED:
            folder = self.out_dir / f"{Path(image_path).stem}_{account_id}"
            glb = make_mesh_glb(folder / f"{Path(image_path).stem}.glb", 12)
            (folder / "textures").mkdir(exist_ok=True)
            (folder / "textures" / "x_basecolor.png").write_bytes(b"png")
            (folder / "x.fbx").write_bytes(b"fbx")
            if self.on_progress:
                self.on_progress(85)
            return WorkerResult(WorkerState.COMPLETED, account_id, "ok", str(glb))
        return WorkerResult(action, account_id, f"{action.value} by script")


def make(tmp_path, script=None, n=2, **kw):
    db = Database(tmp_path / "t.sqlite3")
    for i in range(n):
        db.add_account(f"a{i}@x.com", None, i + 1, str(tmp_path / f"p{i}"))
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    worker = FakeWorker(tmp_path / "out", script, submit_before=kw.pop("submit_before", None))
    return db, PipelineService(db, worker, **kw), img


# ---- validation ---------------------------------------------------------------------------------------------------
def test_validate_image_rules(tmp_path):
    (tmp_path / "n.txt").write_text("x")
    (tmp_path / "empty.png").write_bytes(b"")
    (tmp_path / "big.png").write_bytes(b"0" * (21 * 1024 * 1024))
    for bad, text in (("n.txt", "PNG"), ("missing.png", "does not exist"), ("empty.png", "empty"), ("big.png", "20 MB")):
        with pytest.raises(ValueError, match=text):
            validate_image(tmp_path / bad)
    (tmp_path / "ok.WEBP").write_bytes(b"x")
    assert validate_image(tmp_path / "ok.WEBP").name == "ok.WEBP"


# ---- happy path / verification ------------------------------------------------------------------------------------
def test_completed_requires_a_valid_output_and_fills_the_library(tmp_path):
    db, svc, img = make(tmp_path)
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1
    job = db.get_job(jid)
    assert job.status == "Completed" and job.progress == 100 and job.finished_at and job.started_at
    model = db.list_models()[0]
    assert model["triangles"] == 12 and model["formats"] == "FBX,GLB" and model["thumbnail_path"].endswith("basecolor.png")
    assert svc.worker.calls[0][1].endswith("@x.com")  # credentials are looked up by e-mail, never passed as the key


def test_missing_or_invalid_output_is_never_completed(tmp_path):
    db, svc, img = make(tmp_path, {1: lambda w, a, i: WorkerResult(WorkerState.COMPLETED, a, "claims success", str(tmp_path / "nope.glb"))})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status == "Failed" and "verification failed" in db.get_job(jid).error
    assert db.list_models() == []
    bad = tmp_path / "bad.glb"
    bad.write_bytes(b"not a glb")
    svc.worker.script = {1: lambda w, a, i: WorkerResult(WorkerState.COMPLETED, a, "x", str(bad))}
    svc.worker.script[2] = svc.worker.script[1]
    jid2 = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid2).status == "Failed"


def test_worker_without_output_cannot_complete_a_job(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.GENERATING, 2: WorkerState.GENERATING})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status != "Completed"


# ---- accounts / credits -------------------------------------------------------------------------------------------
def test_quota_requeues_the_job_onto_the_next_account(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    a = {x.id: x for x in db.list_accounts()}
    assert a[1].status == "Quota Limited" and a[1].cooldown_until
    job = db.get_job(jid)
    assert job.status == "Completed" and job.account_id == 2 and job.retries == 0  # no retry budget burnt, not submitted twice
    assert [c[0] for c in svc.worker.calls] == [1, 2]


def test_all_accounts_exhausted_pauses_without_spinning(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    job = db.get_job(jid)
    assert job.status == "Pending"  # requeued; but no usable account is left, so nothing runs
    calls = len(svc.worker.calls)
    assert svc.run_pending() == 0 and len(svc.worker.calls) == calls


def test_paused_job_resumes_when_an_account_returns(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.pause_jobs([jid])
    assert db.get_job(jid).status == "Paused" and svc.run_pending() == 0
    svc.resume_jobs([jid])
    svc.run_pending()
    with db._lock, db._connection:
        db._connection.execute("UPDATE accounts SET cooldown_until=datetime('now','-1 hour')")
    svc.worker.script = {}
    assert svc.run_pending() == 1 and db.get_job(jid).status == "Completed"


def test_invalid_credentials_and_verification_mark_accounts(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.INVALID_CREDENTIALS, 2: WorkerState.MANUAL_VERIFICATION}, n=3)
    jid = svc.enqueue(str(img))
    svc.run_pending()
    a = {x.id: x for x in db.list_accounts()}
    assert a[1].authorized is False and a[1].status == "Invalid credentials"
    assert a[2].status == "Needs verification" and a[3].status == "Not connected"
    job = db.get_job(jid)
    assert job.status == "Paused" and job.account_id == 2 and "CAPTCHA" in job.error
    assert [call[0] for call in svc.worker.calls] == [1, 2]  # never rotates to account 3
    svc.resume_jobs([jid])
    assert svc.manual_account_id == 2 and db.get_job(jid).status == "Pending"


def test_user_can_pin_another_account_and_failure_pauses_instead_of_falling_through(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.QUOTA_LIMITED, 2: WorkerState.QUOTA_LIMITED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    svc.worker.script = {}
    svc.use_account(2)
    svc.run_pending()
    job = db.get_job(jid)
    assert job.status == "Completed" and job.account_id == 2
    svc.worker.script = {2: WorkerState.QUOTA_LIMITED}
    j2 = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(j2).status == "Paused" and "Pick another account" in db.get_job(j2).error


# ---- retry / idempotency ------------------------------------------------------------------------------------------
def test_failure_before_submission_retries_with_backoff(tmp_path):
    db, svc, img = make(tmp_path, {1: WorkerState.FAILED, 2: WorkerState.FAILED})
    jid = svc.enqueue(str(img))
    assert svc.run_pending() == 1
    job = db.get_job(jid)
    assert job.status == "Pending" and job.retries == 1
    assert db.claim_next_job() is None  # still inside the backoff window
    assert pipeline_module.BACKOFF_BASE_SECONDS * 2 <= pipeline_module.BACKOFF_MAX_SECONDS
    with db._lock, db._connection:
        db._connection.execute("UPDATE jobs SET retry_at=?", (time.time() - 1,))
    assert db.claim_next_job().id == jid


def test_retries_are_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_module, "BACKOFF_BASE_SECONDS", 0)
    db, svc, img = make(tmp_path, {1: WorkerState.FAILED, 2: WorkerState.FAILED})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(jid).status == "Failed" and db.get_job(jid).retries == 2


def test_failure_after_submission_is_never_retried_automatically(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_module, "BACKOFF_BASE_SECONDS", 0)
    db, svc, img = make(tmp_path, {1: WorkerState.FAILED, 2: WorkerState.FAILED}, submit_before={1, 2})
    jid = svc.enqueue(str(img))
    svc.run_pending()
    job = db.get_job(jid)
    assert job.status == "Failed" and job.submitted == 1 and "not retried automatically" in job.error
    assert len(svc.worker.calls) == 1  # exactly one attempt = one paid generation at most


def test_restart_does_not_resubmit_a_submitted_job(tmp_path):
    db, svc, img = make(tmp_path)
    submitted = svc.enqueue(str(img))
    fresh = svc.enqueue(str(img))
    db.update_job(submitted, status="Generating", submitted=1)
    db.update_job(fresh, status="Uploading", submitted=0)
    assert db.recover_jobs() == 1  # only the unsubmitted one goes back to the queue
    assert db.get_job(submitted).status == "Failed" and "not re-submitted" in db.get_job(submitted).error
    assert db.get_job(fresh).status == "Pending"


def test_worker_crash_does_not_kill_the_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline_module, "BACKOFF_BASE_SECONDS", 0)

    def boom(worker, account_id, image):
        raise RuntimeError("driver exploded")
    db, svc, img = make(tmp_path, {1: boom, 2: boom})
    bad = svc.enqueue(str(img))
    svc.run_pending()
    assert db.get_job(bad).status == "Failed"
    svc.worker.script = {}
    good = svc.enqueue(str(img))
    assert svc.run_pending() == 1 and db.get_job(good).status == "Completed"


def test_background_stop_cancels_waits_and_releases_worker_resources(tmp_path):
    entered = threading.Event()

    def blocking(worker, account_id, image):
        entered.set()
        assert worker.cancel_event.wait(3)
        return WorkerResult(WorkerState.CANCELED, account_id, "stopped")

    db, svc, img = make(tmp_path, {1: blocking}, n=1, poll_seconds=0.01)
    job_id = svc.enqueue(str(img))
    svc.start_background()
    assert entered.wait(2)
    assert svc.stop(cancel_running=True, wait_seconds=2) is True
    assert not any(thread.is_alive() for thread in svc._threads)
    assert svc.worker.released_all is True and db.get_job(job_id).status == "Canceled"


# ---- cancel / pause / emergency stop -----------------------------------------------------------------------------
def test_cancel_queued_jobs_moves_the_rest_up(tmp_path):
    db, svc, img = make(tmp_path)
    ids = [svc.enqueue(str(img)) for _ in range(4)]
    assert [db.queue_position(i) for i in ids] == [1, 2, 3, 4]
    outcome = svc.cancel_jobs([ids[0], ids[2]])
    assert sorted(outcome["canceled"]) == sorted([ids[0], ids[2]]) and outcome["stopping"] == []
    assert [db.queue_position(i) for i in ids] == [None, 1, None, 2]
    assert svc.run_pending() == 2
    assert [db.get_job(i).status for i in ids] == ["Canceled", "Completed", "Canceled", "Completed"]


def test_cancel_running_job_stops_at_next_step_and_is_local_only(tmp_path):
    db, svc, img = make(tmp_path, submit_before=set())
    jid = svc.enqueue(str(img))

    def cancelled_midway(worker, account_id, image):
        worker.on_submitted(account_id)
        svc.cancel_jobs([jid])  # the user clicks Cancel while the job runs
        return WorkerResult(WorkerState.CANCELED if worker.cancel_event.is_set() else WorkerState.COMPLETED, account_id, "x")
    svc.worker.script = {1: cancelled_midway, 2: cancelled_midway}
    svc.run_pending()
    job = db.get_job(jid)
    assert job.status == "Canceled" and job.submitted == 1 and job.retries == 0


def test_emergency_stop_pauses_queue_cancels_running_and_blocks_new_jobs(tmp_path):
    db, svc, img = make(tmp_path)
    ids = [svc.enqueue(str(img)) for _ in range(3)]
    running = ids[0]
    db.update_job(running, status="Generating")
    svc._current[0] = running
    svc.emergency_stop()
    assert svc.worker.cancel_event.is_set() and svc.halted is True
    assert db.get_job(running).status == "Cancel Requested"
    assert [db.get_job(i).status for i in ids[1:]] == ["Paused", "Paused"]
    assert svc.run_pending() == 0  # nothing new is sent
    svc._current.clear()
    svc.halted = False
    svc._stop.clear()
    db.resume_paused_jobs()
    assert svc.run_pending() == 2


def test_requeue_goes_to_the_back_of_the_line(tmp_path):
    db, svc, img = make(tmp_path)
    ids = [svc.enqueue(str(img)) for _ in range(3)]
    db.cancel_jobs([ids[0]])
    assert db.requeue_jobs([ids[0]]) == 1
    assert [db.queue_position(i) for i in ids] == [3, 1, 2]


# ---- concurrency --------------------------------------------------------------------------------------------------
def test_concurrency_uses_separate_accounts_and_never_runs_a_job_twice(tmp_path):
    db = Database(tmp_path / "t.sqlite3")
    for i in range(3):
        db.add_account(f"a{i}@x.com", None, i + 1, str(tmp_path / f"p{i}"))
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    gate, inside, max_inside = threading.Barrier(2, timeout=10), [0], [0]
    seen_accounts, lock = [], threading.Lock()

    def slow(worker, account_id, image):
        with lock:
            seen_accounts.append(account_id)
            inside[0] += 1
            max_inside[0] = max(max_inside[0], inside[0])
        gate.wait()  # both jobs must be inside run_one at the same time
        time.sleep(0.05)
        with lock:
            inside[0] -= 1
        folder = tmp_path / "out" / f"{Path(image).stem}_{account_id}_{time.time_ns()}"
        return WorkerResult(WorkerState.COMPLETED, account_id, "ok", str(make_mesh_glb(folder / "m.glb")))

    made = []

    def factory():
        worker = FakeWorker(tmp_path / "out", {1: slow, 2: slow, 3: slow})
        made.append(worker)
        return worker

    svc = PipelineService(db, factory(), concurrency=2, worker_factory=factory, poll_seconds=0.05)
    ids = [svc.enqueue(str(img)) for _ in range(2)]
    svc.start_background()
    deadline = time.time() + 20
    while time.time() < deadline and any(db.get_job(i).status != "Completed" for i in ids):
        time.sleep(0.1)
    svc.stop()
    assert [db.get_job(i).status for i in ids] == ["Completed", "Completed"]
    assert max_inside[0] == 2 and len(set(seen_accounts)) == 2  # parallel, on two different accounts
    assert sum(len(w.calls) for w in made) == 2  # each job ran exactly once


def test_concurrency_is_clamped_without_a_worker_factory(tmp_path):
    db, svc, img = make(tmp_path)
    assert svc.set_concurrency(3) == 1
    svc2 = PipelineService(db, svc.worker, concurrency=3, worker_factory=lambda: svc.worker)
    assert svc2.concurrency == 3 and svc2.set_concurrency(99) == pipeline_module.MAX_CONCURRENCY


# ---- runner lock --------------------------------------------------------------------------------------------------
def test_runner_lock_acquired_once_per_process(tmp_path):
    lock = tmp_path / "r.lock"
    assert acquire_runner_lock(lock) is True
    assert runner_lock_held(lock) is False  # we own it
