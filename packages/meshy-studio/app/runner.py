"""Headless runner: `python -m app.runner` processes the job queue with no UI."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from app.automation.browser_manager import BrowserManager
from app.automation.google_login import GoogleOAuthLogin
from app.automation.meshy_worker import MeshyWebWorker
from app.paths import app_root
from app.settings import Settings
from app import bootstrap
from app.core.account_manager import AccountManager
from app.core.database import Database
from app.core.pipeline import PipelineService, acquire_runner_lock
from app.security.credentials import KeyringCredentialStore


def data_root() -> Path:
    return Path(os.environ.get("MESHY_DATA_DIR") or app_root())


def build_service(root: Path) -> PipelineService:
    browser = BrowserManager(root / "profiles")
    database = Database(root / "data" / "meshy.sqlite3")
    worker = MeshyWebWorker(browser, google_login=GoogleOAuthLogin(KeyringCredentialStore()), export_dir=lambda: Settings(root).export_dir)
    return PipelineService(database, worker)


def main() -> int:
    root = data_root()
    if not acquire_runner_lock(root / "data" / "runner.lock"):
        print("Another Meshy runner is already active", file=sys.stderr)
        return 1
    bootstrap.prepare(root)
    service = build_service(root)
    try:
        bootstrap.import_bundled_accounts(root, AccountManager(service.database, KeyringCredentialStore(), root / "profiles"))
    except Exception as error:
        print(f"accounts.txt import failed: {type(error).__name__}", file=sys.stderr)
    service.start_background()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
