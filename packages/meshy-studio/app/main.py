from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                               QListView, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton,
                               QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from app import bootstrap
from app.automation.browser_manager import BrowserManager
from app.automation.meshy_worker import REQUIRED_CREDITS
from app.core.account_manager import AccountManager
from app.core.database import Database
from app.core.pipeline import acquire_runner_lock
from app.logs import setup_logging
from app.paths import app_root
from app.security.credentials import KeyringCredentialStore
from app.services import build_mail_manager, build_pipeline
from app.settings import Settings
from app.ui.library_page import LibraryPage
from app.ui.logs_page import LogsPage
from app.ui.settings_page import SettingsPage
from app.ui.stall_watch import StallWatch
from app.ui.theme import STYLE, status_color

THUMB = 64
RUNNING = ("Generating", "Uploading", "Checking Account", "Downloading", "Cancel Requested")
TERMINAL = ("Completed", "Failed", "Canceled")


def _parse_utc(text: str | None) -> float | None:
    try:
        return time.mktime(time.strptime(text, "%Y-%m-%d %H:%M:%S")) - time.timezone if text else None
    except (TypeError, ValueError):
        return None


def _duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:d}:{seconds % 60:02d}" if seconds < 3600 else f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


class MeshyMainWindow(QMainWindow):
    bootstrap_done = Signal(bool, str)
    _bg_done = Signal(object, object)

    def __init__(self, project_root: str | Path | None = None):
        super().__init__()
        root = Path(project_root or app_root())
        self.setWindowTitle("Meshy AI Studio")
        self.resize(1180, 760)
        self.setMinimumSize(980, 620)
        self.setAcceptDrops(True)
        self.root = self._root = root
        self._owns_runner = False
        setup_logging(root)
        self.settings = Settings(root)
        self.browser_manager = BrowserManager(root / "profiles")
        self.database = Database(root / "data" / "meshy.sqlite3")
        credentials = KeyringCredentialStore()
        self.account_manager = AccountManager(self.database, credentials, root / "profiles")
        try:
            bootstrap.import_bundled_accounts(root, self.account_manager)
        except Exception as error:  # a broken accounts.txt must not stop the app
            print(f"accounts.txt import failed: {type(error).__name__}")
        self.mail = build_mail_manager(self.database, self.settings, credentials)
        self.pipeline = build_pipeline(self.database, self.browser_manager, self.settings, credentials)
        self.meshy_worker = self.pipeline.worker
        self._bg_done.connect(lambda done, result: done(*result))
        self._thumbs: dict[str, QIcon] = {}
        self._build_ui()
        self._refresh_accounts()
        self._refresh_jobs()
        self.bootstrap_done.connect(self._on_bootstrap_done)
        if os.environ.get("MESHY_AUTOSTART", "1") != "0":
            self.status.setText("Preparing decoder and browser (first start only)...")
            threading.Thread(target=self._bootstrap, args=(root,), daemon=True).start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_accounts)
        self._timer.timeout.connect(self._refresh_jobs)
        self._timer.timeout.connect(self._refresh_logs)
        self._timer.start(3000)

    # ---- layout ------------------------------------------------------------------------------------------------------
    def _build_ui(self) -> None:
        root_widget = QWidget(self)
        root_widget.setObjectName("root")
        outer = QHBoxLayout(root_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

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
        stop_button.setToolTip("Stops sending jobs, cancels running local work at its next step, pauses the queue and closes the "
                               "browsers. Jobs already submitted to Meshy keep running on their servers.")
        stop_button.clicked.connect(self._emergency_stop)
        resume_button = QPushButton("Resume queue")
        resume_button.setObjectName("secondary")
        resume_button.clicked.connect(self._resume_queue)
        side.addWidget(stop_button)
        side.addWidget(resume_button)
        outer.addWidget(sidebar)

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
        layouts = []
        for _ in self.page_names:
            page = QWidget()
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
        self.library_page = LibraryPage(self.database)
        layouts[4].addWidget(self.library_page)
        self.settings_page = SettingsPage(self.root, self.settings, self.pipeline, self.mail, self.database,
                                          choose_export=self._choose_export_dir,
                                          runner_label=lambda: "this window" if self._owns_runner else "another process")
        layouts[5].addWidget(self.settings_page)
        self.logs_page = LogsPage(self.root)
        self.log_view = self.logs_page.view
        layouts[6].addWidget(self.logs_page)
        self.navigation.currentRowChanged.connect(self._on_page_changed)
        self.navigation.itemSelectionChanged.connect(self._on_nav_selected)  # also reacts to accessibility / UI Automation selection
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

    @staticmethod
    def _style_table(table: QTableWidget, row_height: int = 40) -> None:
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    # ---- Generate ----------------------------------------------------------------------------------------------------
    def _build_generate_page(self, page_layout: QVBoxLayout) -> None:
        self.image_label = QPushButton("Drop images here, or click to choose\nPNG / JPG / WEBP, up to 20 MB each")
        self.image_label.setObjectName("dropzone")
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.setMinimumHeight(150)
        self.image_label.setToolTip("Every image you drop or choose is queued immediately")
        self.image_label.clicked.connect(self._choose_image)
        page_layout.addWidget(self.image_label)
        self.reject_label = QLabel("")
        self.reject_label.setObjectName("alert")
        self.reject_label.setWordWrap(True)
        page_layout.addWidget(self.reject_label)
        self.recent = QListWidget()
        self.recent.setViewMode(QListView.ViewMode.IconMode)
        self.recent.setFlow(QListView.Flow.LeftToRight)
        self.recent.setWrapping(False)
        self.recent.setMovement(QListView.Movement.Static)
        self.recent.setIconSize(QSize(72, 72))
        self.recent.setGridSize(QSize(100, 104))
        self.recent.setFixedHeight(128)
        self.recent.setToolTip("Images you queued recently (see the Queue page for progress)")
        page_layout.addWidget(self.recent)
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
        hint = QLabel("Each model gets its own sub-folder with the GLB, the FBX and textures/*.png. The folder is remembered.")
        hint.setObjectName("muted")
        inner.addWidget(hint)
        page_layout.addWidget(card)
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Optional note saved with the next jobs")
        page_layout.addWidget(self.prompt_input)
        page_layout.addStretch(1)
        self._refresh_export_label()

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
        if hasattr(os, "startfile"):
            os.startfile(str(folder))

    @Slot()
    def _choose_image(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose input images", "", "Images (*.png *.jpg *.jpeg *.webp)")
        self.enqueue_many(paths)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.enqueue_many(paths)
            event.acceptProposedAction()

    def enqueue_many(self, paths: list[str]) -> tuple[int, list[str]]:
        """Queue every valid image at once; rejected files are listed with the reason."""
        queued, rejected = 0, []
        for path in paths:
            ok, message = self._enqueue(path)
            queued += ok
            if not ok:
                rejected.append(message)
        if paths:
            self.image_label.setText(f"Queued {queued} image(s)\nDrop or click to add more")
        self.reject_label.setText("Not queued: " + "; ".join(rejected) if rejected else "")
        return queued, rejected

    def _enqueue(self, path: str) -> tuple[bool, str]:
        try:
            job_id = self.pipeline.enqueue(path, self.prompt_input.text())
        except ValueError as error:
            self.status.setText(f"Rejected: {error}")
            return False, str(error)
        item = QListWidgetItem(self._thumbnail(path, 72), Path(path).name[:14])
        item.setToolTip(path)
        self.recent.insertItem(0, item)
        while self.recent.count() > 12:
            self.recent.takeItem(self.recent.count() - 1)
        self.status.setText(f"Job {job_id} queued - runs automatically" if self._owns_runner
                            else f"Job {job_id} queued - another runner process will pick it up")
        self._refresh_jobs()
        return True, ""

    # ---- Queue -------------------------------------------------------------------------------------------------------
    def _build_queue_page(self, page_layout: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.addWidget(self._button("Cancel selected", self._cancel_selected,
                                   tip="Select one or more jobs (Ctrl/Shift). Queued jobs behind them move up. A job already "
                                       "submitted to Meshy is only stopped locally; its remote task keeps running."))
        bar.addWidget(self._button("Pause selected", self._pause_selected, secondary=True))
        bar.addWidget(self._button("Resume selected", self._resume_selected, secondary=True))
        bar.addWidget(self._button("Retry selected", self._retry_selected, secondary=True))
        bar.addStretch(1)
        page_layout.addLayout(bar)
        self.jobs_table = QTableWidget(0, 8)
        self.jobs_table.setHorizontalHeaderLabels(["Preview", "Job", "Image", "Status", "Progress", "Account", "Time", "Note / error"])
        self._style_table(self.jobs_table, THUMB + 12)
        self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.jobs_table.setIconSize(QSize(THUMB, THUMB))
        for column, width in enumerate((THUMB + 24, 50, 170, 110, 80, 200, 70)):
            self.jobs_table.setColumnWidth(column, width)
        page_layout.addWidget(self.jobs_table, 1)

    def _thumbnail(self, image_path: str, size: int = THUMB) -> QIcon:
        key = f"{size}:{image_path}"
        icon = self._thumbs.get(key)
        if icon is None:
            pixmap = QPixmap(image_path)
            icon = QIcon(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)) if not pixmap.isNull() else QIcon()
            self._thumbs[key] = icon
        return icon

    def _selected_job_ids(self) -> list[int]:
        rows = {index.row() for index in self.jobs_table.selectedIndexes()}
        ids = [int(self.jobs_table.item(row, 1).text()) for row in rows if self.jobs_table.item(row, 1) is not None]
        return sorted(ids)  # act on jobs in their original order

    @Slot()
    def _refresh_jobs(self) -> None:
        keep = set(self._selected_job_ids())
        jobs = self.database.list_jobs()[:200]
        positions = {job.id: self.database.queue_position(job.id) for job in jobs}
        # running first, then the queue in run order, then everything else (paused/finished, newest first)
        jobs.sort(key=lambda j: (0, 0, j.id) if j.status in RUNNING
                  else (1, positions[j.id], j.id) if positions[j.id] else (2, 0, -j.id))
        emails = {a.id: a.email for a in self.database.list_accounts()}
        now = time.time()
        self.jobs_table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            position = positions[job.id]
            status = f"Queued #{position}" if position else job.status
            progress = f"{job.progress}%" if job.status in RUNNING or job.status == "Completed" else ""
            started, finished = _parse_utc(job.started_at), _parse_utc(job.finished_at)
            elapsed = _duration((finished or now) - started) if started and (job.status in RUNNING or finished) else ""
            preview = QTableWidgetItem()
            preview.setIcon(self._thumbnail(job.image_path))
            self.jobs_table.setItem(row, 0, preview)
            values = (str(job.id), Path(job.image_path).name, status, progress, emails.get(job.account_id, ""), elapsed,
                      job.error or job.note)
            for col, value in enumerate(values, start=1):
                item = QTableWidgetItem(value)
                if col == 3:
                    item.setForeground(QColor(status_color(value)))
                self.jobs_table.setItem(row, col, item)
        running = sum(1 for j in jobs if j.status in RUNNING)
        queued = sum(1 for j in jobs if positions[j.id])
        paused = sum(1 for j in jobs if j.status == "Paused")
        self.summary.setText(f"{running} running  |  {queued} queued" + (f"  |  {paused} paused" if paused else ""))
        mode = self.jobs_table.selectionMode()
        self.jobs_table.clearSelection()
        self.jobs_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for row in range(self.jobs_table.rowCount()):
            if int(self.jobs_table.item(row, 1).text()) in keep:
                self.jobs_table.selectRow(row)
        self.jobs_table.setSelectionMode(mode)

    def _need_selection(self) -> list[int]:
        ids = self._selected_job_ids()
        if not ids:
            self.status.setText("Select one or more jobs in the queue first")
        return ids

    @Slot()
    def _cancel_selected(self) -> None:
        ids = self._need_selection()
        if not ids:
            return
        outcome = self.pipeline.cancel_jobs(ids)
        self.status.setText(f"Canceled {len(outcome['canceled'])} queued job(s); {len(outcome['stopping'])} running job(s) will stop "
                            "at the next step (local only - Meshy keeps any task it already started)")
        self._refresh_jobs()

    @Slot()
    def _pause_selected(self) -> None:
        ids = self._need_selection()
        if ids:
            self.status.setText(f"Paused {self.pipeline.pause_jobs(ids)} queued job(s)")
            self._refresh_jobs()

    @Slot()
    def _resume_selected(self) -> None:
        ids = self._need_selection()
        if ids:
            self.status.setText(f"Resumed {self.pipeline.resume_jobs(ids)} paused job(s)")
            self._refresh_jobs()

    def _confirm(self, text: str) -> bool:
        return QMessageBox.question(self, "Please confirm", text) == QMessageBox.StandardButton.Yes

    @Slot()
    def _retry_selected(self) -> None:
        ids = self._need_selection()
        if not ids:
            return
        submitted = [i for i in ids if self.database.get_job(i).submitted]
        if submitted and not self._confirm(
                f"{len(submitted)} of these job(s) were already submitted to Meshy. Retrying creates a NEW generation and may spend "
                "credits again.\n\nRetry anyway?"):
            ids = [i for i in ids if i not in submitted]
        count = self.database.requeue_jobs(ids)
        self.status.setText(f"Re-queued {count} job(s)")
        self._refresh_jobs()

    @Slot()
    def _resume_queue(self) -> None:
        if self._owns_runner:
            self.pipeline.resume_queue()
        else:
            self.database.resume_paused_jobs()
        self.status.setText("Queue resumed")
        self._refresh_jobs()

    @Slot()
    def _emergency_stop(self) -> None:
        self.pipeline.emergency_stop()
        self.pipeline.release_all_browsers()
        self.status.setText("EMERGENCY STOP: nothing new is sent, running jobs stop at their next step, queue paused, browsers closed "
                            "(Meshy tasks already submitted keep running on the server)")
        self._refresh_jobs()

    # ---- Accounts ----------------------------------------------------------------------------------------------------
    def _build_accounts_page(self, page_layout: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.addWidget(self._button("Use selected account", self._pin_selected_account,
                                   tip="Run all jobs on this account (overrides its rest period); paused jobs continue"))
        bar.addWidget(self._button("Automatic rotation", self._auto_rotation, secondary=True))
        bar.addWidget(self._button("Import list (.txt)", self._import_accounts, secondary=True))
        bar.addWidget(self._button("Refresh", self._refresh_accounts, secondary=True))
        bar.addStretch(1)
        page_layout.addLayout(bar)
        self.accounts_table = QTableWidget(0, 6)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Status", "Credit", "Checked (UTC)", "Session", "Active jobs"])
        self._style_table(self.accounts_table)
        self.accounts_table.setSortingEnabled(True)
        for column, width in enumerate((240, 270, 90, 150, 110)):
            self.accounts_table.setColumnWidth(column, width)
        page_layout.addWidget(self.accounts_table, 1)
        note = QLabel(f"A model needs {REQUIRED_CREDITS} credits. 'unknown' means the balance has not been read yet (it is never "
                      "treated as 0). Accounts below the need rest automatically; jobs pause when none is left. "
                      "The app never creates Meshy accounts.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        page_layout.addWidget(note)

    @Slot()
    def _refresh_accounts(self) -> None:
        if not hasattr(self, "accounts_table"):
            return
        accounts = self.database.list_accounts()
        low = [a for a in accounts if a.credit_balance is not None and a.credit_balance < REQUIRED_CREDITS
               and a.status.lower() != "quota limited"]
        self.alert.setText(f"{len(low)} account(s) low on credits" if low else "")
        selected = self._selected_account()
        self.accounts_table.setSortingEnabled(False)  # sorting while filling moves rows under the loop
        self.accounts_table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            status = f"{account.status} (until {account.cooldown_until} UTC)" if account.cooldown_until else account.status
            if account.credit_balance is None:
                credit, credit_color = "unknown", "#9d96b4"
            elif account.credit_balance < REQUIRED_CREDITS:
                credit, credit_color = f"{account.credit_balance} (low)", "#ff6b6b"
            else:
                credit, credit_color = str(account.credit_balance), "#4cc38a"
            pinned = " [selected]" if account.id == self.pipeline.manual_account_id else ""
            values = [account.email + pinned, status, credit, account.credit_checked_at or "never",
                      "Valid" if account.session_valid else "Not connected", str(account.active_jobs)]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2:
                    item.setForeground(QColor(credit_color))
                if col == 1 and account.status.lower() in ("quota limited", "needs verification", "invalid credentials", "login failed"):
                    item.setForeground(QColor("#ffb347"))
                self.accounts_table.setItem(row, col, item)
        self.accounts_table.setSortingEnabled(True)
        if selected is not None:
            for row in range(self.accounts_table.rowCount()):
                if self.accounts_table.item(row, 0).text().replace(" [selected]", "") == selected.email:
                    self.accounts_table.selectRow(row)

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

    @Slot()
    def _import_accounts(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import account list", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return
        result = self.account_manager.import_file(path)
        self._refresh_accounts()
        self.status.setText(f"Imported {result.imported} accounts | duplicates {result.duplicates} | invalid {result.invalid}")

    # ---- Purelymail --------------------------------------------------------------------------------------------------
    def _background(self, work, done) -> None:
        def run() -> None:
            try:
                outcome = (work(), None)
            except Exception as error:
                outcome = (None, error)
            self._bg_done.emit(done, outcome)
        threading.Thread(target=run, daemon=True).start()

    def _build_mail_page(self, page_layout: QVBoxLayout) -> None:
        self.mail_note = QLabel()
        self.mail_note.setWordWrap(True)
        self.mail_note.setObjectName("muted")
        page_layout.addWidget(self.mail_note)
        token_row = QHBoxLayout()
        self.mail_token = QLineEdit()
        self.mail_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.mail_token.setPlaceholderText("Purelymail API token (stored in the Windows credential store, never shown again)")
        token_row.addWidget(self.mail_token, 1)
        token_row.addWidget(self._button("Save token", self._save_mail_token))
        page_layout.addLayout(token_row)
        self.mail_table = QTableWidget(0, 4)
        self.mail_table.setHorizontalHeaderLabels(["Mailbox", "Status", "Expires", "Last checked"])
        self._style_table(self.mail_table)
        for column, width in enumerate((300, 130, 220)):
            self.mail_table.setColumnWidth(column, width)
        page_layout.addWidget(self.mail_table, 1)
        row = QHBoxLayout()
        row.addWidget(self._button("Add mailbox...", self._add_mailbox))
        self.sync_button = self._button("Sync from API", self._sync_mailboxes, secondary=True)
        row.addWidget(self.sync_button)
        row.addWidget(self._button("Check login", self._check_mailbox, secondary=True))
        row.addWidget(self._button("Read mail / OTP", self._read_mailbox, secondary=True))
        row.addStretch(1)
        page_layout.addLayout(row)
        self.mail_view = QPlainTextEdit()
        self.mail_view.setReadOnly(True)
        page_layout.addWidget(self.mail_view)
        enabled = self.mail.api_enabled()
        self.sync_button.setEnabled(enabled)
        self.sync_button.setToolTip("" if enabled else "Disabled: no verified management-API configuration (see Settings).")
        self.mail_note.setText(
            "Existing mailboxes only; the API token and mailbox passwords stay in the Windows credential store. Reading mail uses "
            "IMAP (imap.purelymail.com:993). " + ("Management API: enabled with your configuration." if enabled else
                                                  "Management API calls are DISABLED: no official endpoint information is configured, "
                                                  "and none is guessed."))
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
                self.status.setText(f"{address}: {status if not error else type(error).__name__}"), self._refresh_mailboxes()))
        else:
            self.status.setText("Select one mailbox first")

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

    # ---- navigation / pages ------------------------------------------------------------------------------------------
    @Slot()
    def _on_nav_selected(self) -> None:
        items = self.navigation.selectedItems()
        if items and self.navigation.row(items[0]) != self.pages.currentIndex():
            self.navigation.setCurrentRow(self.navigation.row(items[0]))

    @Slot(int)
    def _on_page_changed(self, row: int) -> None:
        self.pages.setCurrentIndex(row)
        self.page_title.setText(self.page_names[row])
        name = self.page_names[row]
        if name == "Library":
            self.library_page.refresh()
        elif name == "Settings":
            self.settings_page.load()
        elif name == "Logs":
            self.logs_page.refresh()

    @Slot()
    def _refresh_logs(self) -> None:
        if self.pages.currentIndex() == self.page_names.index("Logs"):
            self.logs_page.refresh()

    # ---- startup / shutdown ------------------------------------------------------------------------------------------
    def _bootstrap(self, root: Path) -> None:
        messages: list[str] = []
        ok = bootstrap.prepare(root, messages.append)
        self.bootstrap_done.emit(ok, messages[-1] if messages else "")

    @Slot(bool, str)
    def _on_bootstrap_done(self, ok: bool, message: str) -> None:
        if not ok:
            self.status.setText(f"Setup incomplete: {message}")
        self._start_pipeline(self.root)

    def _start_pipeline(self, root: Path) -> None:
        if acquire_runner_lock(root / "data" / "runner.lock"):
            self._owns_runner = True
            self.pipeline.start_background()
            image = os.environ.get("MESHY_INPUT_IMAGE")
            if image:
                self._enqueue(image)
        else:
            self.status.setText("A headless runner is active; this window only queues jobs")

    def closeEvent(self, event) -> None:
        """Closing the window stops the local queue; unfinished jobs are restored on the next start (never re-submitted)."""
        self._timer.stop()
        self.pipeline.stop()
        super().closeEvent(event)


def create_app(argv: list[str] | None = None) -> tuple[QApplication, MeshyMainWindow]:
    app = QApplication(argv or sys.argv)
    app.setStyleSheet(STYLE)
    window = MeshyMainWindow()
    window.stall_watch = StallWatch(parent=window)
    return app, window


def main() -> int:
    app, window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
