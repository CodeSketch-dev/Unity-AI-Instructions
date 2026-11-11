from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

THUMB = 56


def _open(path: str) -> None:
    if hasattr(os, "startfile"):
        os.startfile(path)  # Windows Explorer / default application


class LibraryPage(QWidget):
    """Exported models (the `models` table). Removing a record never deletes files from disk."""

    COLUMNS = ["Preview", "Name", "Formats", "Triangles", "Size", "Created", "Folder"]
    message = Signal(str)  # shown in the main status bar: every button says what it did (or why it could not)

    def __init__(self, database: Any, opener: Callable[[str], None] = _open,
                 confirm: Callable[[str], bool] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.database, self._opener = database, opener
        self._confirm = confirm or self._ask
        self._icons: dict[str, QIcon] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name or folder")
        self.search.textChanged.connect(self.refresh)
        self.format_filter = QComboBox()
        self.format_filter.addItems(["All formats", "GLB", "FBX"])
        self.format_filter.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)
        bar.addWidget(self.format_filter)
        layout.addLayout(bar)
        buttons = QHBoxLayout()
        for text, handler, secondary in (("Open model", self.open_model, False), ("Show in folder", self.open_folder, True),
                                         ("Remove record", self.remove_record, True), ("Refresh", self.refresh_clicked, True)):
            button = QPushButton(text)
            if secondary:
                button.setObjectName("secondary")
            button.clicked.connect(handler)
            buttons.addWidget(button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(THUMB + 12)
        self.table.setIconSize(QSize(THUMB, THUMB))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column, width in enumerate((THUMB + 24, 220, 110, 100, 90, 160)):
            self.table.setColumnWidth(column, width)
        self.table.itemDoubleClicked.connect(lambda _item: self.open_model())
        layout.addWidget(self.table, 1)
        self.refresh()
        # Files deleted or renamed in Explorer must update the records: re-check the disk while the page is open.
        self._disk_timer = QTimer(self)
        self._disk_timer.setInterval(3000)
        self._disk_timer.timeout.connect(self._poll_disk)
        self._disk_timer.start()

    def _poll_disk(self) -> None:
        if self.isVisible():
            self.refresh()

    def _icon(self, path: str | None) -> QIcon:
        if not path or not Path(path).is_file():
            return QIcon()
        if path not in self._icons:
            pixmap = QPixmap(path)
            self._icons[path] = QIcon(pixmap.scaled(THUMB, THUMB, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation)) if not pixmap.isNull() else QIcon()
        return self._icons[path]

    def records(self) -> list[dict]:
        needle = self.search.text().strip().lower()
        wanted = self.format_filter.currentText()
        rows = []
        for model in self.database.list_models():
            if needle and needle not in (model["name"] or "").lower() and needle not in (model["folder"] or "").lower():
                continue
            if wanted != "All formats" and wanted not in (model["formats"] or ""):
                continue
            rows.append(model)
        return rows

    def sync_with_disk(self) -> int:
        """Drop records whose files are gone; fix the formats of records that lost only one format. Returns changes."""
        changed = 0
        for model in self.database.list_models():
            folder = Path(model["folder"] or "")
            main = Path(model["file_path"] or "")
            if main.is_file():
                present = ",".join(sorted({f.suffix.lstrip(".").upper() for f in folder.iterdir()
                                          if f.suffix.lower() in (".glb", ".fbx")})) if folder.is_dir() else ""
                if present and present != (model["formats"] or ""):
                    self.database.update_model_formats(model["id"], present)
                    changed += 1
                continue
            survivors = sorted(f for f in folder.glob("*") if f.suffix.lower() in (".glb", ".fbx")) if folder.is_dir() else []
            if survivors:  # the GLB is gone but the FBX is still there: keep the record pointing at what exists
                self.database.update_model_file(model["id"], str(survivors[0]),
                                                ",".join(sorted({f.suffix.lstrip(".").upper() for f in survivors})))
            else:
                self.database.delete_model_record(model["id"])
            changed += 1
        return changed

    def refresh_clicked(self, *_args) -> None:
        self.refresh()
        self.message.emit(f"Library refreshed ({self.table.rowCount()} model(s))")

    def refresh(self, *_args) -> None:
        self.sync_with_disk()
        selected = self.selected_id()
        rows = self.records()
        self.table.setRowCount(len(rows))
        for row, model in enumerate(rows):
            missing = not Path(model["file_path"] or "").is_file()
            preview = QTableWidgetItem()
            preview.setIcon(self._icon(model["thumbnail_path"]))
            preview.setData(Qt.ItemDataRole.UserRole, model["id"])
            self.table.setItem(row, 0, preview)
            size = f"{(model['size_bytes'] or 0) / 1048576:.1f} MB"
            values = (model["name"] + ("  (file missing)" if missing else ""), model["formats"] or "", f"{model['triangles'] or 0:,}",
                      size, model["created_at"] or "", model["folder"] or "")
            for column, value in enumerate(values, start=1):
                self.table.setItem(row, column, QTableWidgetItem(value))
            if model["id"] == selected:
                self.table.selectRow(row)
        if rows and self.selected_id() is None:
            self.table.selectRow(0)  # something is always selected, so Open / Show / Remove work at once

    def selected_id(self) -> int | None:
        rows = {index.row() for index in self.table.selectedIndexes()}
        if len(rows) != 1:
            return None
        item = self.table.item(next(iter(rows)), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_model(self) -> dict | None:
        model_id = self.selected_id()
        return next((m for m in self.database.list_models() if m["id"] == model_id), None)

    def open_model(self) -> bool:
        model = self._selected_model()
        if model is None:
            self.message.emit("Library is empty: generate a model first" if not self.records() else "Select a model first")
            return False
        if not Path(model["file_path"] or "").is_file():
            self.message.emit("That file no longer exists")
            self.refresh()
            return False
        self._opener(model["file_path"])
        self.message.emit(f"Opened {model['name']}")
        return True

    def open_folder(self) -> bool:
        model = self._selected_model()
        if model is None:
            self.message.emit("Select a model first")
            return False
        if not Path(model["folder"] or "").is_dir():
            self.message.emit("That folder no longer exists")
            self.refresh()
            return False
        self._opener(model["folder"])
        self.message.emit("Opened the folder")
        return True

    def remove_record(self) -> bool:
        """Removes only the Library record; the exported files stay on disk."""
        model = self._selected_model()
        if model is None:
            self.message.emit("Select a model first")
            return False
        if not self._confirm(f"Remove '{model['name']}' from the Library?\n\nThe files in\n{model['folder']}\nare NOT deleted."):
            return False
        self.database.delete_model_record(model["id"])
        self.refresh()
        self.message.emit(f"Removed the record of {model['name']} (files stay on disk)")
        return True

    def _ask(self, text: str) -> bool:
        return QMessageBox.question(self, "Remove record", text) == QMessageBox.StandardButton.Yes
