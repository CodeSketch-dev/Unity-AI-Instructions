from __future__ import annotations

import sys
import os
from pathlib import Path

import threading

from PySide6.QtCore import QSize, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QListWidgetItem, QInputDialog, QMessageBox, QPlainTextEdit, QAbstractItemView, QHBoxLayout, QApplication, QLabel, QListWidget, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit

from app.paths import app_root
from app.ui.theme import STYLE, status_color
from app.automation.meshy_worker import REQUIRED_CREDITS
from app.settings import Settings
from app import bootstrap
from app.logs import setup_logging, tail
from app.mail.manager import MailboxManager
from app.automation.browser_manager import BrowserManager
from app.automation.google_login import GoogleOAuthLogin
from app.automation.meshy_worker import MeshyWebWorker
from app.security.credentials import KeyringCredentialStore
from app.ui.browser_host import BrowserHostWidget
from app.core.database import Database
from app.core.account_manager import AccountManager
from app.core.pipeline import PipelineService, acquire_runner_lock


THUMB = 64


class MeshyMainWindow(QMainWindow):
    bootstrap_done = Signal(bool, str)
    _bg_done = Signal(object, object)

    def __init__(self, project_root: str | Path | None = None):
        super().__init__()
        root = Path(project_root or app_root())
        self.setWindowTitle("Meshy AI Studio")
        self.resize(1100, 720)
        self.setAcceptDrops(True)
        self.root = root
        self._owns_runner = False
        setup_logging(root)
        self.settings = Settings(root)
        self.browser_manager = BrowserManager(root / "profiles")
        self.database = Database(root / "data" / "meshy.sqlite3")
        self.account_manager = AccountManager(self.database, KeyringCredentialStore(), root / "profiles")
        self.meshy_worker = MeshyWebWorker(self.browser_manager, google_login=GoogleOAuthLogin(KeyringCredentialStore()), export_dir=lambda: self.settings.export_dir)
        self.browser_host = BrowserHostWidget(self.browser_manager)
        try:
            bootstrap.import_bundled_accounts(root, self.account_manager)
        except Exception as error:  # a broken accounts.txt must not stop the app
            print(f"accounts.txt import failed: {type(error).__name__}")
        self.mail = MailboxManager(self.database, KeyringCredentialStore())
        self._bg_done.connect(lambda done, result: done(*result))
        self.pipeline = PipelineService(self.database, self.meshy_worker)
        self._build_ui()
        self._refresh_accounts()
        self._refresh_jobs()
        self._owns_runner = False
        self.bootstrap_done.connect(self._on_bootstrap_done)
        if os.environ.get("MESHY_AUTOSTART", "1") != "0":
            self._root = root
            self.status.setText("Preparing decoder and browser (first start only)...")
            threading.Thread(target=self._bootstrap, args=(root,), daemon=True).start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_accounts)
        self._timer.timeout.connect(self._refresh_jobs)
        self._timer.timeout.connect(self._refresh_logs)
        self._timer.start(5000)

    def _build_ui(self) -> None:
        root_widget = QWidget(self)
        root_widget.setObjectName("root")
        outer = QHBoxLayout(root_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ----- sidebar: navigation, queue summary, emergency stop ---------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 18, 14, 14)
        side.setSpacing(4)
        brand = QLabel("Meshy AI Studio")
        brand.setObjectName("brand")
        tagline = QLabel("Image to textured 3D model")
        tagline.setObjectName("tagline")
        side.addWidget(brand)
        side.addWidget(tagline)
        side.addSpacing(14)
        self.page_names = ["Generate", "Queue", "Accounts", "Purelymail", "Library", "Settings", "Logs"]
        self.navigation = QListWidget()
        self.navigation.setObjectName("nav")
        self.navigation.addItems(self.page_names)
        self.navigation.setCurrentRow(0)
        self.navigation.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        side.addWidget(self.navigation, 1)
        self.summary = QLabel("")
        self.summary.setObjectName("summary")
        self.summary.setWordWrap(True)
        side.addWidget(self.summary)
        stop_button = QPushButton("EMERGENCY STOP")
        stop_button.setObjectName("danger")
        stop_button.setToolTip("Stops the running job at its next step, pauses the queue and closes the browsers")
        stop_button.clicked.connect(self._emergency_stop)
        resume_button = QPushButton("Resume queue")
        resume_button.setObjectName("secondary")
        resume_button.clicked.connect(self._resume_queue)
        side.addWidget(stop_button)
        side.addWidget(resume_button)
        outer.addWidget(sidebar)

        # ----- content -----------------------------------------------------------------------------------
        content = QWidget()
        column = QVBoxLayout(content)
        column.setContentsMargins(26, 20, 26, 10)
        column.setSpacing(12)
        header = QHBoxLayout()
        self.page_title = QLabel(self.page_names[0])
        self.page_title.setObjectName("pageTitle")
        self.alert = QLabel("")
        self.alert.setObjectName("alert")
        header.addWidget(self.page_title)
        header.addStretch(1)
        header.addWidget(self.alert)
        column.addLayout(header)
        self.pages = QStackedWidget()
        self._pages = [QWidget() for _ in self.page_names]
        layouts = []
        for page in self._pages:
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(12)
            layouts.append(page_layout)
            self.pages.addWidget(page)
        column.addWidget(self.pages, 1)
        self.status = QLabel("Ready")
        self.status.setObjectName("footer")
        column.addWidget(self.status)
        outer.addWidget(content, 1)

        self._build_generate_page(layouts[0])
        self._build_queue_page(layouts[1])
        self._build_accounts_page(layouts[2])
        self._build_mail_page(layouts[3])
        self._build_library_page(layouts[4])
        self._build_settings_page(layouts[5])
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        layouts[6].addWidget(self.log_view)

        self.navigation.currentRowChanged.connect(self._on_page_changed)
        self.setCentralWidget(root_widget)

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("card")
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(8)
        return frame, inner

    @staticmethod
    def _button(text: str, handler, *, secondary: bool = False, tip: str = "") -> QPushButton:
        button = QPushButton(text)
        if secondary:
            button.setObjectName("secondary")
        if tip:
            button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def _style_table(self, table: QTableWidget, row_height: int = 40) -> None:
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _build_generate_page(self, page_layout: QVBoxLayout) -> None:
        self.image_label = QPushButton("Drop images here, or click to choose\nPNG / JPG / WEBP, up to 20 MB each")
        self.image_label.setObjectName("dropzone")
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.setMinimumHeight(190)
        self.image_label.setToolTip("Every image you drop or choose is queued immediately")
        self.image_label.clicked.connect(self._choose_image)
        page_layout.addWidget(self.image_label)
        card, inner = self._card()
        title = QLabel("Save models to")
        title.setObjectName("muted")
        inner.addWidget(title)
        self.export_label = QLabel()
        self.export_label.setWordWrap(True)
        self.export_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        inner.addWidget(self.export_label)
        row = QHBoxLayout()
        row.addWidget(self._button("Change folder...", self._choose_export_dir))
        row.addWidget(self._button("Open folder", self._open_export_dir, secondary=True))
        row.addStretch(1)
        inner.addLayout(row)
        hint = QLabel("Each model gets its own sub-folder with the GLB, the FBX and textures/*.png")
        hint.setObjectName("muted")
        inner.addWidget(hint)
        page_layout.addWidget(card)
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Optional note saved with the next jobs")
        page_layout.addWidget(self.prompt_input)
        page_layout.addStretch(1)
        self._refresh_export_label()

    def _build_queue_page(self, page_layout: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.addWidget(self._button("Cancel selected", self._cancel_selected,
                                   tip="Select one or more jobs (Ctrl/Shift). Queued jobs behind them move up."))
        bar.addWidget(self._button("Retry selected", self._retry_selected, secondary=True))
        bar.addWidget(self._button("Resume paused", self._resume_queue, secondary=True))
        bar.addStretch(1)
        page_layout.addLayout(bar)
        self.jobs_table = QTableWidget(0, 6)
        self.jobs_table.setHorizontalHeaderLabels(["Preview", "Job", "Image", "Status", "Account", "Note / error"])
        self._style_table(self.jobs_table, THUMB + 12)
        self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.jobs_table.setIconSize(QSize(THUMB, THUMB))
        self.jobs_table.setColumnWidth(0, THUMB + 24)
        self.jobs_table.setColumnWidth(1, 56)
        self.jobs_table.setColumnWidth(2, 190)
        self.jobs_table.setColumnWidth(3, 120)
        self.jobs_table.setColumnWidth(4, 210)
        page_layout.addWidget(self.jobs_table, 1)
        self._thumbs: dict[str, QIcon] = {}

    def _build_accounts_page(self, page_layout: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.addWidget(self._button("Use selected account", self._pin_selected_account,
                                   tip="Run all jobs on this account (overrides its rest period); paused jobs continue"))
        bar.addWidget(self._button("Automatic rotation", self._auto_rotation, secondary=True))
        bar.addWidget(self._button("Import list (.txt)", self._import_accounts, secondary=True))
        bar.addWidget(self._button("Refresh", self._refresh_accounts, secondary=True))
        bar.addStretch(1)
        page_layout.addLayout(bar)
        self.accounts_table = QTableWidget(0, 5)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Status", "Credit", "Session", "Active jobs"])
        self._style_table(self.accounts_table)
        self.accounts_table.setSortingEnabled(True)
        self.accounts_table.setColumnWidth(0, 250)
        self.accounts_table.setColumnWidth(1, 290)
        self.accounts_table.setColumnWidth(2, 90)
        self.accounts_table.setColumnWidth(3, 120)
        page_layout.addWidget(self.accounts_table, 1)
        note = QLabel(f"A model needs {REQUIRED_CREDITS} credits. Accounts below that rest automatically; "
                      "jobs pause when none is left. The app never creates Meshy accounts.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        page_layout.addWidget(note)

    def _build_library_page(self, page_layout: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.addWidget(self._button("Open selected", self._open_selected_model))
        bar.addWidget(self._button("Open export folder", self._open_export_dir, secondary=True))
        bar.addWidget(self._button("Refresh", self._refresh_library, secondary=True))
        bar.addStretch(1)
        page_layout.addLayout(bar)
        self.library_list = QListWidget()
        self.library_list.itemDoubleClicked.connect(lambda _item: self._open_selected_model())
        page_layout.addWidget(self.library_list, 1)

    def _build_settings_page(self, page_layout: QVBoxLayout) -> None:
        card, inner = self._card()
        self.settings_info = QLabel()
        self.settings_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.settings_info.setWordWrap(True)
        inner.addWidget(self.settings_info)
        inner.addWidget(self._button("Check again / download missing parts", self._recheck_setup, secondary=True))
        page_layout.addWidget(card)
        page_layout.addStretch(1)
        self._refresh_settings()

    # ----- navigation / small pages -------------------------------------------------------------------------
    @Slot(int)
    def _on_page_changed(self, row: int) -> None:
        self.pages.setCurrentIndex(row)
        self.page_title.setText(self.page_names[row])
        if self.page_names[row] == "Library":
            self._refresh_library()
        elif self.page_names[row] == "Settings":
            self._refresh_settings()

    @Slot()
    def _refresh_library(self) -> None:
        base = self.settings.export_dir
        self.library_list.clear()
        folders = sorted((p for p in base.glob("*") if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True) if base.is_dir() else []
        for folder in folders:
            files = sorted(f.suffix.lstrip(".").upper() for f in folder.iterdir() if f.suffix.lower() in (".glb", ".fbx"))
            item = QListWidgetItem(f"{folder.name}    [{' + '.join(files) or 'empty'}]")
            item.setData(Qt.ItemDataRole.UserRole, str(folder))
            self.library_list.addItem(item)

    @Slot()
    def _open_selected_model(self) -> None:
        item = self.library_list.currentItem()
        if item is not None and hasattr(os, "startfile"):
            os.startfile(item.data(Qt.ItemDataRole.UserRole))

    def _refresh_settings(self) -> None:
        from app.automation.model_export import find_blender
        blender = find_blender(self.root)
        lines = [
            f"Data folder: {self.root}",
            f"Export folder: {self.settings.export_dir}",
            f"Browser: {'Google Chrome found' if bootstrap.chrome_path() else 'Chrome missing (a browser is downloaded on first run)'}",
            f"Model decoder: {'ready' if bootstrap.decoder_ready(self.root) else 'missing (downloaded on first run)'}",
            f"Blender (FBX export): {blender if blender else 'not found (portable copy is downloaded on first FBX export)'}",
            f"Queue runner: {'this window' if self._owns_runner else 'another process'}",
        ]
        self.settings_info.setText("\n".join(lines))

    @Slot()
    def _recheck_setup(self) -> None:
        self.status.setText("Checking and downloading missing parts...")
        self._background(lambda: bootstrap.prepare(self.root, lambda message: None),
                         lambda ok, error: (self.status.setText("Setup complete" if ok and not error else "Setup incomplete - see Settings"),
                                            self._refresh_settings()))

    def open_meshy_profile(self) -> None:
        if not self.browser_host.hosted:
            self.browser_host.start(self._first_account_id())
        self.status.setText("Meshy profile opened — complete Google sign-in manually if requested")

    def _refresh_export_label(self) -> None:
        self.export_label.setText(str(self.settings.export_dir))

    @Slot()
    def _choose_export_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder", str(self.settings.export_dir))
        if folder:
            self.settings.export_dir = folder
            self._refresh_export_label()
            self.status.setText(f"Export folder set to {folder}")

    @Slot()
    def _open_export_dir(self) -> None:
        folder = self.settings.export_dir
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder)) if hasattr(os, "startfile") else None

    @Slot()
    def _choose_image(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose input images", "", "Images (*.png *.jpg *.jpeg *.webp)")
        for path in paths:
            self._enqueue(path)
        if paths:
            self.image_label.setText(f"Queued {len(paths)} image(s).\nDrop or click to add more")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        accepted = False
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                self.image_label.setText(f"Queued: {Path(path).name}")
                self._enqueue(path)
                accepted = True
        if accepted:
            event.acceptProposedAction()

    @Slot()
    def _generate_from_ui(self) -> None:
        paths = getattr(self, "_selected_images", [])
        if not paths:
            self.status.setText("Choose or drop input images first")
            return
        for path in paths:
            self._enqueue(path)
        self._selected_images = []
        self.image_label.setText(f"Queued {len(paths)} image(s) - drop or choose more")

    def _enqueue(self, path: str) -> None:
        try:
            job_id = self.pipeline.enqueue(path, self.prompt_input.text())
        except ValueError as error:
            self.status.setText(f"Rejected: {error}")
            return
        self.status.setText(f"Job {job_id} queued — runs automatically" if self._owns_runner
                            else f"Job {job_id} queued — another runner process will pick it up")
        self._refresh_jobs()

    def _bootstrap(self, root: Path) -> None:
        messages: list[str] = []
        ok = bootstrap.prepare(root, messages.append)
        self.bootstrap_done.emit(ok, messages[-1] if messages else "")

    @Slot(bool, str)
    def _on_bootstrap_done(self, ok: bool, message: str) -> None:
        if not ok:
            self.status.setText(f"Setup incomplete: {message}")
        self._start_pipeline(self._root)

    def _start_pipeline(self, root: Path) -> None:
        if acquire_runner_lock(root / "data" / "runner.lock"):
            self._owns_runner = True
            self.pipeline.start_background()
            image = os.environ.get("MESHY_INPUT_IMAGE")
            if image:
                self._enqueue(image)
        else:
            self.status.setText("A headless runner is active; this window only queues jobs")

    # ----- emergency stop / account choice ---------------------------------------------------------------
    @Slot()
    def _emergency_stop(self) -> None:
        self.pipeline.emergency_stop()
        self.meshy_worker.release_all()
        self.status.setText("EMERGENCY STOP: queue paused, running job stops at its next step, browsers closed")
        self._refresh_jobs()

    @Slot()
    def _resume_queue(self) -> None:
        if self._owns_runner:
            self.pipeline.resume_queue()
        else:
            self.database.resume_paused_jobs()
        self.status.setText("Queue resumed")
        self._refresh_jobs()

    def _selected_account(self):
        rows = {index.row() for index in self.accounts_table.selectedIndexes()}
        if len(rows) != 1:
            return None
        email = self.accounts_table.item(next(iter(rows)), 0).text().replace(" [selected]", "")
        return self.database.account_by_email(email)

    @Slot()
    def _pin_selected_account(self) -> None:
        account = self._selected_account()
        if account is None:
            self.status.setText("Select exactly one account first")
            return
        self.pipeline.use_account(account.id)
        self.status.setText(f"All jobs now run on {account.email}")
        self._refresh_accounts()

    @Slot()
    def _auto_rotation(self) -> None:
        self.pipeline.use_account(None)
        self.status.setText("Automatic account rotation")
        self._refresh_accounts()

    # ----- Purelymail ------------------------------------------------------------------------------------
    def _background(self, work, done) -> None:
        def run() -> None:
            try:
                outcome = (work(), None)
            except Exception as error:
                outcome = (None, error)
            self._bg_done.emit(done, outcome)
        threading.Thread(target=run, daemon=True).start()

    def _build_mail_page(self, page_layout) -> None:
        note = QLabel("Existing mailboxes only. API token and mailbox passwords are kept in the Windows credential store. "
                      "The management API endpoints are unverified defaults (see README).")
        note.setWordWrap(True)
        page_layout.addWidget(note)
        token_row = QHBoxLayout()
        self.mail_token = QLineEdit()
        self.mail_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.mail_token.setPlaceholderText("Purelymail API token (stored securely, never shown again)")
        save_token = QPushButton("Save token")
        save_token.clicked.connect(self._save_mail_token)
        token_row.addWidget(self.mail_token, 1)
        token_row.addWidget(save_token)
        page_layout.addLayout(token_row)
        self.mail_table = QTableWidget(0, 4)
        self.mail_table.setHorizontalHeaderLabels(["Mailbox", "Status", "Expires", "Last checked"])
        self._style_table(self.mail_table)
        self.mail_table.setColumnWidth(0, 300)
        self.mail_table.setColumnWidth(1, 130)
        self.mail_table.setColumnWidth(2, 220)
        page_layout.addWidget(self.mail_table, 1)
        row = QHBoxLayout()
        for label, handler, secondary in (("Add mailbox...", self._add_mailbox, False), ("Sync from API", self._sync_mailboxes, True),
                                          ("Check login", self._check_mailbox, True), ("Read mail / OTP", self._read_mailbox, True)):
            row.addWidget(self._button(label, handler, secondary=secondary))
        row.addStretch(1)
        page_layout.addLayout(row)
        self.mail_view = QPlainTextEdit()
        self.mail_view.setReadOnly(True)
        page_layout.addWidget(self.mail_view)
        self._refresh_mailboxes()

    @Slot()
    def _refresh_mailboxes(self) -> None:
        rows = self.database.list_mailboxes()
        self.mail_table.setRowCount(len(rows))
        soon = {m["email"] for m in self.mail.expiring()}
        for index, mailbox in enumerate(rows):
            expires = (mailbox["expires_at"] or "") + (" (expiring!)" if mailbox["email"] in soon else "")
            for col, value in enumerate((mailbox["email"], mailbox["status"], expires, mailbox["last_checked_at"] or "")):
                self.mail_table.setItem(index, col, QTableWidgetItem(value))
        if soon:
            self.alert.setText(f"{len(soon)} mailbox(es) expire within 7 days")

    def _selected_mailbox(self) -> str | None:
        rows = {index.row() for index in self.mail_table.selectedIndexes()}
        return self.mail_table.item(next(iter(rows)), 0).text() if len(rows) == 1 else None

    @Slot()
    def _save_mail_token(self) -> None:
        if self.mail_token.text().strip():
            self.mail.set_api_token(self.mail_token.text().strip())
            self.mail_token.clear()
            self.status.setText("Purelymail token saved")

    @Slot()
    def _add_mailbox(self) -> None:
        address, ok = QInputDialog.getText(self, "Add mailbox", "Mailbox address:")
        if not ok or "@" not in address:
            return
        password, ok = QInputDialog.getText(self, "Add mailbox", "Mailbox password:", QLineEdit.EchoMode.Password)
        if not ok or not password:
            return
        days, ok = QInputDialog.getInt(self, "Add mailbox", "Days until it expires (0 = never):", 0, 0, 3650)
        self.mail.add_mailbox(address.strip(), password, expires_in_days=days or None)
        self._refresh_mailboxes()

    @Slot()
    def _sync_mailboxes(self) -> None:
        self.status.setText("Syncing mailboxes from the Purelymail API...")
        self._background(self.mail.sync_from_api, self._after_sync)

    def _after_sync(self, added, error) -> None:
        self.status.setText(f"Sync failed: {error}" if error else f"Sync done: {len(added)} new mailbox(es)")
        self._refresh_mailboxes()

    @Slot()
    def _check_mailbox(self) -> None:
        address = self._selected_mailbox()
        if address:
            self.status.setText(f"Checking {address}...")
            self._background(lambda: self.mail.check(address), lambda status, error: (
                self.status.setText(f"{address}: {status if not error else error}"), self._refresh_mailboxes()))

    @Slot()
    def _read_mailbox(self) -> None:
        address = self._selected_mailbox()
        if not address:
            self.status.setText("Select one mailbox first")
            return
        self._background(lambda: self.mail.read(address, limit=10), self._show_mail)

    def _show_mail(self, messages, error) -> None:
        if error:
            self.mail_view.setPlainText(f"Could not read mail: {type(error).__name__}")
            return
        from app.mail.purelymail import extract_otp
        lines = []
        for message in messages:
            code = extract_otp(message.subject) or extract_otp(message.body)
            lines.append(f"{message.received or ''}  {message.sender}\n  {message.subject}" + (f"\n  code: {code}" if code else ""))
        self.mail_view.setPlainText("\n\n".join(lines) or "No messages")

    @Slot()
    def _refresh_logs(self) -> None:
        text = tail(self.root)
        if text != self.log_view.toPlainText():
            self.log_view.setPlainText(text)
            self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def _thumbnail(self, image_path: str) -> QIcon:
        icon = self._thumbs.get(image_path)
        if icon is None:
            pixmap = QPixmap(image_path)
            icon = QIcon(pixmap.scaled(THUMB, THUMB, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)) if not pixmap.isNull() else QIcon()
            self._thumbs[image_path] = icon
        return icon

    def _selected_job_ids(self) -> list[int]:
        rows = {index.row() for index in self.jobs_table.selectedIndexes()}
        ids = []
        for row in sorted(rows):
            item = self.jobs_table.item(row, 1)
            if item is not None:
                ids.append(int(item.text()))
        return sorted(ids)  # act on jobs in their original order

    @Slot()
    def _refresh_jobs(self) -> None:
        keep = set(self._selected_job_ids())
        jobs = self.database.list_jobs()[:200]
        positions = {job.id: self.database.queue_position(job.id) for job in jobs}
        # running first, then the queue in run order, then finished jobs (newest first)
        terminal = {"Completed", "Failed", "Canceled"}
        jobs.sort(key=lambda j: (0, 0, j.id) if j.status not in terminal and not positions[j.id]
                  else (1, positions[j.id], j.id) if positions[j.id] else (2, 0, -j.id))
        emails = {a.id: a.email for a in self.database.list_accounts()}
        self.jobs_table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            position = positions[job.id]
            status = f"Queued #{position}" if position else job.status
            preview = QTableWidgetItem()
            preview.setIcon(self._thumbnail(job.image_path))
            self.jobs_table.setItem(row, 0, preview)
            values = (str(job.id), Path(job.image_path).name, status, emails.get(job.account_id, ""), job.error or job.note)
            for col, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                if col == 3:
                    item.setForeground(QColor(status_color(value)))
                self.jobs_table.setItem(row, col, item)
        queued = sum(1 for j in jobs if positions[j.id])
        running = sum(1 for j in jobs if j.status in ("Generating", "Uploading", "Checking Account", "Downloading", "Cancel Requested"))
        self.summary.setText(f"{running} running  |  {queued} queued")
        self.jobs_table.clearSelection()
        mode = self.jobs_table.selectionMode()
        self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for row in range(self.jobs_table.rowCount()):
            if int(self.jobs_table.item(row, 1).text()) in keep:
                self.jobs_table.selectRow(row)
        self.jobs_table.setSelectionMode(mode)

    @Slot()
    def _cancel_selected(self) -> None:
        ids = self._selected_job_ids()
        if not ids:
            self.status.setText("Select one or more jobs in the queue first")
            return
        outcome = self.pipeline.cancel_jobs(ids)
        self.status.setText(f"Canceled {len(outcome['canceled'])} queued job(s); {len(outcome['stopping'])} running job(s) will stop at the next step")
        self._refresh_jobs()

    @Slot()
    def _retry_selected(self) -> None:
        count = self.database.requeue_jobs(self._selected_job_ids())
        self.status.setText(f"Re-queued {count} job(s)")
        self._refresh_jobs()

    @Slot()
    def _refresh_accounts(self) -> None:
        if not hasattr(self, "accounts_table"):
            return
        accounts = self.database.list_accounts()
        if not accounts:
            # Surface existing Playwright profiles even before an account import
            # file is loaded, so the operator can see what the app can rotate.
            profile_dirs = sorted(self.browser_manager.profiles_root.glob("account_*"))
            for path in profile_dirs:
                try:
                    account_id = int(path.name.split("_")[-1])
                except ValueError:
                    continue
                from app.core.models import Account
                accounts.append(Account(account_id, path.name, None, account_id, str(path), "Profile detected", False, True, 0))
        low = [a for a in accounts if a.credit_balance is not None and a.credit_balance < REQUIRED_CREDITS
               and a.status.lower() not in ("quota limited",)]
        self.alert.setText(f"{len(low)} account(s) low on credits" if low else "")
        self.accounts_table.setSortingEnabled(False)  # sorting while filling moves rows under the loop
        self.accounts_table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            status = f"{account.status} (until {account.cooldown_until} UTC)" if getattr(account, "cooldown_until", None) else account.status
            credit = "Unknown" if account.credit_balance is None else (
                f"{account.credit_balance}  (low)" if account.credit_balance < REQUIRED_CREDITS else str(account.credit_balance))
            pinned = " [selected]" if account.id == self.pipeline.manual_account_id else ""
            values = [account.email + pinned, status, credit, "Valid" if account.session_valid else "Not connected", str(account.active_jobs)]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2 and account.credit_balance is not None:
                    item.setForeground(QColor("#ff6b6b" if account.credit_balance < REQUIRED_CREDITS else "#4cc38a"))
                if col == 1 and account.status.lower() in ("quota limited", "needs verification", "invalid credentials", "login failed"):
                    item.setForeground(QColor("#ffb347"))
                self.accounts_table.setItem(row, col, item)
        self.accounts_table.setSortingEnabled(True)

    @Slot()
    def _import_accounts(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import account list", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return
        result = self.account_manager.import_file(path)
        self._refresh_accounts()
        self.status.setText(f"Imported {result.imported} accounts | duplicates {result.duplicates} | invalid {result.invalid}")

    @staticmethod
    def _first_account_id() -> int:
        try:
            return max(1, int(os.environ.get("MESHY_FIRST_ACCOUNT_ID", "1")))
        except ValueError:
            return 1


def create_app(argv: list[str] | None = None) -> tuple[QApplication, MeshyMainWindow]:
    app = QApplication(argv or sys.argv)
    app.setStyleSheet(STYLE)
    window = MeshyMainWindow()
    return app, window


def main() -> int:
    app, window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
