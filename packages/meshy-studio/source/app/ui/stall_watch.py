from __future__ import annotations

import logging
import time

from PySide6.QtCore import QObject, QTimer

LOG = logging.getLogger("meshy.ui")


class StallWatch(QObject):
    """Logs every time the UI thread was blocked longer than `threshold` seconds (a frozen window is a bug)."""

    def __init__(self, threshold: float = 0.5, interval_ms: int = 100, parent: QObject | None = None):
        super().__init__(parent)
        self.threshold = threshold
        self.worst = 0.0
        self._last = time.monotonic()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._beat)
        self._timer.start(interval_ms)

    def _beat(self) -> None:
        now = time.monotonic()
        gap = now - self._last
        self._last = now
        self.worst = max(self.worst, gap)
        if gap > self.threshold:
            LOG.warning("UI thread was blocked for %.1fs", gap)
