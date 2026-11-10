from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

from app.mail.purelymail import PurelymailError

LOG = logging.getLogger("meshy.provisioner")

DEFAULT_RULE = {"prefix": "codesketch", "domain": "purelymail.com", "digits": 6, "max_per_hour": 3}


@dataclass(frozen=True, slots=True)
class MailboxRule:
    """Naming rule for auto-created mailboxes: <prefix><zero-padded counter>@<domain>. The shared password is NOT here
    (it lives in the Windows credential store, see MailboxManager.set_default_password)."""
    prefix: str = "codesketch"
    domain: str = "purelymail.com"
    digits: int = 6
    max_per_hour: int = 3

    @staticmethod
    def from_settings(value: Any) -> "MailboxRule":
        data = {**DEFAULT_RULE, **(value if isinstance(value, dict) else {})}
        return MailboxRule(str(data["prefix"]), str(data["domain"]), int(data["digits"]), int(data["max_per_hour"]))

    def _pattern(self) -> re.Pattern[str]:
        return re.compile(rf"^{re.escape(self.prefix)}(\d{{{self.digits}}})@{re.escape(self.domain)}$", re.I)

    def counter_of(self, address: str) -> int | None:
        match = self._pattern().match(address.strip())
        return int(match.group(1)) if match else None

    def address_for(self, number: int) -> str:
        return f"{self.prefix}{number:0{self.digits}d}@{self.domain}"

    def next_address(self, existing: list[str]) -> str:
        used = [n for n in (self.counter_of(a) for a in existing) if n is not None]
        return self.address_for(max(used, default=0) + 1)


class AccountProvisioner:
    """Keeps a free Meshy account available: adopts mailboxes that follow the rule, and creates the next one
    (codesketch000003@... style) only when no usable account is left. Hourly cap so a failure loop cannot spend money."""

    def __init__(self, database: Any, mail: Any, accounts: Any, rule: Callable[[], MailboxRule],
                 enabled: Callable[[], bool], clock: Callable[[], float] = time.time):
        self.database, self.mail, self.accounts = database, mail, accounts
        self._rule, self._enabled, self._clock = rule, enabled, clock
        self._created_at: list[float] = []

    def _known_addresses(self) -> list[str]:
        known = {m["email"] for m in self.database.list_mailboxes()} | {a.email for a in self.database.list_accounts()}
        try:
            known |= {u.lower() for u in self.mail.api().list_users()}
        except PurelymailError:
            pass
        return sorted(known)

    def adopt_existing(self) -> list[str]:
        """Mailboxes of the account that match the rule become Meshy accounts (shared password, email-OTP sign-in)."""
        rule, adopted = self._rule(), []
        for address in self._known_addresses():
            if rule.counter_of(address) is None or self.database.account_by_email(address):
                continue
            password = self.mail.credentials.get(address, "mail_password") or self.mail.shared_password()
            if not password:
                continue
            if not self.database.account_by_email(address):
                self.mail.add_mailbox(address, password)
                self.accounts.import_lines([address])
                adopted.append(address)
        return adopted

    def provision_one(self) -> str | None:
        """Create the next rule-named mailbox and register it as an account. None when capped, disabled or unconfigured."""
        if not self._enabled() or not self.mail.create_enabled():
            return None
        now = self._clock()
        self._created_at = [t for t in self._created_at if now - t < 3600]
        rule = self._rule()
        if len(self._created_at) >= rule.max_per_hour:
            LOG.warning("mailbox auto-create paused: %d created in the last hour", len(self._created_at))
            return None
        address = rule.next_address(self._known_addresses())
        self._created_at.append(now)  # count the attempt: a failing API must not be hammered
        self.mail.create_mailbox(address)  # raises PurelymailError (no password / API error): the caller logs it
        self.accounts.import_lines([address])
        LOG.info("created mailbox %s and registered it as a Meshy account", address)
        return address

    def ensure_account(self) -> int:
        """Called when no account can take the next job. Returns how many accounts became available."""
        if not self._enabled():
            return 0
        try:
            adopted = self.adopt_existing()
            if adopted:
                return len(adopted)
            return 1 if self.provision_one() else 0
        except Exception:
            LOG.exception("could not provision a mailbox/account")
            return 0
