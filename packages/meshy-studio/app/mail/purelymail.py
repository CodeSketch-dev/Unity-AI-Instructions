from __future__ import annotations

import email as email_lib
import imaplib
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from typing import Any, Callable

# IMAP settings are from Purelymail's "Technical Setup" page (verified).
IMAP_HOST = "imap.purelymail.com"
IMAP_PORT = 993
# The management API is NOT documented on the public site, so these defaults are an UNVERIFIED assumption.
# Override them in Settings once you have the official documentation from your Purelymail account.
DEFAULT_API_BASE = "https://purelymail.com/api/v0"
DEFAULT_TOKEN_HEADER = "Purelymail-Api-Token"
OTP_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")


class PurelymailError(RuntimeError):
    pass


class PurelymailApi:
    """Thin client for the Purelymail management API (JSON over POST). The transport is injectable for tests."""

    def __init__(self, token: str, base_url: str = DEFAULT_API_BASE, header: str = DEFAULT_TOKEN_HEADER,
                 transport: Callable[[str, dict[str, str], bytes], bytes] | None = None):
        if not token:
            raise PurelymailError("Purelymail API token is not configured")
        self._token, self.base_url, self.header = token, base_url.rstrip("/"), header
        self._transport = transport or self._post

    @staticmethod
    def _post(url: str, headers: dict[str, str], body: bytes) -> bytes:
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()

    def call(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", self.header: self._token}
        try:
            raw = self._transport(f"{self.base_url}/{endpoint}", headers, json.dumps(payload or {}).encode("utf-8"))
        except Exception as error:  # never include the token in the message
            raise PurelymailError(f"{endpoint} failed: {type(error).__name__}") from None
        data = json.loads(raw.decode("utf-8") or "{}")
        if isinstance(data, dict) and data.get("error"):
            raise PurelymailError(f"{endpoint} returned an error: {data['error']}")
        return data.get("result", data) if isinstance(data, dict) else {"result": data}

    def list_users(self) -> list[str]:
        result = self.call("listUser")
        users = result.get("users", []) if isinstance(result, dict) else []
        return [user["userName"] + "@" + user["domainName"] if isinstance(user, dict) and "domainName" in user
                else str(user) for user in users]

    def list_domains(self) -> list[str]:
        result = self.call("listDomains")
        domains = result.get("domains", []) if isinstance(result, dict) else []
        return [domain["name"] if isinstance(domain, dict) else str(domain) for domain in domains]

    def check_credit(self) -> float | None:
        result = self.call("checkAccountCredit")
        value = result.get("credit") if isinstance(result, dict) else None
        return float(value) if value is not None else None


@dataclass(frozen=True, slots=True)
class MailMessage:
    uid: str
    sender: str
    subject: str
    received: datetime | None
    body: str


def extract_otp(text: str) -> str | None:
    match = OTP_PATTERN.search(text)
    return match.group(1) if match else None


def _decode(value: str | None) -> str:
    return str(make_header(decode_header(value))) if value else ""


def _body_text(message: email_lib.message.Message) -> str:
    parts = message.walk() if message.is_multipart() else [message]
    chunks = []
    for part in parts:
        if part.get_content_type() in ("text/plain", "text/html") and not part.get_filename():
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            chunks.append(re.sub(r"<[^>]+>", " ", text) if part.get_content_type() == "text/html" else text)
    return "\n".join(chunks)


class ImapMailbox:
    """Read-only IMAP access to one mailbox. Credentials stay in memory; nothing is logged."""

    def __init__(self, address: str, password: str, host: str = IMAP_HOST, port: int = IMAP_PORT,
                 imap_factory: Callable[[str, int], Any] | None = None):
        self.address, self._password, self.host, self.port = address, password, host, port
        self._factory = imap_factory or (lambda h, p: imaplib.IMAP4_SSL(h, p))

    def check_login(self) -> bool:
        try:
            connection = self._factory(self.host, self.port)
            connection.login(self.address, self._password)
            connection.logout()
            return True
        except Exception:
            return False

    def recent(self, *, sender: str | None = None, subject: str | None = None, since: datetime | None = None,
               limit: int = 20) -> list[MailMessage]:
        connection = self._factory(self.host, self.port)
        try:
            connection.login(self.address, self._password)
            connection.select("INBOX", readonly=True)
            criteria = ["ALL"]
            if sender:
                criteria += ["FROM", f'"{sender}"']
            if subject:
                criteria += ["SUBJECT", f'"{subject}"']
            if since:
                criteria += ["SINCE", since.strftime("%d-%b-%Y")]
            _, data = connection.search(None, *criteria)
            uids = (data[0] or b"").split()[-limit:]
            messages = []
            for uid in reversed(uids):
                _, fetched = connection.fetch(uid, "(RFC822)")
                parsed = email_lib.message_from_bytes(fetched[0][1])
                try:
                    received = parsedate_to_datetime(parsed["Date"]) if parsed["Date"] else None
                except (TypeError, ValueError):
                    received = None
                if since and received and received.astimezone(timezone.utc) < since.astimezone(timezone.utc):
                    continue  # IMAP SINCE only has day resolution
                messages.append(MailMessage(uid.decode(), _decode(parsed["From"]), _decode(parsed["Subject"]),
                                            received, _body_text(parsed)))
            return messages
        finally:
            try:
                connection.logout()
            except Exception:
                pass

    def latest_otp(self, *, sender: str | None = None, subject: str | None = None, within_minutes: int = 15,
                   now: datetime | None = None) -> str | None:
        since = (now or datetime.now(timezone.utc)) - timedelta(minutes=within_minutes)
        for message in self.recent(sender=sender, subject=subject, since=since):
            code = extract_otp(message.subject) or extract_otp(message.body)
            if code:
                return code
        return None
