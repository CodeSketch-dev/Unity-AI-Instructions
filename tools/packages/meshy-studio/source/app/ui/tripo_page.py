from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QProgressBar, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from app.tripo.client import TripoError
from app.tripo.options import DEFAULT_FACES, MAX_FACES, MIN_FACES, MODEL_VERSIONS, TripoOptions
from app.tripo.service import TripoService

COLUMNS = ["#", "Image", "Status", "Progress", "Result", "Note"]


def _open(path: str) -> None:
    if hasattr(os, "startfile"):
        os.startfile(path)


class TripoPage(QWidget):
    """Tripo tab: API key, its own generation options, its own queue. Runs through the official API (service.py)."""

    message = Signal(str)
    _balance = Signal(object)

    def __init__(self, service: TripoService, opener: Callable[[str], None] = _open, parent: QWidget | None = None):
        super().__init__(parent)
        self.service, self._opener = service, opener
        self._staged: list[str] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 20, 26, 10)
        layout.setSpacing(12)

        title = QLabel("Tripo - image to 3D (official API)")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        key_row = QHBoxLayout()
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("Tripo API key (tsk_...) from platform.tripo3d.ai -> API Keys. Stored in the Windows credential store.")
        self.save_key_button = QPushButton("Save key")
        self.save_key_button.clicked.connect(self._save_key)
        self.balance_label = QLabel("Credits: ?")
        self.balance_button = QPushButton("Check credits")
        self.balance_button.setObjectName("secondary")
        self.balance_button.clicked.connect(self.refresh_balance)
        key_row.addWidget(self.key_edit, 1)
        key_row.addWidget(self.save_key_button)
        key_row.addWidget(self.balance_button)
        key_row.addWidget(self.balance_label)
        layout.addLayout(key_row)

        card = QFrame()
        card.setObjectName("card")
        form = QFormLayout(card)
        self.version = QComboBox()
        self.version.setEditable(True)
        self.version.addItems(MODEL_VERSIONS)
        self.version.setToolTip("Tripo model version string sent to the API. Editable: use the newest one listed in the Tripo API docs.")
        self.faces = QSpinBox()
        self.faces.setRange(MIN_FACES, MAX_FACES)
        self.faces.setSingleStep(500)
        self.faces.setValue(DEFAULT_FACES)
        self.faces.setToolTip("face_limit: target triangle count (quads if Quad is on). Hero pieces 8-20k, props 1-5k.")
        self.quality = QComboBox()
        self.quality.addItems(["detailed", "standard"])
        self.align = QComboBox()
        self.align.addItems(["original_image", "geometry"])
        self.smart_low_poly = QCheckBox("Smart low poly (clean hand-made style topology)")
        self.smart_low_poly.setChecked(True)
        self.pbr = QCheckBox("PBR maps (more credits; not needed for the flat mobile look)")
        self.texture = QCheckBox("Texture")
        self.texture.setChecked(True)
        self.quad = QCheckBox("Quad mesh")
        self.download = QCheckBox("Download result (GLB + FBX; needs a Tripo plan that allows export)")
        form.addRow("Model version", self.version)
        form.addRow("Triangles (face_limit)", self.faces)
        form.addRow("Texture quality", self.quality)
        form.addRow("Texture alignment", self.align)
        form.addRow("", self.texture)
        form.addRow("", self.smart_low_poly)
        form.addRow("", self.pbr)
        form.addRow("", self.quad)
        form.addRow("", self.download)
        layout.addWidget(card)

        action = QHBoxLayout()
        self.choose_button = QPushButton("Choose images...")
        self.choose_button.clicked.connect(self._choose)
        self.staged_label = QLabel("No image chosen")
        self.generate_button = QPushButton("Generate with Tripo")
        self.generate_button.clicked.connect(self.generate)
        self.open_button = QPushButton("Open result folder")
        self.open_button.setObjectName("secondary")
        self.open_button.clicked.connect(self._open_result)
        action.addWidget(self.choose_button)
        action.addWidget(self.staged_label, 1)
        action.addWidget(self.open_button)
        action.addWidget(self.generate_button)
        layout.addLayout(action)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        self.progress = QProgressBar()
        self.progress.setVisible(False)

        self._balance.connect(self._show_balance)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_jobs)
        self._timer.start(2000)
        self._sync_key_state()

    # ---- key / balance ---------------------------------------------------------------------------------------------------
    def _sync_key_state(self) -> None:
        has = self.service.has_key()
        self.key_edit.setPlaceholderText("Key saved (paste a new one to replace it)" if has else self.key_edit.placeholderText())
        self._sync_generate()

    def _save_key(self) -> None:
        text = self.key_edit.text().strip()
        if not text:
            self.message.emit("Paste the Tripo API key first")
            return
        self.service.set_key(text)
        self.key_edit.clear()
        self.message.emit("Tripo API key saved to the Windows credential store")
        self._sync_key_state()
        self.refresh_balance()

    def refresh_balance(self) -> None:
        import threading
        if not self.service.has_key():
            self.message.emit("Save your Tripo API key first (platform.tripo3d.ai -> API Keys)")
            return

        def work() -> None:
            try:
                self._balance.emit(self.service.balance())
            except Exception as error:  # noqa: BLE001
                self._balance.emit(error)
        threading.Thread(target=work, daemon=True).start()

    def _show_balance(self, value: Any) -> None:
        if isinstance(value, Exception):
            self.balance_label.setText("Credits: error")
            self.message.emit(f"Tripo: {value}")
        else:
            self.balance_label.setText(f"Credits: {value}")

    # ---- staging / generate ----------------------------------------------------------------------------------------------
    def current_options(self) -> TripoOptions:
        return TripoOptions(self.version.currentText(), self.faces.value(), self.texture.isChecked(), self.pbr.isChecked(),
                            self.quality.currentText(), self.align.currentText(), self.smart_low_poly.isChecked(), self.quad.isChecked(), True,
                            "default", self.download.isChecked()).normalized()

    def stage(self, paths: list[str]) -> None:
        good = [p for p in paths if Path(p).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and Path(p).is_file()]
        self._staged = good
        self.staged_label.setText(f"{len(good)} image(s) ready" if good else "No image chosen")
        self._sync_generate()

    def _choose(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose images", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if paths:
            self.stage(paths)

    def _sync_generate(self) -> None:
        self.generate_button.setText(f"Generate with Tripo ({len(self._staged)})" if self._staged else "Generate with Tripo")

    def generate(self) -> None:
        if not self._staged:
            self.message.emit("Choose images first (Tripo tab)")
            return
        if not self.service.has_key():
            self.message.emit("Save your Tripo API key first (platform.tripo3d.ai -> API Keys)")
            return
        options, count = self.current_options(), 0
        for path in self._staged:
            try:
                self.service.submit(path, options)
                count += 1
            except TripoError as error:
                self.message.emit(f"Tripo: {error}")
                break
        self._staged = []
        self.staged_label.setText(f"Queued {count} job(s)" if count else "No image chosen")
        self._sync_generate()
        self.refresh_jobs()

    # ---- queue -----------------------------------------------------------------------------------------------------------
    def refresh_jobs(self) -> None:
        jobs = self.service.jobs()
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(reversed(jobs)):
            values = [job["id"], Path(job["image"]).name, job["status"], f"{job['progress']}%", job.get("result") or job.get("error") or "",
                      job.get("note", "")]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def _open_result(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self.message.emit("Select a finished Tripo job first")
            return
        result = self.table.item(row, 4)
        if result and Path(result.text()).is_dir():
            self._opener(result.text())
        else:
            self.message.emit("This job has no result folder yet")
