from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Folder holding data/, profiles/, Export/ and docs/vendor.

    From source it is the repo root. In the frozen exe (dist/MeshyAIStudio/) walk up to the
    first folder that has docs/vendor, so the exe shares data with the source tree.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        for folder in (exe_dir, *exe_dir.parents):
            if (folder / "docs" / "vendor").exists():
                return folder
        return exe_dir
    return Path(__file__).resolve().parents[1]
