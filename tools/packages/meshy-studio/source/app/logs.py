from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from app.security.redaction import redact


class _RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


def log_path(root: Path) -> Path:
    return Path(root) / "data" / "logs" / "app.log"


def setup_logging(root: Path) -> Path:
    """Rotating file log (1 MB x 3). Passwords, cookies and tokens are redacted before writing."""
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("meshy")
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) and h.baseFilename == str(path.resolve())
               for h in logger.handlers):
        handler = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(_RedactFilter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return path


def tail(root: Path, lines: int = 200) -> str:
    try:
        return "\n".join(log_path(root).read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""
