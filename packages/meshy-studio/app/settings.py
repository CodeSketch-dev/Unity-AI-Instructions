from __future__ import annotations

import json
from pathlib import Path


class Settings:
    """Tiny JSON settings file (data/settings.json); currently only the export folder."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "data" / "settings.json"

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    @property
    def export_dir(self) -> Path:
        value = self._load().get("export_dir")
        return Path(value) if value else self.root / "Export"

    @export_dir.setter
    def export_dir(self, value: str | Path) -> None:
        data = self._load()
        data["export_dir"] = str(Path(value))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
