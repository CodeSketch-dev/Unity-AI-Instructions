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
OTP_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")


class PurelymailError(RuntimeError):
    pass


API_DISABLED_REASON = (
    "Purelymail API management is disabled: the official management API documentation is not available to this app, "
    "so no endpoint is guessed. Mailbox reading (IMAP) works. To enable API calls, copy the base URL, token header "
    "and endpoint paths from the documentation in your Purelymail account into data/settings.json (key purelymail_api).")


def api_config_valid(config: Any) -> bool:
    return (isinstance(config, dict) and bool(config.get("base_url")) and bool(config.get("token_header"))
            and isinstance(config.get("endpoints"), dict) and bool(config["endpoints"]))


class PurelymailApi:
    """Client for a Purelymail management API that the USER configured from the official documentation.

    Nothing is assumed: base URL, token header and endpoint paths all come from `config` and there are no defaults.
    The transport is injectable for tests."""

    def __init__(self, token: str, config: dict[str, Any],
                 transport: Callable[[str, dict[str, str], bytes], bytes] | None = None):
        if not token:
            raise PurelymailError("Purelymail API token is not configured")
        if not api_config_valid(config):
            raise PurelymailError(API_DISABLED_REASON)
        self._token = token
        self.base_url, self.header, self.endpoints = config["base_url"].rstrip("/"), config["token_header"], config["endpoints"]
        self._transport = transport or self._post

    @staticmethod
    def _post(url: str, headers: dict[str, str], body: bytes) -> bytes:
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()

    def call(self, name: str, payload: dict[str, Any] | None = None) -> Any:
        path = self.endpoints.get(name)
        if not path:
            raise PurelymailError(f"endpoint '{name}' is not configured")
        headers = {"Content-Type": "application/json", self.header: self._token}
        try:
            raw = self._transport(f"{self.base_url}/{path.lstrip('/')}", headers, json.dumps(payload or {}).encode("utf-8"))
        except Exception as error:  # never include the token in the message
            raise PurelymailError(f"{name} failed: {type(error).__name__}") from None
        data = json.loads(raw.decode("utf-8") or "{}")
        if isinstance(data, dict) and data.get("error"):
            raise PurelymailError(f"{name} returned an error: {data['error']}")
        return data.get("result", data) if isinstance(data, dict) else data

    def list_users(self) -> list[str]:
        result = self.call("list_users")
        users = result.get("users", []) if isinstance(result, dict) else result
        addresses = []
        for user in users or []:
            if isinstance(user, dict):
                address = user.get("address") or user.get("email") or (
                    f"{user['userName']}@{user['domainName']}" if "userName" in user and "domainName" in user else None)
            else:
                address = str(user)
            if address:
                addresses.append(address)
        return addresses


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
