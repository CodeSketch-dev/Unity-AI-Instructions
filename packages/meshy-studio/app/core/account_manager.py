from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.core.database import Database
from app.security.credentials import CredentialStore


EMAIL = re.compile(r"^[^\s@|]+@[^\s@|]+\.[^\s@|]+$")


@dataclass(frozen=True, slots=True)
class ParsedAccount:
    email: str
    password: str | None
    recovery_email: str | None = None
    totp_secret: str | None = None
    auth_mode: str = "google"


@dataclass(frozen=True, slots=True)
class ImportResult:
    imported: int
    duplicates: int
    invalid: int


def parse_account_line(line: str) -> ParsedAccount:
    parts = [part.strip() for part in line.strip().split("|")]
    if len(parts) == 1 and EMAIL.match(parts[0]):
        return ParsedAccount(parts[0].lower(), None, auth_mode="email_otp")
    if len(parts) not in (2, 4) or not EMAIL.match(parts[0]) or not parts[1]:
        raise ValueError("Expected email|password or email|password|recovery_email|totp_secret")
    recovery = parts[2] or None if len(parts) == 4 else None
    totp = parts[3].replace(" ", "") or None if len(parts) == 4 else None
    if recovery and not EMAIL.match(recovery):
        raise ValueError("Invalid recovery email")
    return ParsedAccount(parts[0].lower(), parts[1], recovery.lower() if recovery else None, totp)


class AccountManager:
    SECRET_KINDS = ("email", "password", "totp", "api_key")

    def __init__(self, database: Database, credentials: CredentialStore, profiles_root: str | Path):
        self.database = database
        self.credentials = credentials
        self.profiles_root = Path(profiles_root).resolve()
        self.profiles_root.mkdir(parents=True, exist_ok=True)

    def import_lines(self, lines: list[str]) -> ImportResult:
        imported = duplicates = invalid = 0
        seen: set[str] = set()
        for raw in lines:
            try:
                parsed = parse_account_line(raw)
            except ValueError:
                invalid += 1
                continue
            if parsed.email in seen or self.database.account_by_email(parsed.email):
                duplicates += 1
                continue
            seen.add(parsed.email)
            provisional = self.profiles_root / f"pending_{imported + 1:06d}"
            account_id = self.database.add_account(parsed.email, parsed.recovery_email, 100 + imported, str(provisional))
            final = self.profiles_root / f"account_{account_id:06d}"
            final.mkdir(parents=True, exist_ok=True)
            with self.database._lock, self.database._connection:
                self.database._connection.execute("UPDATE accounts SET profile_path=? WHERE id=?", (str(final), account_id))
            try:
                self.credentials.set(parsed.email, "email", parsed.email)
                self.credentials.set(parsed.email, "auth_mode", parsed.auth_mode)
                if parsed.password:
                    self.credentials.set(parsed.email, "password", parsed.password)
                if parsed.totp_secret:
                    self.credentials.set(parsed.email, "totp", parsed.totp_secret)
            except Exception:
                self.database.delete_account(account_id)
                shutil.rmtree(final, ignore_errors=True)
                raise
            imported += 1
        return ImportResult(imported, duplicates, invalid)

    def import_file(self, path: str | Path) -> ImportResult:
        return self.import_lines(Path(path).read_text(encoding="utf-8-sig").splitlines())

    def remove(self, account_id: int, delete_profile: bool = True) -> None:
        account = next(item for item in self.database.list_accounts() if item.id == account_id)
        for kind in self.SECRET_KINDS:
            self.credentials.delete(account.email, kind)
        self.database.delete_account(account_id)
        profile = Path(account.profile_path).resolve()
        if delete_profile and profile.parent == self.profiles_root:
            shutil.rmtree(profile, ignore_errors=True)

