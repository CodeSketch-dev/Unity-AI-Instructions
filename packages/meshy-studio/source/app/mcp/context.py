from __future__ import annotations

import os
from pathlib import Path

from app.core.database import Database
from app.paths import app_root
from app.settings import Settings

ROOT = Path(__file__).resolve().parents[2]  # the `source` folder
DATA = Path(os.environ.get("MESHY_DATA_DIR") or app_root())
PACKAGE = ROOT.parent if ROOT.name == "source" else ROOT  # folder with publish.bat and MeshyAIStudio.exe
TERMINAL = ("Completed", "Failed", "Canceled")


def db() -> Database:
    return Database(DATA / "data" / "meshy.sqlite3")


def settings() -> Settings:
    return Settings(DATA)


def export_dir() -> Path:
    return settings().export_dir


def lock_path() -> Path:
    return DATA / "data" / "runner.lock"
