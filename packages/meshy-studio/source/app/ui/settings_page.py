from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFormLayout, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout,
                               QWidget)

from app import bootstrap
from app.automation.model_export import find_blender
from app.mail.purelymail import API_DISABLED_REASON


class SettingsPage(QWidget):
    _done = Signal(object, object)

    def __init__(self, root: Path, settings: Any, pipeline: Any, mail: Any, database: Any, *,
                 choose_export: Callable[[], None], runner_label: Callable[[], str], parent: QWidget | None = None):
        super().__init__(parent)
        self.root, self.settings, self.pipeline, self.mail, self.database = Path(root), settings, pipeline, mail, database
        self._choose_export, self._runner_label = choose_export, runner_label
        self._done.connect(lambda callback, result: callback(*result))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = self._card(layout)
        form = QFormLayout()
        self.concurrency = QSpinBox(); self.concurrency.setRange(1, 3)
        self.timeout = QSpinBox(); self.timeout.setRange(5, 240); self.timeout.setSuffix(" min")
        self.retries = QSpinBox(); self.retries.setRange(0, 5)
        form.addRow("Parallel jobs", self.concurrency)
        form.addRow("Job time limit", self.timeout)
        form.addRow("Automatic retries", self.retries)
        card.addLayout(form)
        note = QLabel("Each parallel job uses its own account and browser. Retries only happen for failures BEFORE a job was "
                      "submitted to Meshy, so a retry can never start a second paid generation.")
        note.setWordWrap(True); note.setObjectName("muted")
        card.addWidget(note)
        row = QHBoxLayout()
        apply = QPushButton("Apply"); apply.clicked.connect(self.apply)
        export = QPushButton("Change export folder..."); export.setObjectName("secondary"); export.clicked.connect(lambda: self._choose_export())
        row.addWidget(apply); row.addWidget(export); row.addStretch(1)
        card.addLayout(row)
        self.apply_result = QLabel(""); self.apply_result.setObjectName("muted")
        card.addWidget(self.apply_result)

        env = self._card(layout)
        self.environment = QLabel(); self.environment.setWordWrap(True)
        self.environment.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        env.addWidget(self.environment)
        recheck = QPushButton("Check again / download missing parts"); recheck.setObjectName("secondary")
        recheck.clicked.connect(self.recheck)
        env.addWidget(recheck)

        mailcard = self._card(layout)
        self.api_status = QLabel(); self.api_status.setWordWrap(True)
        mailcard.addWidget(self.api_status)
        mrow = QHBoxLayout()
        self.mailbox = QComboBox()
        check = QPushButton("Check IMAP connection"); check.setObjectName("secondary"); check.clicked.connect(self.check_mail)
        mrow.addWidget(self.mailbox, 1); mrow.addWidget(check)
        mailcard.addLayout(mrow)
        self.mail_result = QLabel(""); self.mail_result.setObjectName("muted")
        mailcard.addWidget(self.mail_result)
        layout.addStretch(1)
        self.load()

    @staticmethod
    def _card_frame() -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(); frame.setObjectName("card")
        inner = QVBoxLayout(frame); inner.setContentsMargins(16, 14, 16, 14); inner.setSpacing(8)
        return frame, inner

    def _card(self, layout: QVBoxLayout) -> QVBoxLayout:
        frame, inner = self._card_frame()
        layout.addWidget(frame)
        return inner

    # ---- values ------------------------------------------------------------------------------------------------------
    def load(self) -> None:
        self.concurrency.setValue(self.settings.concurrency)
        self.timeout.setValue(self.settings.job_timeout_minutes)
        self.retries.setValue(self.settings.max_retries)
        self.refresh_environment()
        self.mailbox.clear()
        self.mailbox.addItems([m["email"] for m in self.database.list_mailboxes()])
        self.api_status.setText("Purelymail management API: " + (
            "enabled (configuration supplied by you)" if self.mail.api_enabled() else "DISABLED. " + API_DISABLED_REASON))

    def apply(self) -> None:
        self.settings.set("concurrency", self.concurrency.value())
        self.settings.set("job_timeout_minutes", self.timeout.value())
        self.settings.set("max_retries", self.retries.value())
        effective = self.pipeline.set_concurrency(self.concurrency.value())
        self.pipeline.max_retries = self.retries.value()
        self.pipeline.job_timeout_seconds = self.timeout.value() * 60
        self.apply_result.setText(f"Saved. Running with {effective} parallel job(s)"
                                  + ("" if effective == self.concurrency.value() else " (the worker factory is unavailable here)")
                                  + "; applies to the next job.")

    def refresh_environment(self) -> None:
        blender = find_blender(self.root)
        lines = [
            f"Data folder: {self.root}",
            f"Export folder: {self.settings.export_dir}",
            f"Browser: {'Google Chrome found' if bootstrap.chrome_path() else 'Chrome missing (a browser is downloaded on first run)'}",
            f"Model decoder: {'ready' if bootstrap.decoder_ready(self.root) else 'missing (downloaded on first run)'}",
            f"Blender (FBX export): {blender if blender else 'not found (a portable copy is downloaded on first FBX export)'}",
            f"Queue runner: {self._runner_label()}",
        ]
        self.environment.setText("\n".join(lines))

    def _background(self, work: Callable[[], Any], done: Callable[[Any, Any], None]) -> None:
        def run() -> None:
            try:
                outcome = (work(), None)
            except Exception as error:
                outcome = (None, error)
            self._done.emit(done, outcome)
        threading.Thread(target=run, daemon=True).start()

    def recheck(self) -> None:
        self.environment.setText("Checking and downloading missing parts...")
        self._background(lambda: bootstrap.prepare(self.root, lambda message: None),
                         lambda ok, error: self.refresh_environment())

    def check_mail(self) -> None:
        address = self.mailbox.currentText()
        if not address:
            self.mail_result.setText("Add a mailbox on the Purelymail page first.")
            return
        self.mail_result.setText(f"Checking {address}...")
        self._background(lambda: self.mail.check(address),
                         lambda status, error: self.mail_result.setText(f"{address}: {status if not error else type(error).__name__}"))
