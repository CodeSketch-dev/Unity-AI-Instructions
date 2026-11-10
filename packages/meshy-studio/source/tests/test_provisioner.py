from pathlib import Path

from app.core.account_manager import AccountManager
from app.core.database import Database
from app.mail.manager import DEFAULT_PASSWORD_KEY, MailboxManager
from app.mail.provisioner import AccountProvisioner, MailboxRule


class MemStore:
    def __init__(self): self.d = {}
    def set(self, k, kind, v): self.d[(k, kind)] = v
    def get(self, k, kind): return self.d.get((k, kind))
    def delete(self, k, kind): self.d.pop((k, kind), None)


class FakeApi:
    def __init__(self, users): self.users = list(users); self.created = []
    def list_users(self): return list(self.users)
    def create_user(self, address, password): self.users.append(address); self.created.append((address, password))


class Imap:
    def __init__(self, a, p): pass
    def check_login(self): return True


def build(tmp_path, users, enabled=True, clock=lambda: 0.0, password="shared-pw"):
    db = Database(tmp_path / "t.db")
    store = MemStore()
    if password:
        store.set(*DEFAULT_PASSWORD_KEY, password)
    api = FakeApi(users)
    mail = MailboxManager(db, store, api_config=lambda: {"base_url": "x", "token_header": "h", "endpoints": {"create_user": "/c", "list_users": "/l"},
                                                         "payload_templates": {"create_user": {"u": "{local}"}}},
                          api_factory=lambda t, c: api, imap_factory=Imap)
    accounts = AccountManager(db, store, tmp_path / "profiles")
    prov = AccountProvisioner(db, mail, accounts, lambda: MailboxRule(), lambda: enabled, clock)
    return db, store, api, prov


def test_rule_next_address_ignores_other_shapes():
    rule = MailboxRule()
    assert rule.next_address(["codesketch000001@purelymail.com", "codesketch000002@purelymail.com", "codesketch2506@purelymail.com"]) == "codesketch000003@purelymail.com"
    assert rule.next_address([]) == "codesketch000001@purelymail.com"


def test_adopts_existing_then_creates_next(tmp_path: Path):
    db, store, api, prov = build(tmp_path, ["codesketch000001@purelymail.com", "codesketch000002@purelymail.com", "codesketch2506@purelymail.com"])
    assert prov.ensure_account() == 2  # the two rule-named mailboxes become accounts; the odd one is left alone
    assert {a.email for a in db.list_accounts()} == {"codesketch000001@purelymail.com", "codesketch000002@purelymail.com"}
    assert store.get("codesketch000001@purelymail.com", "auth_mode") == "email_otp"
    assert prov.ensure_account() == 1  # all adopted: now create 000003
    assert api.created == [("codesketch000003@purelymail.com", "shared-pw")]
    assert db.account_by_email("codesketch000003@purelymail.com") is not None


def test_disabled_missing_password_and_hourly_cap(tmp_path: Path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir(); (tmp_path / "c").mkdir()
    _, _, api, prov = build(tmp_path / "a", [], enabled=False)
    assert prov.ensure_account() == 0 and api.created == []
    _, _, api, prov = build(tmp_path / "b", [], password=None)
    assert prov.ensure_account() == 1  # no stored password: the built-in default is used, so a fresh clone just works
    from app.mail.default_key import default_mail_password
    assert api.created == [("codesketch000001@purelymail.com", default_mail_password())]
    _, _, api, prov = build(tmp_path / "c", [])
    results = [prov.ensure_account() for _ in range(5)]
    assert results == [1, 1, 1, 0, 0] and len(api.created) == 3  # max 3 per hour


def test_pipeline_asks_provisioner_only_when_no_usable_account(tmp_path: Path):
    from app.core.pipeline import PipelineService
    db = Database(tmp_path / "p.db")
    img = tmp_path / "a.png"; img.write_bytes(b"x")
    service = PipelineService(db, object())
    calls = []
    service.provisioner = type("P", (), {"ensure_account": lambda self: calls.append(1) or 0})()
    assert service._provision_account() is False and calls == []  # nothing pending
    service.enqueue(str(img))
    assert service._provision_account() is False and calls == [1]  # pending + no accounts -> asked once
    assert service._provision_account() is False and calls == [1]  # throttled
