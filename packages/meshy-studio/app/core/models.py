from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "Pending"
    CHECKING_ACCOUNT = "Checking Account"
    WAITING_FOR_LOGIN = "Waiting for Login"
    UPLOADING = "Uploading"
    GENERATING = "Generating"
    DOWNLOADING = "Downloading"
    COMPLETED = "Completed"
    FAILED = "Failed"
    PAUSED = "Paused"
    CANCELED = "Canceled"
    QUOTA_LIMITED = "Quota Limited"
    CANCEL_REQUESTED = "Cancel Requested"


@dataclass(slots=True)
class Account:
    id: int
    email: str
    recovery_email: str | None
    priority: int
    profile_path: str
    status: str
    session_valid: bool
    authorized: bool
    active_jobs: int = 0
    cooldown_until: str | None = None
    credit_balance: int | None = None
    credit_checked_at: str | None = None


@dataclass(slots=True)
class Job:
    id: int
    image_path: str
    note: str
    status: str
    account_id: int | None
    meshy_task_id: str | None
    progress: int
    retries: int
    error: str | None
    result_path: str | None
    meshy_url: str | None
    created_at: str
    updated_at: str
    submitted: int = 0
    started_at: str | None = None
    finished_at: str | None = None

