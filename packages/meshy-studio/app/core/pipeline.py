from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

from app.automation.meshy_worker import WorkerState
from app.core.models import JobStatus
from app.core.scheduler import Scheduler

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_RETRIES = 2
QUOTA_COOLDOWN_HOURS = 24
LOGIN_RETRY_HOURS = 1
_UNUSABLE = {"quota limited", "needs verification", "login failed", "busy"}
_lock_handle: Any = None
LOG = logging.getLogger('meshy.pipeline')
BACKOFF_BASE_SECONDS = 30
BACKOFF_MAX_SECONDS = 600


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


class PipelineService:
    """Claims Pending jobs and drives the worker. All worker calls stay on one thread."""

    def __init__(self, database: Any, worker: Any, scheduler: Scheduler | None = None, *, poll_seconds: float = 3.0):
        self.database = database
        self.worker = worker
        self.scheduler = scheduler or Scheduler()
        self.poll_seconds = poll_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._recovered = False
        self._current_job_id: int | None = None
        self.manual_account_id: int | None = None
        self.halted = False

    def enqueue(self, image_path: str, note: str = "") -> int:
        path = Path(image_path)
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("Image must be PNG, JPG, JPEG or WebP")
        if not path.is_file():
            raise ValueError("Image file does not exist")
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image exceeds the 20 MB limit")
        return self.database.create_job(str(path.resolve()), note)

    def use_account(self, account_id: int | None) -> None:
        """Pin all jobs to one account the user chose (overrides rest/quota status); None = automatic rotation."""
        self.manual_account_id = account_id
        if account_id is not None:
            self.database.mark_account(account_id, "Ready")
            self.database.resume_paused_jobs()
        LOG.info("account selection: %s", "auto" if account_id is None else f"manual #{account_id}")

    def emergency_stop(self) -> None:
        """Stop everything now: running job stops at its next step, queue is paused, browsers are closed."""
        self.halted = True
        self._stop.set()
        if self._current_job_id is not None:
            self.database.cancel_jobs([self._current_job_id])
            getattr(self.worker, "request_cancel", lambda: None)()
        paused = self.database.pause_pending_jobs()
        LOG.warning("EMERGENCY STOP: queue paused (%d jobs)", paused)

    def resume_queue(self) -> None:
        self.halted = False
        self.database.resume_paused_jobs()
        self.start_background()
        LOG.info("queue resumed")

    def _usable_accounts(self) -> list[Any]:
        if self.manual_account_id is not None:
            return [a for a in self.database.list_accounts() if a.id == self.manual_account_id and a.authorized]
        return [a for a in self.database.list_accounts() if a.authorized and a.status.lower() not in _UNUSABLE]

    def run_pending(self) -> int:
        if not self._recovered:
            self.database.recover_jobs()
            self._recovered = True
        processed = 0
        while not self._stop.is_set():
            if self.database.release_expired_cooldowns() and not self.halted:
                self.database.resume_paused_jobs()  # a resting account is back: waiting jobs continue by themselves
            if not self._usable_accounts():
                break
            job = self.database.claim_next_job()
            if job is None:
                break
            self._run_job(job)
            processed += 1
        return processed

    def cancel_jobs(self, job_ids: list[int]) -> dict[str, list[int]]:
        """Cancel queued jobs at once (the rest move up); ask the running one to stop at its next step."""
        outcome = self.database.cancel_jobs(job_ids)
        if outcome["stopping"]:
            getattr(self.worker, "request_cancel", lambda: None)()
        return outcome

    def _run_job(self, job: Any) -> None:
        db = self.database
        self._current_job_id = job.id
        getattr(getattr(self.worker, "cancel_event", None), "clear", lambda: None)()
        # another process (MCP) may flag the running job in the database
        self.worker.cancel_probe = lambda: self.database.get_job(job.id).status == JobStatus.CANCEL_REQUESTED.value
        try:
            self._run_job_inner(job)
        finally:
            self._current_job_id = None

    def _run_job_inner(self, job: Any) -> None:
        db = self.database
        db.update_job(job.id, status=JobStatus.GENERATING.value, error=None)

        def on_result(account: Any, result: Any) -> None:
            state = result.state
            if state == WorkerState.QUOTA_LIMITED:
                db.mark_account(account.id, "Quota Limited", cooldown_hours=QUOTA_COOLDOWN_HOURS)
                LOG.warning("account #%s has no credits: %s", account.id, result.message)
            elif state == WorkerState.INVALID_CREDENTIALS:
                db.mark_account(account.id, "Invalid credentials", authorized=False, session_valid=False)
            elif state == WorkerState.MANUAL_VERIFICATION:
                db.mark_account(account.id, "Needs verification", session_valid=False)
            elif state == WorkerState.WAITING_FOR_LOGIN:
                db.mark_account(account.id, "Login failed", cooldown_hours=LOGIN_RETRY_HOURS, session_valid=False)
            elif state in (WorkerState.GENERATING, WorkerState.COMPLETED):
                db.mark_account(account.id, "Ready", session_valid=True)
                if getattr(result, "result_path", None):
                    db.update_job(job.id, result_path=result.result_path)
            db.update_job(job.id, account_id=account.id)
            if state == WorkerState.FAILED:
                # A stuck page is useless on retry and would stay open as a stray window.
                getattr(self.worker, "release_account", lambda _id: None)(account.id)

        self.worker.on_credits = lambda account_id, balance: db.set_credit(account_id, balance)
        LOG.info("job %s started: %s", job.id, job.image_path)
        try:
            result = self.worker.run_with_rotation(
                self._usable_accounts(), job.image_path, self.scheduler,
                account_key_for=lambda account: account.email, on_result=on_result)
        except Exception as error:
            self._fail_or_retry(job, type(error).__name__)
            return
        if result.state == WorkerState.CANCELED:
            db.update_job(job.id, status=JobStatus.CANCELED.value, error="Canceled by user")
            self._release_when_idle(result.account_id)
        elif result.state in (WorkerState.GENERATING, WorkerState.COMPLETED):
            db.update_job(job.id, status=JobStatus.COMPLETED.value, progress=100, error=None)
            self._release_when_idle(result.account_id)
        elif result.state == WorkerState.FAILED:
            self._fail_or_retry(job, result.message)
        else:
            # Every usable account was exhausted: pause until a cooldown ends or the user picks another account.
            db.update_job(job.id, status=JobStatus.PAUSED.value,
                          error="Paused: no account with enough credits. Pick another account or wait.")
            LOG.warning("job %s paused: no account with enough credits", job.id)

    def _release_when_idle(self, account_id: int) -> None:
        """Close the browser window once the queue is empty so no windows are left behind."""
        release = getattr(self.worker, "release_account", None)
        if release is not None and not any(j.status == JobStatus.PENDING.value for j in self.database.list_jobs()):
            try:
                release(account_id)
            except Exception:
                pass

    def _fail_or_retry(self, job: Any, message: str) -> None:
        current = self.database.get_job(job.id)
        if current.retries < MAX_RETRIES:
            delay = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * 2 ** current.retries)  # exponential backoff
            LOG.warning("job %s failed (%s); retry %d in %ds", job.id, message[:120], current.retries + 1, delay)
            self.database.update_job(job.id, status=JobStatus.PENDING.value, retries=current.retries + 1, error=message,
                                     retry_at=time.time() + delay)
        else:
            self.database.update_job(job.id, status=JobStatus.FAILED.value, error=message)

    def start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="meshy-pipeline", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_pending()
            except Exception:
                pass
            self._stop.wait(self.poll_seconds)

    def stop(self) -> None:
        self._stop.set()
