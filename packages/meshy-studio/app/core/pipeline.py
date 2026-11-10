from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from app.automation.meshy_export import MeshyExportError, inspect_glb
from app.automation.meshy_worker import WorkerResult, WorkerState
from app.core.models import JobStatus
from app.core.scheduler import Scheduler, SchedulePolicy

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_RETRIES = 2
QUOTA_COOLDOWN_HOURS = 24
LOGIN_RETRY_HOURS = 1
BACKOFF_BASE_SECONDS = 30
BACKOFF_MAX_SECONDS = 600
MAX_CONCURRENCY = 3
_UNUSABLE = {"quota limited", "needs verification", "login failed", "busy"}
_lock_handle: Any = None
LOG = logging.getLogger("meshy.pipeline")


def validate_image(path: str | Path) -> Path:
    """Raises ValueError with a message suitable for the user."""
    path = Path(path)
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"{path.name}: must be PNG, JPG, JPEG or WebP")
    if not path.is_file():
        raise ValueError(f"{path.name}: file does not exist")
    size = path.stat().st_size
    if size == 0:
        raise ValueError(f"{path.name}: file is empty")
    if size > MAX_IMAGE_BYTES:
        raise ValueError(f"{path.name}: {size / 1048576:.1f} MB exceeds the 20 MB limit")
    return path


def acquire_runner_lock(path: str | Path) -> bool:
    """OS-level exclusive lock; released automatically if the process dies."""
    global _lock_handle
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    _lock_handle = handle
    return True


def runner_lock_held(path: str | Path) -> bool:
    """True when ANOTHER process owns the lock (probe, then release)."""
    global _lock_handle
    if _lock_handle is not None:
        return False
    if acquire_runner_lock(path):
        _lock_handle.close()
        _lock_handle = None
        return False
    return True


def _utc_now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


