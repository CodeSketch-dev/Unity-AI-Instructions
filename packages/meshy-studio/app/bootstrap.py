from __future__ import annotations

import io
import os
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from app.core.account_manager import AccountManager, ImportResult

DECODER_ZIP = "https://github.com/ChesterTheCatt/meshy-ai-to-stl/archive/refs/heads/main.zip"
DECODER_FILES = (
    "https://www.meshy.ai/pt-BR/resource/decrypt/mesh_loader.js",
    "https://www.meshy.ai/pt-BR/resource/decrypt/mesh_loader.wasm",
)
ACCOUNTS_FILE = "accounts.txt"
Log = Callable[[str], None]


def decoder_dir(root: Path) -> Path:
    return root / "docs" / "vendor" / "meshy-ai-to-stl" / "chrome-extension"


def decoder_ready(root: Path) -> bool:
    vendor = decoder_dir(root) / "vendor"
    return all((vendor / name).is_file() and (vendor / name).stat().st_size > 0 for name in ("mesh_loader.js", "mesh_loader.wasm")) \
        and (decoder_dir(root) / "sandbox.html").is_file()


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "MeshyAIStudio"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def ensure_decoder(root: Path, log: Log = print, fetch: Callable[[str], bytes] = _fetch) -> bool:
    """Download the meshy-ai-to-stl shell and Meshy's decoder files when they are missing."""
    if decoder_ready(root):
        return True
    log("Downloading the model decoder (first start only)...")
    try:
        target = root / "docs" / "vendor" / "meshy-ai-to-stl"
        with zipfile.ZipFile(io.BytesIO(fetch(DECODER_ZIP))) as archive:
            for member in archive.infolist():
                relative = member.filename.split("/", 1)[1] if "/" in member.filename else ""
                if not relative or member.is_dir() or relative.startswith(".git"):
                    continue
                destination = target / relative
                if target.resolve() not in destination.resolve().parents:
                    continue  # never write outside the vendor folder
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))
        vendor = decoder_dir(root) / "vendor"
        vendor.mkdir(parents=True, exist_ok=True)
        for url in DECODER_FILES:
            data = fetch(url)
            if not data:
                raise OSError(f"empty download: {url}")
            (vendor / url.rsplit("/", 1)[1]).write_bytes(data)
    except Exception as error:
        log(f"Decoder download failed: {type(error).__name__}: {error}")
        return False
    log("Decoder ready.")
    return decoder_ready(root)


def chrome_path() -> Path | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    return next((path for path in candidates if path.is_file()), None)


def ensure_browser(log: Log = print) -> bool:
    """Use installed Chrome; otherwise download Playwright's Chromium once (~150 MB)."""
    if chrome_path() is not None:
        return True
    log("Google Chrome not found: downloading a browser (first start only, ~150 MB)...")
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env
        node, cli = compute_driver_executable()
        result = subprocess.run([str(node), str(cli), "install", "chromium"], env=get_driver_env(),
                                capture_output=True, text=True, timeout=1800,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            log(f"Browser download failed: {result.stderr[-300:]}")
            return False
    except Exception as error:
        log(f"Browser download failed: {type(error).__name__}: {error}")
        return False
    log("Browser ready.")
    return True


def import_bundled_accounts(root: Path, manager: AccountManager, log: Log = print) -> ImportResult | None:
    """First start of a shared build: import accounts.txt next to the exe, then rename it so it runs once."""
    path = root / ACCOUNTS_FILE
    if not path.is_file() or manager.database.list_accounts():
        return None
    result = manager.import_file(path)
    path.rename(root / "accounts.imported.txt")
    log(f"Imported {result.imported} accounts from {ACCOUNTS_FILE} (duplicates {result.duplicates}, invalid {result.invalid}).")
    return result


def prepare(root: Path, log: Log = print) -> bool:
    """Everything the worker needs that is not inside the exe."""
    return ensure_decoder(root, log) and ensure_browser(log)
