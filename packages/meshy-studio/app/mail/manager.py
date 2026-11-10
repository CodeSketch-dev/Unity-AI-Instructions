from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.mail.purelymail import API_DISABLED_REASON, ImapMailbox, PurelymailApi, PurelymailError, api_config_valid
from app.mail.default_key import default_token
from app.security.credentials import CredentialStore

PROVIDER = "purelymail"
TOKEN_KEY = ("_purelymail", "api_token")
DEFAULT_PASSWORD_KEY = ("_purelymail", "default_mail_password")
EXPIRY_WARNING_DAYS = 7


class MailboxManager:
    """Existing mailboxes only: track them, check login, read mail. Passwords/tokens live in the CredentialStore."""

    def __init__(self, database: Any, credentials: CredentialStore,
                 api_config: Callable[[], dict | None] = lambda: None,
                 api_factory: Callable[[str, dict], PurelymailApi] = PurelymailApi,
                 imap_factory: Callable[..., ImapMailbox] = ImapMailbox):
        self.database, self.credentials = database, credentials
        self._api_config = api_config
        self._api_factory, self._imap_factory = api_factory, imap_factory

    def set_api_token(self, token: str) -> None:
        self.credentials.set(*TOKEN_KEY, token)

    def set_default_password(self, password: str) -> None:
        if not password:
            raise PurelymailError("Default mailbox password cannot be empty")
        self.credentials.set(*DEFAULT_PASSWORD_KEY, password)

    def api_enabled(self) -> bool:
        """The management API is only used with an endpoint configuration the user supplied; there are no defaults."""
        return api_config_valid(self._api_config())

    def create_enabled(self) -> bool:
        config = self._api_config() or {}
        return (self.api_enabled() and bool((config.get("endpoints") or {}).get("create_user"))
                and bool((config.get("payload_templates") or {}).get("create_user")))

    def api(self) -> PurelymailApi:
        if not self.api_enabled():
            raise PurelymailError(API_DISABLED_REASON)
        return self._api_factory(self.credentials.get(*TOKEN_KEY) or default_token(), self._api_config())

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

    def create_mailbox(self, address: str, password: str | None = None, *, expires_in_days: int | None = None) -> int:
        """Provision one mailbox idempotently, then store credentials only after server confirmation."""
        normalized = address.strip().lower()
        if normalized.count("@") != 1 or not all(normalized.split("@", 1)):
            raise PurelymailError("A valid mailbox address is required")
        password = password or self.credentials.get(*DEFAULT_PASSWORD_KEY)
        if not password:
            raise PurelymailError("No mailbox password supplied and no default password is stored")
        api = self.api()
        existing = {user.strip().lower() for user in api.list_users()}
        if normalized in existing:
            if not self._imap_factory(normalized, password).check_login():
                raise PurelymailError("Mailbox already exists but the supplied password was not verified")
        else:
            try:
                api.create_user(normalized, password)
            except PurelymailError as create_error:
                # A timeout can happen after the server commits. Reconcile before reporting failure or retrying.
                if normalized not in {user.strip().lower() for user in api.list_users()}:
                    raise create_error
            if normalized not in {user.strip().lower() for user in api.list_users()}:
                raise PurelymailError("create_user returned without the mailbox appearing in listUser")
        return self.add_mailbox(normalized, password, expires_in_days=expires_in_days)

    def change_password(self, address: str, password: str) -> None:
        normalized = address.strip().lower()
        self.api().modify_user_password(normalized, password)
        if not self._imap_factory(normalized, password).check_login():
            raise PurelymailError("Password update was not verified by IMAP")
        self.credentials.set(normalized, "mail_password", password)

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
