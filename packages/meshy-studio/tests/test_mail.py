import json
from datetime import datetime, timezone

import pytest

from app.core.database import Database
from app.mail.manager import MailboxManager
from app.mail.purelymail import ImapMailbox, PurelymailApi, PurelymailError, extract_otp
from app.security.credentials import MemoryCredentialStore

RAW = (b"From: Meshy <noreply@meshy.ai>\r\nSubject: 481675 is your Meshy verification code\r\n"
       b"Date: Mon, 10 Nov 2026 09:34:00 +0000\r\nContent-Type: text/plain\r\n\r\nYour code is 481675. Ignore 12345678.")


class FakeImap:
    log = []

    def __init__(self, host, port):
        self.host, self.port = host, port

    def login(self, user, password):
        FakeImap.log.append((user, password))
        if password != "good":
            raise OSError("auth failed")

    def select(self, box, readonly=False):
        assert readonly is True  # mail must never be modified

    def search(self, charset, *criteria):
        FakeImap.criteria = criteria
        return "OK", [b"1 2"]

    def fetch(self, uid, spec):
        return "OK", [(b"1 (RFC822)", RAW)]

    def logout(self):
        pass


def test_otp_extraction_ignores_longer_numbers():
    assert extract_otp("code 481675 now") == "481675"
    assert extract_otp("order 12345678") is None


def test_imap_reads_read_only_and_finds_otp():
    box = ImapMailbox("a@purelymail.com", "good", imap_factory=FakeImap)
    messages = box.recent(sender="meshy", subject="verification", limit=5)
    assert messages[0].subject.startswith("481675") and messages[0].sender.startswith("Meshy")
    assert "FROM" in FakeImap.criteria and "SUBJECT" in FakeImap.criteria
    assert box.recent(since=datetime(2026, 11, 11, tzinfo=timezone.utc)) == []
    assert ImapMailbox("a@purelymail.com", "good", imap_factory=FakeImap).check_login() is True
    assert ImapMailbox("a@purelymail.com", "bad", imap_factory=FakeImap).check_login() is False


def test_api_client_uses_header_and_never_leaks_token():
    seen = {}

    def transport(url, headers, body):
        seen.update(url=url, headers=headers, body=body)
        return json.dumps({"result": {"users": [{"userName": "a", "domainName": "purelymail.com"}]}}).encode()

    api = PurelymailApi("SECRET-TOKEN", transport=transport)
    assert api.list_users() == ["a@purelymail.com"]
    assert seen["headers"]["Purelymail-Api-Token"] == "SECRET-TOKEN" and seen["url"].endswith("/listUser")

    def broken(url, headers, body):
        raise OSError("boom SECRET-TOKEN")

    with pytest.raises(PurelymailError) as error:
        PurelymailApi("SECRET-TOKEN", transport=broken).list_users()
    assert "SECRET-TOKEN" not in str(error.value)
    with pytest.raises(PurelymailError):
        PurelymailApi("")


def test_api_error_payload_becomes_exception():
    api = PurelymailApi("t", transport=lambda *a: json.dumps({"error": {"message": "nope"}}).encode())
    with pytest.raises(PurelymailError):
        api.list_domains()


def test_manager_tracks_mailboxes_and_expiry(tmp_path):
    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, imap_factory=lambda a, p: ImapMailbox(a, p, imap_factory=FakeImap),
                             api_factory=lambda token: PurelymailApi(token, transport=lambda *a: json.dumps(
                                 {"result": {"users": ["new@purelymail.com", "a@purelymail.com"]}}).encode()))
    manager.add_mailbox("A@purelymail.com", "good", expires_in_days=3)
    manager.add_mailbox("b@purelymail.com", "bad", expires_in_days=90)
    assert manager.check("a@purelymail.com") == "Active" and manager.check("b@purelymail.com") == "Login failed"
    assert [m["email"] for m in manager.expiring(7)] == ["a@purelymail.com"]
    manager.set_api_token("tok")
    assert manager.sync_from_api() == ["new@purelymail.com"]
    assert manager.check("new@purelymail.com") == "No password"
    fixture_time = datetime(2026, 11, 10, 9, 36, tzinfo=timezone.utc)  # two minutes after the fixture mail
    assert manager.otp("a@purelymail.com", sender="meshy", now=fixture_time) == "481675"
    assert manager.otp("a@purelymail.com", sender="meshy", now=datetime(2026, 11, 10, 11, 0, tzinfo=timezone.utc)) is None  # too old
    with pytest.raises(PurelymailError):
        manager.otp("new@purelymail.com")  # no stored password
    assert all(row["status"] != "Unchecked" for row in db.list_mailboxes())
