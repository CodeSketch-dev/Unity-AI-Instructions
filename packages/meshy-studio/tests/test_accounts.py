from pathlib import Path

from app.core.account_manager import AccountManager, parse_account_line
from app.core.database import Database
from app.security.credentials import MemoryCredentialStore


def test_parse_account_line_accepts_supported_formats():
    basic = parse_account_line("first@example.com|pw")
    full = parse_account_line("second@example.com|pw2|recover@example.com|JBSWY3DPEHPK3PXP")
    assert basic.email == "first@example.com"
    assert basic.recovery_email is None
    assert full.recovery_email == "recover@example.com"
    assert full.totp_secret == "JBSWY3DPEHPK3PXP"


def test_parse_account_line_rejects_invalid_data():
    for line in ("", "not-an-email|pw", "a@example.com", "a@example.com|"):
        try:
            parse_account_line(line)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted invalid line: {line!r}")


def test_import_ten_accounts_deduplicates_and_keeps_secrets_out_of_sqlite(tmp_path: Path):
    db_path = tmp_path / "studio.db"
    db = Database(db_path)
    store = MemoryCredentialStore()
    manager = AccountManager(db, store, tmp_path / "profiles")
    lines = [f"user{i}@example.com|secret-{i}" for i in range(10)]
    result = manager.import_lines(lines + [lines[0], "broken"])

    assert result.imported == 10
    assert result.duplicates == 1
    assert result.invalid == 1
    assert len(db.list_accounts()) == 10
    raw = db_path.read_bytes()
    assert b"secret-" not in raw
    assert len({a.profile_path for a in db.list_accounts()}) == 10
    assert all(Path(a.profile_path).is_dir() for a in db.list_accounts())

