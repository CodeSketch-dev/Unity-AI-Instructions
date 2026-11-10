from __future__ import annotations

import sys
import os
from pathlib import Path

import threading

from PySide6.QtCore import QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import QHBoxLayout, QApplication, QLabel, QListWidget, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit

from app.paths import app_root
from app.settings import Settings
from app import bootstrap
from app.automation.browser_manager import BrowserManager
from app.automation.google_login import GoogleOAuthLogin
from app.automation.meshy_worker import MeshyWebWorker
from app.security.credentials import KeyringCredentialStore
from app.ui.browser_host import BrowserHostWidget
from app.core.database import Database
from app.core.account_manager import AccountManager
from app.core.pipeline import PipelineService, acquire_runner_lock


class MeshyMainWindow(QMainWindow):
    bootstrap_done = Signal(bool, str)

    def __init__(self, project_root: str | Path | None = None):
        super().__init__()
        root = Path(project_root or app_root())
        self.setWindowTitle("Meshy AI Studio")
        self.resize(1100, 720)
        self.setAcceptDrops(True)
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
        self._timer.start(5000)

    def _build_ui(self) -> None:
        shell = QWidget(self)
        layout = QVBoxLayout(shell)
        title = QLabel("Meshy AI Studio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        self.navigation = QListWidget()
        self.navigation.addItems(["AI 3D Chat", "Accounts", "Generation Queue", "Model Library", "Settings", "Logs"])
        self.navigation.setCurrentRow(0)
        layout.addWidget(self.navigation)

        self.pages = QStackedWidget()
        for name in ("AI 3D Chat", "Accounts", "Generation Queue", "Model Library", "Settings", "Logs"):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.addWidget(QLabel(name))
            self.pages.addWidget(page)
        self.pages.widget(0).layout().addWidget(self.browser_host)
        chat = self.pages.widget(0)
        chat_layout = chat.layout()
        self.image_label = QLabel("Drop an image here or choose a file")
        self.image_label.setMinimumHeight(48)
        self.image_label.setStyleSheet("border: 1px dashed #8b6de0; padding: 12px; color: #cfc5f5;")
        chat_layout.insertWidget(0, self.image_label)
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Optional prompt for the 3D model")
        chat_layout.insertWidget(1, self.prompt_input)
        choose = QPushButton("Choose image")
        choose.clicked.connect(self._choose_image)
        chat_layout.insertWidget(2, choose)
        generate = QPushButton("Generate 3D")
        generate.clicked.connect(self._generate_from_ui)
        chat_layout.insertWidget(3, generate)
        self.export_label = QLabel()
        self.export_label.setWordWrap(True)
        self.export_label.setObjectName("exportLabel")
        choose_export = QPushButton("Choose export folder...")
        choose_export.clicked.connect(self._choose_export_dir)
        open_export = QPushButton("Open")
        open_export.clicked.connect(self._open_export_dir)
        export_row = QHBoxLayout()
        export_row.addWidget(self.export_label, 1)
        export_row.addWidget(choose_export)
        export_row.addWidget(open_export)
        chat_layout.insertLayout(0, export_row)
        self._refresh_export_label()
        accounts_page = self.pages.widget(1)
        accounts_layout = accounts_page.layout()
        accounts_layout.addWidget(QLabel("Account pool — tự chọn account còn session và credit"))
        self.accounts_table = QTableWidget(0, 5)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Status", "Credit", "Session", "Active jobs"])
        self.accounts_table.setSortingEnabled(True)
        accounts_layout.addWidget(self.accounts_table)
        refresh = QPushButton("Refresh accounts")
        refresh.clicked.connect(self._refresh_accounts)
        accounts_layout.addWidget(refresh)
        import_button = QPushButton("Import account list (.txt)")
        import_button.clicked.connect(self._import_accounts)
        accounts_layout.addWidget(import_button)
        queue_layout = self.pages.widget(2).layout()
        self.jobs_table = QTableWidget(0, 4)
        self.jobs_table.setHorizontalHeaderLabels(["Job", "Image", "Status", "Note / error"])
        queue_layout.addWidget(self.jobs_table)
        layout.addWidget(self.pages)

        self.status = QLabel("Ready — no credentials loaded")
        layout.addWidget(self.status)
        open_button = QPushButton("Open Meshy sign-in profile")
        open_button.clicked.connect(self.open_meshy_profile)
        layout.addWidget(open_button)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.setCentralWidget(shell)

    def open_meshy_profile(self) -> None:
        if not self.browser_host.hosted:
            self.browser_host.start(self._first_account_id())
        self.status.setText("Meshy profile opened — complete Google sign-in manually if requested")

    def _refresh_export_label(self) -> None:
        self.export_label.setText(f"Export folder: {self.settings.export_dir}  (each model gets its own sub-folder: GLB, textures/*.png, FBX)")

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
        path, _ = QFileDialog.getOpenFileName(self, "Choose input image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self._selected_image = path
            self.image_label.setText(f"Selected: {Path(path).name}")

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        accepted = False
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                self._selected_image = path
                self.image_label.setText(f"Queued: {Path(path).name}")
                self._enqueue(path)
                accepted = True
        if accepted:
            event.acceptProposedAction()

    @Slot()
    def _generate_from_ui(self) -> None:
        path = getattr(self, "_selected_image", None)
        if not path:
            self.status.setText("Choose or drop an input image first")
            return
        self._enqueue(path)

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

    @Slot()
    def _refresh_jobs(self) -> None:
        jobs = self.database.list_jobs()[:200]
        self.jobs_table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            for col, value in enumerate((str(job.id), Path(job.image_path).name, job.status, job.error or job.note)):
                self.jobs_table.setItem(row, col, QTableWidgetItem(value))

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
        self.accounts_table.setRowCount(len(accounts))
        for row, account in enumerate(accounts):
            status = f"{account.status} (until {account.cooldown_until} UTC)" if getattr(account, "cooldown_until", None) else account.status
            values = [account.email, status, "Unknown", "Valid" if account.session_valid else "Not connected", str(account.active_jobs)]
            for col, value in enumerate(values):
                self.accounts_table.setItem(row, col, QTableWidgetItem(value))

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
    app.setStyleSheet("QMainWindow { background: #15131d; color: #f7f4ff; } QLabel#title { font-size: 26px; font-weight: 700; padding: 12px; } QListWidget, QStackedWidget { background: #211d2b; color: #f7f4ff; border: 1px solid #3a3150; padding: 8px; } QPushButton { background: #8055d6; color: white; padding: 10px; border-radius: 8px; }")
    window = MeshyMainWindow()
    return app, window


def main() -> int:
    app, window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
