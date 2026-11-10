from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.mail.purelymail import ImapMailbox, PurelymailApi, PurelymailError
from app.security.credentials import CredentialStore

PROVIDER = "purelymail"
TOKEN_KEY = ("_purelymail", "api_token")
EXPIRY_WARNING_DAYS = 7


class MailboxManager:
    """Existing mailboxes only: track them, check login, read mail. Passwords/tokens live in the CredentialStore."""

    def __init__(self, database: Any, credentials: CredentialStore,
                 api_factory: Callable[[str], PurelymailApi] = PurelymailApi,
                 imap_factory: Callable[..., ImapMailbox] = ImapMailbox):
        self.database, self.credentials = database, credentials
        self._api_factory, self._imap_factory = api_factory, imap_factory

    def set_api_token(self, token: str) -> None:
        self.credentials.set(*TOKEN_KEY, token)

    def api(self) -> PurelymailApi:
        return self._api_factory(self.credentials.get(*TOKEN_KEY) or "")

    def add_mailbox(self, address: str, password: str, *, expires_in_days: int | None = None) -> int:
        expires = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).strftime("%Y-%m-%d %H:%M:%S") \
            if expires_in_days else None
        mailbox_id = self.database.upsert_mailbox(address.lower(), PROVIDER, expires)
        self.credentials.set(address.lower(), "mail_password", password)
        return mailbox_id

    def sync_from_api(self) -> list[str]:
        """Register mailboxes the account owns that are not tracked yet (no password: read-only until set)."""
        known = {m["email"] for m in self.database.list_mailboxes()}
        added = []
        for address in self.api().list_users():
            if address.lower() not in known:
                self.database.upsert_mailbox(address.lower(), PROVIDER, None)
                added.append(address.lower())
        return added

    def check(self, address: str) -> str:
        """Login test over IMAP; stores the result. Returns the new status."""
        password = self.credentials.get(address.lower(), "mail_password")
        if not password:
            status = "No password"
        else:
            status = "Active" if self._imap_factory(address.lower(), password).check_login() else "Login failed"
        self.database.set_mailbox_status(address.lower(), status)
        return status

    def read(self, address: str, **filters: Any):
        password = self.credentials.get(address.lower(), "mail_password")
        if not password:
            raise PurelymailError("No stored password for this mailbox")
        return self._imap_factory(address.lower(), password).recent(**filters)

    def otp(self, address: str, **filters: Any) -> str | None:
        password = self.credentials.get(address.lower(), "mail_password")
        if not password:
            raise PurelymailError("No stored password for this mailbox")
        return self._imap_factory(address.lower(), password).latest_otp(**filters)

    def expiring(self, within_days: int = EXPIRY_WARNING_DAYS) -> list[dict]:
        limit = (datetime.now(timezone.utc) + timedelta(days=within_days)).strftime("%Y-%m-%d %H:%M:%S")
        return [m for m in self.database.list_mailboxes() if m["expires_at"] and m["expires_at"] <= limit]
