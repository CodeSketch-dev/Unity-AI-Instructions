from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QPlainTextEdit, QPushButton,
                               QVBoxLayout, QWidget)

from app.logs import tail

LEVELS = ["All levels", "WARNING and above", "ERROR only"]
_RANK = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


def filter_lines(text: str, level: str = "All levels", needle: str = "") -> str:
    """Level filter plus a free-text filter (e.g. 'job 12' or '#3' for an account). Secrets are redacted at write time."""
    minimum = {"WARNING and above": 30, "ERROR only": 40}.get(level, 0)
    needle = needle.strip().lower()
    kept = []
    for line in text.splitlines():
        parts = line.split(" ", 3)
        rank = next((_RANK[p] for p in parts[:4] if p in _RANK), 20)
        if rank >= minimum and (not needle or needle in line.lower()):
            kept.append(line)
    return "\n".join(kept)


class LogsPage(QWidget):
    def __init__(self, root: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.root = Path(root)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.level = QComboBox()
        self.level.addItems(LEVELS)
        self.level.currentIndexChanged.connect(self.refresh)
        self.needle = QLineEdit()
        self.needle.setPlaceholderText("Filter by text, e.g. job 12, #3 (account), error")
        self.needle.textChanged.connect(self.refresh)
        export = QPushButton("Export log...")
        export.setObjectName("secondary")
        export.clicked.connect(self.export)
        bar.addWidget(self.level)
        bar.addWidget(self.needle, 1)
        bar.addWidget(export)
        layout.addLayout(bar)
        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        layout.addWidget(self.view, 1)

    def filtered(self) -> str:
        return filter_lines(tail(self.root, 1000), self.level.currentText(), self.needle.text())

    def refresh(self) -> None:
        text = self.filtered()
        if text != self.view.toPlainText():
            self.view.setPlainText(text)
            self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def export(self, path: str | None = None) -> str | None:
        """Writes the CURRENT (filtered) view. The log is already redacted, so nothing secret is exported."""
        if not isinstance(path, str):
            path, _ = QFileDialog.getSaveFileName(self, "Export log", "meshy-log.txt", "Text files (*.txt)")
        if not path:
            return None
        Path(path).write_text(self.filtered() + "\n", encoding="utf-8")
        return path