class PipelineService:
    """Claims Pending jobs and drives Meshy workers.

    One job = one reserved account (an account never runs two jobs at once). A job that was already submitted to Meshy is
    never submitted again automatically (that would spend credits twice). Each worker/thread owns its own browser contexts.
    """

    def __init__(self, database: Any, worker: Any, scheduler: Scheduler | None = None, *, poll_seconds: float = 3.0,
                 concurrency: int = 1, worker_factory: Callable[[], Any] | None = None,
                 max_retries: int = MAX_RETRIES, job_timeout_seconds: float | None = None):
        self.database = database
        self.scheduler = scheduler or Scheduler()
        self.poll_seconds = poll_seconds
        self.max_retries = max_retries
        self.job_timeout_seconds = job_timeout_seconds
        self._worker_factory = worker_factory
        self._workers: list[Any] = [worker]
        self.concurrency = 1
        self.set_concurrency(concurrency)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._recovered = False
        self._state_lock = threading.RLock()
        self._busy_accounts: set[int] = set()
        self._current: dict[int, int] = {}  # slot -> job id
        self.manual_account_id: int | None = None
        self.halted = False

    # ---- configuration ----------------------------------------------------------------------------------------------
    @property
    def worker(self) -> Any:
        return self._workers[0]

    @worker.setter
    def worker(self, value: Any) -> None:
        self._workers[0] = value

    def set_concurrency(self, value: int) -> int:
        """Clamped to 1..MAX_CONCURRENCY; more than 1 needs a worker factory (one browser driver per thread)."""
        value = max(1, min(MAX_CONCURRENCY, int(value)))
        if value > 1 and self._worker_factory is None:
            LOG.warning("concurrency %d requested but no worker factory: using 1", value)
            value = 1
        self.concurrency = value
        return value

    def _worker_for(self, slot: int) -> Any:
        with self._state_lock:
            while len(self._workers) <= slot:
                self._workers.append(self._worker_factory())
            return self._workers[slot]

    # ---- queue ------------------------------------------------------------------------------------------------------
    def enqueue(self, image_path: str, note: str = "") -> int:
        path = validate_image(image_path)
        job_id = self.database.create_job(str(path.resolve()), note)
        LOG.info("job %s queued: %s", job_id, path.name)
        return job_id

    def cancel_jobs(self, job_ids: list[int]) -> dict[str, list[int]]:
        """Queued jobs are canceled at once (the rest move up); a running job stops at its next step.
        This only cancels LOCAL work: a Meshy task that was already submitted keeps running on their servers."""
        outcome = self.database.cancel_jobs(job_ids)
        if outcome["stopping"]:
            for slot, running in list(self._current.items()):
                if running in outcome["stopping"]:
                    getattr(self._workers[slot], "request_cancel", lambda: None)()
        LOG.info("cancel: %s", outcome)
        return outcome

    def pause_jobs(self, job_ids: list[int]) -> int:
        return self.database.pause_jobs(job_ids)

    def resume_jobs(self, job_ids: list[int]) -> int:
        return self.database.resume_jobs(job_ids)

    def use_account(self, account_id: int | None) -> None:
        """Pin all jobs to one account the user chose (overrides rest/quota status); None = automatic rotation."""
        self.manual_account_id = account_id
        if account_id is not None:
            self.database.mark_account(account_id, "Ready")
            self.database.resume_paused_jobs()
        LOG.info("account selection: %s", "auto" if account_id is None else f"manual #{account_id}")

    def emergency_stop(self) -> None:
        """Stop sending new jobs, cancel every running local job at its next step, pause the queue, close browsers.
        Meshy tasks that were already submitted are NOT canceled on the server (there is no safe way to do that here)."""
        self.halted = True
        self._stop.set()
        running = list(self._current.values())
        if running:
            self.database.cancel_jobs(running)
        for worker in list(self._workers):
            getattr(worker, "request_cancel", lambda: None)()
        paused = self.database.pause_pending_jobs()
        LOG.warning("EMERGENCY STOP: %d running job(s) told to stop, %d queued job(s) paused", len(running), paused)

    def release_all_browsers(self) -> None:
        for worker in list(self._workers):
            getattr(worker, "release_all", lambda: None)()

    def resume_queue(self) -> None:
        self.halted = False
        self.database.resume_paused_jobs()
        self.start_background()
        LOG.info("queue resumed")

    # ---- accounts ---------------------------------------------------------------------------------------------------
    def _usable_accounts(self) -> list[Any]:
        accounts = self.database.list_accounts()
        if self.manual_account_id is not None:
            return [a for a in accounts if a.id == self.manual_account_id and a.authorized]
        return [a for a in accounts if a.authorized and a.status.lower() not in _UNUSABLE]

    def _reserve_account(self) -> Any | None:
        with self._state_lock:
            free = [a for a in self._usable_accounts() if a.id not in self._busy_accounts]
            if not free:
                return None
            if self.manual_account_id is not None:
                chosen = free[0]
            else:
                chosen = self.scheduler.select(free, SchedulePolicy.ROUND_ROBIN, allow_unvalidated=True).account
            self._busy_accounts.add(chosen.id)
            return chosen

    def _release_account(self, account_id: int) -> None:
        with self._state_lock:
            self._busy_accounts.discard(account_id)

    # ---- running ----------------------------------------------------------------------------------------------------
    def run_pending(self) -> int:
        """Process the queue on the calling thread (slot 0) until nothing is claimable."""
        if not self._recovered:
            self.database.recover_jobs()
            self._recovered = True
        return self._drain(0)

    def _drain(self, slot: int) -> int:
        processed = 0
        while not self._stop.is_set():
            if self.database.release_expired_cooldowns() and not self.halted:
                self.database.resume_paused_jobs()  # a resting account is back: waiting jobs continue by themselves
            account = self._reserve_account()
            if account is None:
                break
            job = self.database.claim_next_job()
            if job is None:
                self._release_account(account.id)
                break
            try:
                self._attempt(slot, job, account)
            finally:
                self._release_account(account.id)
            processed += 1
        return processed

    def _attempt(self, slot: int, job: Any, account: Any) -> None:
        db, worker = self.database, self._worker_for(slot)
        self._current[slot] = job.id
        started = _utc_now() if job.started_at is None else job.started_at
        db.update_job(job.id, status=JobStatus.GENERATING.value, account_id=account.id, error=None, started_at=started)
        if hasattr(worker, "cancel_event"):
            worker.cancel_event.clear()
        worker.cancel_probe = lambda: db.get_job(job.id).status == JobStatus.CANCEL_REQUESTED.value
        worker.deadline = (time.monotonic() + self.job_timeout_seconds) if self.job_timeout_seconds else None
        worker.on_credits = lambda account_id, balance: db.set_credit(account_id, balance)
        worker.on_submitted = lambda account_id: db.update_job(job.id, submitted=1)
        worker.on_progress = lambda percent: db.update_job(job.id, progress=int(percent))
        LOG.info("job %s started on account #%s (%s)", job.id, account.id, Path(job.image_path).name)
        try:
            result = worker.run_one(account.id, job.image_path, account_key=account.email)
        except Exception as error:  # a crash inside the worker must not kill the queue
            LOG.exception("job %s crashed", job.id)
            result = WorkerResult(WorkerState.FAILED, account.id, f"{type(error).__name__}")
        finally:
            self._current.pop(slot, None)
        self._finish(slot, job, account, result)

    def _finish(self, slot: int, job: Any, account: Any, result: Any) -> None:
        db = self.database
        submitted = bool(db.get_job(job.id).submitted)
        state = result.state
        if state == WorkerState.COMPLETED:
            self._complete(slot, job, account, result)
            return
        if state == WorkerState.CANCELED:
            db.update_job(job.id, status=JobStatus.CANCELED.value, error="Canceled by user", finished_at=_utc_now())
            LOG.info("job %s canceled (local only%s)", job.id, "; the Meshy task keeps running" if submitted else "")
            self._release_when_idle(slot, account.id)
            return
        if state in (WorkerState.QUOTA_LIMITED, WorkerState.INVALID_CREDENTIALS, WorkerState.MANUAL_VERIFICATION,
                     WorkerState.WAITING_FOR_LOGIN):
            self._mark_account(account, result)
            getattr(self._worker_for(slot), "release_account", lambda _id: None)(account.id)
            if submitted:
                self._fail_submitted(job, f"Stopped after submission: {result.message}")
            elif self.manual_account_id is not None:
                db.update_job(job.id, status=JobStatus.PAUSED.value, error=f"Paused: selected account unusable ({result.message}). Pick another account.")
            else:
                db.update_job(job.id, status=JobStatus.PENDING.value, error=None)  # another account takes it next
            return
        # FAILED (or an unexpected state)
        getattr(self._worker_for(slot), "release_account", lambda _id: None)(account.id)  # a stuck page is useless
        if submitted:
            self._fail_submitted(job, result.message)
        else:
            self._fail_or_retry(job, result.message or "Failed")

    def _complete(self, slot: int, job: Any, account: Any, result: Any) -> None:
        """Completed only when the output file exists and is a valid GLB."""
        db = self.database
        try:
            path = Path(result.result_path or "")
            if not path.is_file() or path.stat().st_size == 0:
                raise MeshyExportError("output file is missing or empty")
            info = inspect_glb(path)
            if info["triangles"] <= 0:
                raise MeshyExportError("output model has no triangles")
        except Exception as error:
            self._fail_submitted(job, f"Output verification failed: {error}")
            return
        folder = path.parent
        formats = ",".join(sorted({f.suffix.lstrip(".").upper() for f in folder.iterdir() if f.suffix.lower() in (".glb", ".fbx")}))
        textures = sorted((folder / "textures").glob("*basecolor.png")) if (folder / "textures").is_dir() else []
        db.update_job(job.id, status=JobStatus.COMPLETED.value, progress=100, error=None, result_path=str(path), finished_at=_utc_now())
        db.add_model(job.id, path.stem, job.image_path, account.id, str(path), str(folder), formats, info["triangles"],
                     path.stat().st_size, str(textures[0]) if textures else None)
        db.mark_account(account.id, "Ready", session_valid=True)
        LOG.info("job %s completed: %s (%d triangles, %s)", job.id, path.name, info["triangles"], formats)
        self._release_when_idle(slot, account.id)

    def _mark_account(self, account: Any, result: Any) -> None:
        db, state = self.database, result.state
        if state == WorkerState.QUOTA_LIMITED:
            db.mark_account(account.id, "Quota Limited", cooldown_hours=QUOTA_COOLDOWN_HOURS)
            LOG.warning("account #%s has no credits: %s", account.id, result.message)
        elif state == WorkerState.INVALID_CREDENTIALS:
            db.mark_account(account.id, "Invalid credentials", authorized=False, session_valid=False)
        elif state == WorkerState.MANUAL_VERIFICATION:
            db.mark_account(account.id, "Needs verification", session_valid=False)
        elif state == WorkerState.WAITING_FOR_LOGIN:
            db.mark_account(account.id, "Login failed", cooldown_hours=LOGIN_RETRY_HOURS, session_valid=False)

    def _release_when_idle(self, slot: int, account_id: int) -> None:
        """Close the browser window once the queue is empty so no windows are left behind."""
        release = getattr(self._worker_for(slot), "release_account", None)
        if release is not None and not any(j.status == JobStatus.PENDING.value for j in self.database.list_jobs()):
            try:
                release(account_id)
            except Exception:
                LOG.exception("could not close the browser of account #%s", account_id)

    def _fail_submitted(self, job: Any, message: str) -> None:
        """After submission there may be a paid remote task: never retry automatically."""
        note = (message + " | not retried automatically (a second paid generation could result). "
                          "Check the Meshy workspace, then use Retry if you accept that cost.")[:500]
        self.database.update_job(job.id, status=JobStatus.FAILED.value, error=note, finished_at=_utc_now())
        LOG.error("job %s failed after submission: %s", job.id, message[:200])

    def _fail_or_retry(self, job: Any, message: str) -> None:
        current = self.database.get_job(job.id)
        if current.retries < self.max_retries:
            delay = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * 2 ** current.retries)  # exponential backoff
            LOG.warning("job %s failed before submission (%s); retry %d in %ds", job.id, message[:120], current.retries + 1, delay)
            self.database.update_job(job.id, status=JobStatus.PENDING.value, retries=current.retries + 1, error=message,
                                     retry_at=time.time() + delay)
        else:
            self.database.update_job(job.id, status=JobStatus.FAILED.value, error=message, finished_at=_utc_now())
            LOG.error("job %s failed for good: %s", job.id, message[:200])

    # ---- background threads -----------------------------------------------------------------------------------------
    def start_background(self) -> None:
        self._threads = [t for t in self._threads if t.is_alive()]
        self._stop.clear()
        if not self._recovered:
            self.database.recover_jobs()
            self._recovered = True
        for slot in range(len(self._threads), self.concurrency):
            thread = threading.Thread(target=self._loop, args=(slot,), name=f"meshy-pipeline-{slot}", daemon=True)
            self._threads.append(thread)
            thread.start()

    def _loop(self, slot: int) -> None:
        while not self._stop.is_set():
            try:
                self._drain(slot)
            except Exception:
                LOG.exception("pipeline loop error")
            self._stop.wait(self.poll_seconds)

    def stop(self) -> None:
        self._stop.set()
