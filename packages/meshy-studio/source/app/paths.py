from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Folder holding data/, profiles/, Export/ and docs/vendor.

    From source it is the repo root. A frozen exe uses its own folder, except when it sits inside the
    source tree (e.g. dist/) where it shares the repo's data.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "source" / "app" / "main.py").is_file():  # published layout: exe beside publish.bat and source
            return exe_dir / "source"
        for folder in (exe_dir, *exe_dir.parents):
            if (folder / "app" / "main.py").is_file():
                return folder
        return exe_dir
    return Path(__file__).resolve().parents[1]


def default_export_dir(root: Path) -> Path:
    """Models go to an Export folder next to publish.bat / MeshyAIStudio.exe so the team finds them at once."""
    root = Path(root)
    return root.parent / "Export" if root.name == "source" and (root / "app" / "main.py").is_file() else root / "Export"
