import io
import zipfile
from pathlib import Path

from app import bootstrap
from app.core.account_manager import AccountManager
from app.core.database import Database
from app.security.credentials import MemoryCredentialStore


def fake_fetch(url: str) -> bytes:
    if url == bootstrap.DECODER_ZIP:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("meshy-ai-to-stl-main/chrome-extension/sandbox.html", "<html/>")
            archive.writestr("meshy-ai-to-stl-main/chrome-extension/manifest.json", "{}")
            archive.writestr("meshy-ai-to-stl-main/.gitignore", "x")
            archive.writestr("meshy-ai-to-stl-main/../../evil.txt", "x")
        return buffer.getvalue()
    return b"decoder-bytes"


def test_decoder_downloads_once_and_stays_inside_vendor(tmp_path: Path):
    assert not bootstrap.decoder_ready(tmp_path)
    assert bootstrap.ensure_decoder(tmp_path, log=lambda m: None, fetch=fake_fetch) is True
    assert bootstrap.decoder_ready(tmp_path)
    assert not (tmp_path / "docs" / "vendor" / "meshy-ai-to-stl" / ".gitignore").exists()
    assert not list(tmp_path.parent.glob("evil.txt"))
    calls = []
    assert bootstrap.ensure_decoder(tmp_path, log=lambda m: None, fetch=lambda u: calls.append(u) or b"") is True
    assert calls == []  # already present: nothing is downloaded again


def test_decoder_failure_is_reported_not_raised(tmp_path: Path):
    def boom(url):
        raise OSError("offline")
    messages = []
    assert bootstrap.ensure_decoder(tmp_path, log=messages.append, fetch=boom) is False
    assert any("offline" in m for m in messages)


def test_bundled_accounts_import_runs_once(tmp_path: Path):
    db = Database(tmp_path / "t.sqlite3")
    store = MemoryCredentialStore()
    manager = AccountManager(db, store, tmp_path / "profiles")
    (tmp_path / "accounts.txt").write_text("a@x.com|pw1\nb@x.com|pw2|rec@x.com|GEZDGNBVGY3TQOJQ\n")
    result = bootstrap.import_bundled_accounts(tmp_path, manager, log=lambda m: None)
    assert result.imported == 2
    assert store.get("b@x.com", "totp") == "GEZDGNBVGY3TQOJQ"
    assert not (tmp_path / "accounts.txt").exists() and (tmp_path / "accounts.imported.txt").exists()
    assert bootstrap.import_bundled_accounts(tmp_path, manager, log=lambda m: None) is None
