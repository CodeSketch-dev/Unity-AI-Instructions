import json
from datetime import datetime, timezone

import pytest

from app.core.database import Database
from app.mail.manager import MailboxManager
from app.mail.purelymail import API_DISABLED_REASON, OFFICIAL_API_CONFIG, ImapMailbox, PurelymailApi, PurelymailError, extract_otp

CONFIG = {"base_url": "https://api.example.test/v1", "token_header": "X-Test-Token", "endpoints": {"list_users": "users/list"}}
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

    api = PurelymailApi("SECRET-TOKEN", CONFIG, transport=transport)
    assert api.list_users() == ["a@purelymail.com"]
    assert seen["headers"]["X-Test-Token"] == "SECRET-TOKEN" and seen["url"] == "https://api.example.test/v1/users/list"

    def broken(url, headers, body):
        raise OSError("boom SECRET-TOKEN")

    with pytest.raises(PurelymailError) as error:
        PurelymailApi("SECRET-TOKEN", CONFIG, transport=broken).list_users()
    assert "SECRET-TOKEN" not in str(error.value)
    with pytest.raises(PurelymailError):
        PurelymailApi("", CONFIG)


def test_api_creates_only_a_configured_purelymail_user_and_tracks_it(tmp_path):
    requests = []
    config = {
        **CONFIG,
        "endpoints": {**CONFIG["endpoints"], "create_user": "users/create"},
        "payload_templates": {"create_user": {"userName": "{local}", "domainName": "{domain}", "password": "{password}"}},
    }

    created = False

    def transport(url, headers, body):
        nonlocal created
        requests.append((url, json.loads(body)))
        if url.endswith("users/list"):
            users = ["artist@owned.example"] if created else []
            return json.dumps({"result": {"users": users}}).encode()
        created = True
        return b'{"result":{"created":true}}'

    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: config,
                             api_factory=lambda token, cfg: PurelymailApi(token, cfg, transport=transport))
    manager.set_api_token("owner-token")
    manager.create_mailbox("artist@owned.example", "safe-password", expires_in_days=30)
    assert requests == [
        ("https://api.example.test/v1/users/list", {}),
        ("https://api.example.test/v1/users/create",
         {"userName": "artist", "domainName": "owned.example", "password": "safe-password"}),
        ("https://api.example.test/v1/users/list", {}),
    ]
    assert db.list_mailboxes()[0]["email"] == "artist@owned.example"
    assert store.get("artist@owned.example", "mail_password") == "safe-password"


def test_official_api_contract_matches_purelymail_openapi():
    assert OFFICIAL_API_CONFIG == {
        "base_url": "https://purelymail.com",
        "token_header": "Purelymail-Api-Token",
        "endpoints": {"list_users": "/api/v0/listUser", "create_user": "/api/v0/createUser",
                      "modify_user": "/api/v0/modifyUser"},
        "payload_templates": {"create_user": {
            "userName": "{local}", "domainName": "{domain}", "password": "{password}",
            "enableSearchIndexing": True,
        }},
    }


def test_create_mailbox_is_idempotent_when_user_already_exists(tmp_path):
    calls = []

    class Api:
        def list_users(self):
            calls.append("list")
            return ["Artist@owned.example"]

        def create_user(self, address, password):
            calls.append("create")

    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: OFFICIAL_API_CONFIG,
                             api_factory=lambda token, config: Api(),
                             imap_factory=lambda address, password: ImapMailbox(address, password, imap_factory=FakeImap))
    manager.set_api_token("owner-token")
    manager.create_mailbox("artist@owned.example", "good")
    assert calls == ["list"]
    assert db.list_mailboxes()[0]["email"] == "artist@owned.example"


def test_default_password_and_modify_password_stay_in_credential_store(tmp_path):
    changed = []

    class Api:
        def list_users(self):
            return []

        def create_user(self, address, password):
            changed.append(("create", address, password))

        def modify_user_password(self, address, password):
            changed.append(("modify", address, password))

    class Login:
        def __init__(self, address, password):
            self.password = password

        def check_login(self):
            return self.password == "good"

    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: OFFICIAL_API_CONFIG,
                             api_factory=lambda token, config: Api(), imap_factory=Login)
    manager.set_api_token("owner-token")
    manager.set_default_password("good")
    manager.change_password("artist@owned.example", "good")
    assert changed == [("modify", "artist@owned.example", "good")]
    assert store.get("_purelymail", "default_mail_password") == "good"
    assert store.get("artist@owned.example", "mail_password") == "good"


def test_create_mailbox_reconciles_timeout_after_server_commit(tmp_path):
    calls = 0

    class Api:
        def list_users(self):
            return ["artist@owned.example"] if calls else []

        def create_user(self, address, password):
            nonlocal calls
            calls += 1
            raise PurelymailError("create_user failed")

    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: OFFICIAL_API_CONFIG,
                             api_factory=lambda token, config: Api())
    manager.set_api_token("owner-token")
    manager.create_mailbox("artist@owned.example", "safe-password")
    assert calls == 1
    assert store.get("artist@owned.example", "mail_password") == "safe-password"


def test_create_mailbox_does_not_store_password_when_server_never_confirms(tmp_path):
    class Api:
        def list_users(self):
            return []

        def create_user(self, address, password):
            return {}

    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: OFFICIAL_API_CONFIG,
                             api_factory=lambda token, config: Api())
    manager.set_api_token("owner-token")
    with pytest.raises(PurelymailError, match="without the mailbox appearing"):
        manager.create_mailbox("artist@owned.example", "safe-password")
    assert db.list_mailboxes() == []
    assert store.get("artist@owned.example", "mail_password") is None


def test_api_never_guesses_create_user_payload_schema():
    config = {**CONFIG, "endpoints": {**CONFIG["endpoints"], "create_user": "users/create"}}
    with pytest.raises(PurelymailError, match="payload template"):
        PurelymailApi("token", config, transport=lambda *args: b"{}").create_user("a@owned.example", "password")


def test_api_error_payload_becomes_exception():
    api = PurelymailApi("t", {**CONFIG, "endpoints": {"list_users": "u", "list_domains": "d"}},
                        transport=lambda *a: json.dumps({"error": {"message": "nope"}}).encode())
    with pytest.raises(PurelymailError, match="nope"):
        api.call("list_domains")
    with pytest.raises(PurelymailError, match="not configured"):
        PurelymailApi("t", CONFIG).call("check_credit")


def test_no_endpoint_is_ever_guessed(tmp_path):
    called = []
    db = Database(tmp_path / "t.sqlite3")
    manager = MailboxManager(db, MemoryCredentialStore(), api_factory=lambda *a: called.append(a))  # default: no configuration
    manager.set_api_token("tok")
    assert manager.api_enabled() is False
    with pytest.raises(PurelymailError, match="configuration is invalid"):
        manager.sync_from_api()
    with pytest.raises(PurelymailError, match="no endpoint is guessed"):
        PurelymailApi("tok", {})
    assert called == [] and "no endpoint is guessed" in API_DISABLED_REASON


def test_manager_tracks_mailboxes_and_expiry(tmp_path):
    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = MailboxManager(db, store, api_config=lambda: CONFIG,
                             imap_factory=lambda a, p: ImapMailbox(a, p, imap_factory=FakeImap),
                             api_factory=lambda token, config: PurelymailApi(token, config, transport=lambda *a: json.dumps(
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
