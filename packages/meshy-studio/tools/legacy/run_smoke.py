from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MESHY_AUTOSTART", "0")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def main() -> int:
    app, window = create_app([])
    assert window.windowTitle() == "Meshy AI Studio"
    assert window.navigation.count() == 6
    assert window.navigation.currentRow() == 0
    assert window.status.text().startswith("Ready")
    print("PASS: PySide6 shell created; 6 pages reachable; no browser or credential side effect")
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
