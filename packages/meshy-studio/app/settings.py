from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "concurrency": 1,           # parallel jobs (each on its own account, own browser)
    "job_timeout_minutes": 30,  # whole job; checked at every step boundary
    "max_retries": 2,           # automatic retries, only for failures BEFORE the job was submitted to Meshy
    "purelymail_api": None,     # {"base_url", "token_header", "endpoints": {"list_users", "list_domains", "check_credit"}}
}


class Settings:
    """Persistent JSON settings (data/settings.json). Written atomically so a crash cannot corrupt it."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "data" / "settings.json"

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
        os.replace(temp, self.path)

    def get(self, key: str) -> Any:
        return self._load().get(key, DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        data = self._load()
        data[key] = value
        self._save(data)

    @property
    def export_dir(self) -> Path:
        value = self._load().get("export_dir")
        return Path(value) if value else self.root / "Export"

    @export_dir.setter
    def export_dir(self, value: str | Path) -> None:
        self.set("export_dir", str(Path(value)))

    def _int(self, key: str, low: int, high: int) -> int:
        try:
            return max(low, min(high, int(self.get(key))))
        except (TypeError, ValueError):
            return int(DEFAULTS[key])

    @property
    def concurrency(self) -> int:
        return self._int("concurrency", 1, 3)

    @property
    def job_timeout_minutes(self) -> int:
        return self._int("job_timeout_minutes", 5, 240)

    @property
    def max_retries(self) -> int:
        return self._int("max_retries", 0, 5)
