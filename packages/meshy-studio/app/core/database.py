from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from app.core.models import Account, Job, JobStatus


def _add_columns(connection: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    for name, kind in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")


def _m1_account_columns(connection: sqlite3.Connection) -> None:
    _add_columns(connection, "accounts", {"cooldown_until": "TEXT", "credit_balance": "INTEGER", "credit_checked_at": "TEXT"})


def _m2_job_columns(connection: sqlite3.Connection) -> None:
    _add_columns(connection, "jobs", {"retry_at": "REAL", "queue_seq": "INTEGER"})


def _m3_idempotency_and_timing(connection: sqlite3.Connection) -> None:
    # submitted=1 once Generate was clicked and a new remote task appeared: such a job is never re-submitted automatically
    _add_columns(connection, "jobs", {"submitted": "INTEGER NOT NULL DEFAULT 0", "started_at": "TEXT", "finished_at": "TEXT"})


def _m4_library_metadata(connection: sqlite3.Connection) -> None:
    _add_columns(connection, "models", {"folder": "TEXT", "formats": "TEXT", "triangles": "INTEGER", "size_bytes": "INTEGER"})


MIGRATIONS = [_m1_account_columns, _m2_job_columns, _m3_idempotency_and_timing, _m4_library_metadata]


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self._connection:
            self._connection.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    recovery_email TEXT,
                    priority INTEGER NOT NULL DEFAULT 100,
                    profile_path TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'Not connected',
                    session_valid INTEGER NOT NULL DEFAULT 0,
                    authorized INTEGER NOT NULL DEFAULT 1,
                    active_jobs INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                    meshy_task_id TEXT,
                    progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
                    retries INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    result_path TEXT,
                    meshy_url TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    source_image TEXT NOT NULL,
                    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
                    status TEXT NOT NULL,
                    file_path TEXT,
                    meshy_task_id TEXT,
                    meshy_url TEXT,
                    thumbnail_path TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS mailboxes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    provider TEXT NOT NULL DEFAULT 'purelymail',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    status TEXT NOT NULL DEFAULT 'Unchecked',
                    last_checked_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            """)
        self._migrate()

    def schema_version(self) -> int:
        return int(self._connection.execute("PRAGMA user_version").fetchone()[0])

    def _migrate(self) -> None:
        """Ordered, idempotent migrations tracked by PRAGMA user_version (safe on databases from older builds)."""
        for target, step in enumerate(MIGRATIONS, start=1):
            if self.schema_version() < target:
                with self._lock, self._connection:
                    step(self._connection)
                    self._connection.execute(f"PRAGMA user_version={target}")

    def add_account(self, email: str, recovery_email: str | None, priority: int, profile_path: str) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO accounts(email,recovery_email,priority,profile_path) VALUES(?,?,?,?)",
                (email, recovery_email, priority, profile_path),
            )
            return int(cursor.lastrowid)

    def account_by_email(self, email: str) -> Account | None:
        with self._lock:
            row = self._connection.execute("SELECT * FROM accounts WHERE email=? COLLATE NOCASE", (email,)).fetchone()
        return self._account(row) if row else None

    def list_accounts(self) -> list[Account]:
        with self._lock:
            rows = self._connection.execute("SELECT * FROM accounts ORDER BY priority,id").fetchall()
        return [self._account(row) for row in rows]

    def update_account(self, account_id: int, **fields: object) -> None:
        allowed = {"email", "recovery_email", "priority", "status", "session_valid", "authorized", "active_jobs", "cooldown_until",
                   "credit_balance", "credit_checked_at"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return
        sql = ",".join(f"{key}=?" for key in updates)
        with self._lock, self._connection:
            self._connection.execute(f"UPDATE accounts SET {sql} WHERE id=?", (*updates.values(), account_id))

    def mark_account(self, account_id: int, status: str, *, cooldown_hours: float = 0,
                     authorized: bool | None = None, session_valid: bool | None = None) -> None:
        fields: dict[str, object] = {"status": status}
        fields["cooldown_until"] = None
        if authorized is not None:
            fields["authorized"] = int(authorized)
        if session_valid is not None:
            fields["session_valid"] = int(session_valid)
        with self._lock, self._connection:
            if cooldown_hours > 0:
                self._connection.execute("UPDATE accounts SET cooldown_until=datetime('now', ?) WHERE id=?",
                                         (f"+{int(cooldown_hours * 3600)} seconds", account_id))
                fields.pop("cooldown_until")
            sql = ",".join(f"{key}=?" for key in fields)
            self._connection.execute(f"UPDATE accounts SET {sql} WHERE id=?", (*fields.values(), account_id))

    def set_credit(self, account_id: int, balance: int) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE accounts SET credit_balance=?, credit_checked_at=CURRENT_TIMESTAMP WHERE id=?", (balance, account_id))

    def pause_jobs(self, job_ids: list[int]) -> int:
        count = 0
        with self._lock, self._connection:
            for job_id in job_ids:
                count += self._connection.execute(
                    "UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status=?",
                    (JobStatus.PAUSED.value, job_id, JobStatus.PENDING.value)).rowcount
        return count

    def resume_jobs(self, job_ids: list[int]) -> int:
        count = 0
        with self._lock, self._connection:
            for job_id in job_ids:
                count += self._connection.execute(
                    "UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status=?",
                    (JobStatus.PENDING.value, job_id, JobStatus.PAUSED.value)).rowcount
        return count

    def pause_pending_jobs(self) -> int:
        with self._lock, self._connection:
            return self._connection.execute("UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE status=?",
                                            (JobStatus.PAUSED.value, JobStatus.PENDING.value)).rowcount

    def resume_paused_jobs(self) -> int:
        with self._lock, self._connection:
            return self._connection.execute("UPDATE jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE status=?",
                                            (JobStatus.PENDING.value, JobStatus.PAUSED.value)).rowcount

    def release_expired_cooldowns(self) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "UPDATE accounts SET status='Ready', cooldown_until=NULL "
                "WHERE cooldown_until IS NOT NULL AND cooldown_until <= datetime('now')")
            return cursor.rowcount

    def claim_next_job(self) -> Job | None:
        with self._lock, self._connection:
            row = self._connection.execute(
                "SELECT * FROM jobs WHERE status=? AND (retry_at IS NULL OR retry_at<=?) ORDER BY COALESCE(queue_seq, id), id LIMIT 1",
                (JobStatus.PENDING.value, time.time())).fetchone()
            if not row:
                return None
            self._connection.execute("UPDATE jobs SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                                     (JobStatus.CHECKING_ACCOUNT.value, row["id"]))
        return self.get_job(row["id"])

    def delete_account(self, account_id: int) -> None:
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM accounts WHERE id=?", (account_id,))

    def create_job(self, image_path: str, note: str = "", account_id: int | None = None) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO jobs(image_path,note,status,account_id) VALUES(?,?,?,?)",
                (image_path, note, JobStatus.PENDING.value, account_id),
            )
            return int(cursor.lastrowid)

    def get_job(self, job_id: int) -> Job:
        with self._lock:
            row = self._connection.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise KeyError(job_id)
        return self._job(row)

    def list_jobs(self) -> list[Job]:
        with self._lock:
            return [self._job(row) for row in self._connection.execute("SELECT * FROM jobs ORDER BY id DESC")]

    def update_job(self, job_id: int, **fields: object) -> None:
        allowed = {"status", "account_id", "meshy_task_id", "progress", "retries", "error", "result_path", "meshy_url", "retry_at", "submitted", "started_at", "finished_at"}
        updates = {key: value for key, value in fields.items() if key in allowed}
        if not updates:
            return
        updates["updated_at"] = "CURRENT_TIMESTAMP"
        assignments = [f"{key}=?" for key in updates if key != "updated_at"] + ["updated_at=CURRENT_TIMESTAMP"]
        values = [value for key, value in updates.items() if key != "updated_at"]
        with self._lock, self._connection:
            self._connection.execute(f"UPDATE jobs SET {','.join(assignments)} WHERE id=?", (*values, job_id))

    def cancel_queued_jobs(self, job_ids: list[int]) -> list[int]:
        """Cancel jobs that have not started (Pending/Paused). Returns the ids that were cancelled."""
        cancelled: list[int] = []
        with self._lock, self._connection:
            for job_id in job_ids:
                cursor = self._connection.execute(
                    "UPDATE jobs SET status=?,error=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN (?,?)",
                    (JobStatus.CANCELED.value, "Canceled by user", job_id, JobStatus.PENDING.value, JobStatus.PAUSED.value))
                if cursor.rowcount:
                    cancelled.append(job_id)
        return cancelled

    def cancel_jobs(self, job_ids: list[int]) -> dict[str, list[int]]:
        """Queued jobs become Canceled now; a running job is flagged so its worker stops at the next step."""
        canceled = self.cancel_queued_jobs(job_ids)
        running = (JobStatus.CHECKING_ACCOUNT.value, JobStatus.UPLOADING.value, JobStatus.GENERATING.value, JobStatus.DOWNLOADING.value)
        flagged: list[int] = []
        with self._lock, self._connection:
            for job_id in job_ids:
                if job_id in canceled:
                    continue
                cursor = self._connection.execute(
                    f"UPDATE jobs SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ({','.join('?' * len(running))})",
                    (JobStatus.CANCEL_REQUESTED.value, job_id, *running))
                if cursor.rowcount:
                    flagged.append(job_id)
        return {"canceled": canceled, "stopping": flagged}

    def requeue_jobs(self, job_ids: list[int]) -> int:
        """Put unsubmitted Failed/Canceled jobs back at the end of the queue.

        A submitted job may still exist remotely and must be reconciled first; silently resetting its submitted flag can
        spend credits twice.
        """
        count = 0
        with self._lock, self._connection:
            for job_id in job_ids:
                cursor = self._connection.execute(
                    "UPDATE jobs SET status=?,error=NULL,retries=0,submitted=0,progress=0,started_at=NULL,finished_at=NULL,updated_at=CURRENT_TIMESTAMP,"
                    "queue_seq=(SELECT COALESCE(MAX(COALESCE(queue_seq,id)),0)+1 FROM jobs) "
                    "WHERE id=? AND submitted=0 AND status IN (?,?)",
                    (JobStatus.PENDING.value, job_id, JobStatus.FAILED.value, JobStatus.CANCELED.value))
                count += cursor.rowcount
        return count

    def queue_position(self, job_id: int) -> int | None:
        """1-based place among Pending jobs (1 = next to run); None if not pending."""
        with self._lock:
            row = self._connection.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row or row["status"] != JobStatus.PENDING.value:
                return None
            key = self._connection.execute("SELECT COALESCE(queue_seq,id) AS k FROM jobs WHERE id=?", (job_id,)).fetchone()["k"]
            return int(self._connection.execute(
                "SELECT COUNT(*) FROM jobs WHERE status=? AND (COALESCE(queue_seq,id)<? OR (COALESCE(queue_seq,id)=? AND id<=?))",
                (JobStatus.PENDING.value, key, key, job_id)).fetchone()[0])

    def upsert_mailbox(self, email: str, provider: str, expires_at: str | None) -> int:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO mailboxes(email,provider,expires_at) VALUES(?,?,?) "
                "ON CONFLICT(email) DO UPDATE SET provider=excluded.provider, "
                "expires_at=COALESCE(excluded.expires_at, mailboxes.expires_at)", (email, provider, expires_at))
            return int(self._connection.execute("SELECT id FROM mailboxes WHERE email=?", (email,)).fetchone()["id"])

    def list_mailboxes(self) -> list[dict]:
        with self._lock:
            return [dict(row) for row in self._connection.execute("SELECT * FROM mailboxes ORDER BY email")]

    def set_mailbox_status(self, email: str, status: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE mailboxes SET status=?, last_checked_at=CURRENT_TIMESTAMP WHERE email=?", (status, email))

    def recover_jobs(self) -> int:
        """After a crash/close: unsubmitted work is queued again; a job that was already submitted to Meshy is NOT
        re-submitted (that would spend credits twice) - it is marked Failed so the user can check the workspace."""
        active = (
            JobStatus.CHECKING_ACCOUNT.value, JobStatus.UPLOADING.value, JobStatus.GENERATING.value,
            JobStatus.DOWNLOADING.value, JobStatus.WAITING_FOR_LOGIN.value, JobStatus.CANCEL_REQUESTED.value,
        )
        placeholders = ",".join("?" for _ in active)
        with self._lock, self._connection:
            self._connection.execute(
                f"UPDATE jobs SET status=?,error=?,finished_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP "
                f"WHERE status IN ({placeholders}) AND submitted=1 AND status<>?",
                (JobStatus.FAILED.value, "Interrupted after it was submitted to Meshy; not re-submitted automatically "
                 "(check the Meshy workspace, then Retry if you accept spending credits again)", *active, JobStatus.CANCEL_REQUESTED.value))
            self._connection.execute(
                "UPDATE jobs SET status=?,error='Canceled by user',updated_at=CURRENT_TIMESTAMP WHERE status=?",
                (JobStatus.CANCELED.value, JobStatus.CANCEL_REQUESTED.value))
            cursor = self._connection.execute(
                f"UPDATE jobs SET status=?,updated_at=CURRENT_TIMESTAMP WHERE status IN ({placeholders})",
                (JobStatus.PENDING.value, *active))
            return cursor.rowcount

    # ---- library (exported models) ------------------------------------------------------------------------------
    def add_model(self, job_id: int, name: str, source_image: str, account_id: int | None, file_path: str, folder: str,
                  formats: str, triangles: int | None, size_bytes: int | None, thumbnail_path: str | None) -> int:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "INSERT INTO models(job_id,name,source_image,account_id,status,file_path,folder,formats,triangles,size_bytes,thumbnail_path) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET file_path=excluded.file_path, folder=excluded.folder, "
                "formats=excluded.formats, triangles=excluded.triangles, size_bytes=excluded.size_bytes, thumbnail_path=excluded.thumbnail_path",
                (job_id, name, source_image, account_id, "Exported", file_path, folder, formats, triangles, size_bytes, thumbnail_path))
            return int(cursor.lastrowid)

    def list_models(self) -> list[dict]:
        with self._lock:
            return [dict(row) for row in self._connection.execute("SELECT * FROM models ORDER BY id DESC")]

    def delete_model_record(self, model_id: int) -> None:
        """Removes the Library record only; files on disk are never touched."""
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM models WHERE id=?", (model_id,))

    def close(self) -> None:
        self._connection.close()

    @staticmethod
    def _account(row: sqlite3.Row) -> Account:
        return Account(row["id"], row["email"], row["recovery_email"], row["priority"], row["profile_path"],
                       row["status"], bool(row["session_valid"]), bool(row["authorized"]), row["active_jobs"], row["cooldown_until"],
                       row["credit_balance"], row["credit_checked_at"])

    @staticmethod
    def _job(row: sqlite3.Row) -> Job:
        return Job(*(row[key] for key in ("id", "image_path", "note", "status", "account_id", "meshy_task_id",
                                           "progress", "retries", "error", "result_path", "meshy_url",
                                           "created_at", "updated_at", "submitted", "started_at", "finished_at")))

