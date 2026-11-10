from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.automation.meshy_export import MeshyExporter
from app.automation.model_export import job_folder, package_model, safe_name
from app.paths import app_root
from app.automation.meshy_adapter import MeshyLoginState, MeshyWebAdapter, _advance_onboarding, dismiss_onboarding
from app.automation.google_login import GoogleLoginOutcome, GoogleOAuthLogin
from app.security.redaction import redact


REQUIRED_CREDITS = 30  # Generate 20 + Texture 10 (remesh is free)


class WorkerState(StrEnum):
    IDLE = "idle"
    WAITING_FOR_LOGIN = "waiting_for_login"
    UPLOADING = "uploading"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    QUOTA_LIMITED = "quota_limited"
    MANUAL_VERIFICATION = "manual_verification"
    INVALID_CREDENTIALS = "invalid_credentials"
    CANCELED = "canceled"


@dataclass(slots=True)
class WorkerResult:
    state: WorkerState
    account_id: int
    message: str = ""
    result_path: str | None = None


class MeshyWebWorker:
    """Sequential web worker. It intentionally never accepts credentials or closes contexts."""

    def __init__(self, browser_manager: Any, adapter: MeshyWebAdapter | None = None, google_login: GoogleOAuthLogin | None = None,
                 *, export_dir: Any = None, exporter: MeshyExporter | None = None, packager: Any = None):
        self.browser_manager = browser_manager
        self.adapter = adapter or MeshyWebAdapter(browser_manager)
        self.google_login = google_login
        # a folder, or a callable returning the folder (read per job so the GUI can change it live)
        self.export_dir = export_dir if callable(export_dir) or export_dir is None else Path(export_dir)
        self.packager = packager or (lambda glb: package_model(glb, app_root()))
        self.exporter = exporter or MeshyExporter()
        self._contexts: dict[int, tuple[Any, Any]] = {}
        self._active_account: int | None = None
        self.cancel_event = threading.Event()
        self.on_credits: Any = None  # callback(account_id, balance)
        self.on_submitted: Any = None  # callback(account_id): Generate was clicked, a paid remote task may exist
        self.on_progress: Any = None  # callback(percent)
        self.deadline: float | None = None  # time.monotonic() limit for the whole job
        self.cancel_probe: Any = None
        self.required_credits = REQUIRED_CREDITS

    def context_for(self, account_id: int) -> tuple[Any, Any]:
        if account_id not in self._contexts:
            self._contexts[account_id] = self.adapter.open_profile(account_id, headless=False)
        return self._contexts[account_id]

    def run_one(self, account_id: int, image_path: str | Path, *, account_key: str | None = None, wait_for_login_ms: int = 120_000) -> WorkerResult:
        result = self._run_one(account_id, image_path, account_key=account_key, wait_for_login_ms=wait_for_login_ms)
        if result.state == WorkerState.FAILED:
            self._snapshot(account_id)
        return result

    def _snapshot(self, account_id: int) -> None:
        """Save a screenshot of the failed page so the cause can be seen, not guessed."""
        try:
            _, context = self._contexts[account_id]
            page = next(p for p in context.pages if "meshy.ai" in str(p.url))
            folder = (self.export_dir.parent if self.export_dir else Path.cwd()) / "output" / "diagnostics"
            folder.mkdir(parents=True, exist_ok=True)
            import time
            page.screenshot(path=str(folder / f"{time.strftime('%Y%m%d_%H%M%S')}_acc{account_id}.png"))
        except Exception:
            pass

    def _run_one(self, account_id: int, image_path: str | Path, *, account_key: str | None = None, wait_for_login_ms: int = 120_000) -> WorkerResult:
        if self._active_account is not None:
            raise RuntimeError("A Meshy job is already running; queue is sequential")
        self._active_account = account_id
        try:
            _, context = self.context_for(account_id)
            page = context.pages[0] if context.pages else context.new_page()
            login_state = self.adapter.classify_login_state(page)
            # The page may still be rendering; wait for a definite signed-in/out state.
            for _ in range(40):
                if login_state != MeshyLoginState.UNKNOWN:
                    break
                page.wait_for_timeout(500)
                login_state = self.adapter.classify_login_state(page)
            if login_state == MeshyLoginState.MANUAL_VERIFICATION:
                return WorkerResult(WorkerState.MANUAL_VERIFICATION, account_id, "Manual verification required")
            if login_state == MeshyLoginState.LOGIN_REQUIRED:
                self.adapter.start_manual_google_login(page)
                if self.google_login and account_key:
                    oauth_page = _new_oauth_page(context, page)
                    if oauth_page is not None:
                        outcome = self.google_login.attempt(oauth_page, account_key)
                        if outcome == GoogleLoginOutcome.MANUAL_VERIFICATION:
                            return WorkerResult(WorkerState.MANUAL_VERIFICATION, account_id, "Google MFA/CAPTCHA/device verification requires the user")
                        if outcome == GoogleLoginOutcome.INVALID_CREDENTIALS:
                            return WorkerResult(WorkerState.INVALID_CREDENTIALS, account_id, "Google credentials were rejected")
                        if outcome == GoogleLoginOutcome.CREDENTIALS_UNAVAILABLE:
                            return WorkerResult(WorkerState.WAITING_FOR_LOGIN, account_id, "Google credentials are unavailable in CredentialStore")
                login_state = self.adapter.wait_for_authenticated(page, timeout_ms=wait_for_login_ms)
                if login_state == MeshyLoginState.MANUAL_VERIFICATION:
                    return WorkerResult(WorkerState.MANUAL_VERIFICATION, account_id, "Google MFA/CAPTCHA/device verification requires the user")
                if login_state != MeshyLoginState.AUTHENTICATED:
                    return WorkerResult(WorkerState.WAITING_FOR_LOGIN, account_id, "Google sign-in did not complete before timeout")
            if login_state != MeshyLoginState.AUTHENTICATED:
                return WorkerResult(WorkerState.FAILED, account_id, "Meshy authentication state is unknown")

            if (stop := self._canceled(account_id)):
                return stop
            self.close_stray_tabs(context, page)
            dismiss_onboarding(page)
            read_credits = getattr(self.adapter, "read_credits", None)
            balance = read_credits(page) if read_credits is not None else None
            if balance is not None:
                if callable(self.on_credits):
                    self.on_credits(account_id, balance)
                if balance < self.required_credits:
                    return WorkerResult(WorkerState.QUOTA_LIMITED, account_id,
                                        f"Only {balance} credits left (a model needs {self.required_credits})")
            self.adapter.open_model_tab(page)
            dismiss_onboarding(page)
            self.adapter.upload_image(page, image_path)
            if not _has_uploaded_preview(page):
                return WorkerResult(WorkerState.FAILED, account_id, "Upload preview was not visible")
            self._progress(10)
            dismiss_onboarding(page, 10)  # a product tour can start right after the upload
            generate = _generate_button(page)
            if not generate.is_visible() or not generate.is_enabled():
                return WorkerResult(WorkerState.FAILED, account_id, "Generate button was not enabled")
            count_cards = getattr(self.adapter, "count_cards", None)
            cards_before = count_cards(page) if count_cards is not None else 0
            try:
                generate.click(timeout=8000)
            except Exception:
                if self._poll_visible_status(page) == WorkerState.QUOTA_LIMITED:
                    _dismiss_modal(page)
                    return WorkerResult(WorkerState.QUOTA_LIMITED, account_id, "Account has no credits left")
                raise
            # From here a paid remote task may exist: the pipeline must never submit this job again by itself.
            if callable(self.on_submitted):
                self.on_submitted(account_id)
            self._progress(20)
            wait_new_early = getattr(self.adapter, "wait_for_new_asset", None)
            if wait_new_early is not None and not wait_new_early(page, cards_before, 20_000):
                if self._poll_visible_status(page) == WorkerState.QUOTA_LIMITED:
                    _dismiss_modal(page)
                    return WorkerResult(WorkerState.QUOTA_LIMITED, account_id, "Account has no credits left")
                generate = _generate_button(page)  # first click did not start a job; try once more
                if generate.is_visible() and generate.is_enabled():
                    generate.click(timeout=8000)
            # Meshy may show the daily check-in reward immediately after a job
            # starts; claim/dismiss it without interrupting the generation.
            _advance_onboarding(page)
            page.wait_for_timeout(1500)
            if self._poll_visible_status(page) == WorkerState.QUOTA_LIMITED:
                return WorkerResult(WorkerState.QUOTA_LIMITED, account_id, "Account has no credits left")
            wait_new = getattr(self.adapter, "wait_for_new_asset", None)
            if wait_new is not None and not wait_new(page, cards_before):
                if self._poll_visible_status(page) == WorkerState.QUOTA_LIMITED:
                    return WorkerResult(WorkerState.QUOTA_LIMITED, account_id, "Account has no credits left")
                return WorkerResult(WorkerState.FAILED, account_id, "No new model appeared after Generate")
            wait_ready = getattr(self.adapter, "wait_for_cards_idle", None) or getattr(self.adapter, "wait_for_model_ready", None)
            if wait_ready is not None and not wait_ready(page):
                return WorkerResult(WorkerState.FAILED, account_id, "Model did not reach a ready viewer state")
            self._progress(45)
            self._refresh_credits(page, account_id)
            if (stop := self._canceled(account_id)):
                return stop
            idle = getattr(self.adapter, "wait_for_cards_idle", None)
            texture = getattr(self.adapter, "apply_texture", None)
            if texture is not None:
                before = count_cards(page) if count_cards is not None else 0
                if not texture(page) or (wait_new is not None and not wait_new(page, before, 60_000)):
                    return WorkerResult(WorkerState.FAILED, account_id, "Texture step could not start")
                if idle is not None:
                    idle(page)
                elif wait_ready is not None:
                    wait_ready(page)
            self._progress(65)
            if (stop := self._canceled(account_id)):
                return stop
            optimize = getattr(self.adapter, "optimize_remesh_10k", None)
            if optimize is not None:
                before = count_cards(page) if count_cards is not None else 0
                if not optimize(page) or (wait_new is not None and not wait_new(page, before, 60_000)):
                    return WorkerResult(WorkerState.FAILED, account_id, "Remesh 10K could not start")
                if idle is not None:
                    idle(page)
            self._progress(85)
            if (stop := self._canceled(account_id)):
                return stop
            if self.export_dir is not None and optimize is not None:
                base = self.export_dir() if callable(self.export_dir) else self.export_dir
                folder = job_folder(base, image_path)
                target = folder / f"{safe_name(Path(image_path).stem)}.glb"
                info = self.exporter.export_latest(context, page, target)
                self.close_stray_tabs(context, page)
                try:
                    extra = self.packager(info["path"])
                except Exception as error:  # the verified GLB is already on disk: PNG/FBX problems are warnings
                    extra = {"textures": [], "fbx": None, "warnings": [f"post-processing failed: {type(error).__name__}"]}
                self._refresh_credits(page, account_id)
                message = (f"Exported {info['triangles']} triangles, {len(extra['textures'])} PNG textures, "
                           f"FBX {'yes' if extra['fbx'] else 'no'} -> {folder}")
                if extra["warnings"]:
                    message += " | " + "; ".join(extra["warnings"])
                return WorkerResult(WorkerState.COMPLETED, account_id, message, str(info["path"]))
            return WorkerResult(WorkerState.FAILED, account_id, "No output was produced (export folder or remesh step missing)")
        except Exception as error:
            return WorkerResult(WorkerState.FAILED, account_id, f"{type(error).__name__}: {redact(error)[:300]}")
        finally:
            self._active_account = None

    def release_all(self) -> None:
        for account_id in list(self._contexts):
            try:
                self.release_account(account_id)
            except Exception:
                pass

    def request_cancel(self) -> None:
        """Stop the running job at the next step boundary (a step already clicked cannot be undone)."""
        self.cancel_event.set()

    def _canceled(self, account_id: int) -> WorkerResult | None:
        probe = self.cancel_probe
        if self.cancel_event.is_set() or (probe is not None and probe()):
            return WorkerResult(WorkerState.CANCELED, account_id, "Canceled by user")
        if self.deadline is not None and time.monotonic() > self.deadline:
            return WorkerResult(WorkerState.FAILED, account_id, "Timed out (job time limit reached)")
        return None

    def _progress(self, percent: int) -> None:
        if callable(self.on_progress):
            try:
                self.on_progress(percent)
            except Exception:
                pass

    def _refresh_credits(self, page: Any, account_id: int) -> None:
        read = getattr(self.adapter, "read_credits", None)
        balance = read(page) if read is not None else None
        if balance is not None and callable(self.on_credits):
            self.on_credits(account_id, balance)  # unreadable stays "unknown": never recorded as 0

    def release_account(self, account_id: int) -> None:
        """Close this account's whole browser window (used when rotating away from it)."""
        entry = self._contexts.pop(account_id, None)
        closer = getattr(self.browser_manager, "close_account", None)
        if closer is not None:
            closer(account_id, entry[1] if entry else None)

    @staticmethod
    def close_stray_tabs(context: Any, keep: Any) -> None:
        """Close Google OAuth popups and blank tabs; keep only the Meshy workspace page."""
        for tab in list(context.pages):
            if tab is keep:
                continue
            try:
                tab.close()
            except Exception:
                pass

    def switch_after_quota(self, account_id: int) -> tuple[Any, Any]:
        """Switching is explicit and only allowed after a confirmed quota result."""
        return self.context_for(account_id)

    @staticmethod
    def _poll_visible_status(page: Any) -> WorkerState:
        text = page.locator("body").inner_text().lower()
        dialog_text = ""
        try:
            dialog_text = " ".join(page.locator("[role='dialog']:visible").all_inner_texts()).lower()
        except Exception:
            pass
        if any(token in dialog_text or token in text for token in _QUOTA_TOKENS):
            return WorkerState.QUOTA_LIMITED
        if any(token in text for token in ("completed", "succeeded", "hoàn thành", "thành công")):
            return WorkerState.COMPLETED
        return WorkerState.GENERATING


_QUOTA_TOKENS = (
    "quota", "credit limit", "hạn mức", "không đủ tín dụng", "insufficient credit", "mua tín dụng thêm",
    "chỉ dành cho người đăng ký", "buy more credits", "không đủ cho nhiệm vụ", "nâng cấp gói của bạn",
)


def _dismiss_modal(page: Any) -> None:
    """Close an upsell/pricing modal. Never click anything that buys or upgrades."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass


def _has_uploaded_preview(page: Any) -> bool:
    try:
        return page.locator("img").count() > 0
    except Exception:
        return False


def _new_oauth_page(context: Any, workspace_page: Any, timeout_ms: int = 15_000) -> Any | None:
    """The Google popup opens a moment after the click; wait for it instead of racing."""
    waited = 0
    while True:
        pages = [page for page in context.pages if page is not workspace_page]
        google = [page for page in pages if "accounts.google.com" in str(getattr(page, "url", ""))]
        if google or (pages and waited >= timeout_ms):
            return (google or pages)[-1]
        if waited >= timeout_ms:
            return None
        workspace_page.wait_for_timeout(500)
        waited += 500


def _generate_button(page: Any) -> Any:
    """Prefer Meshy's stable test id (the visible one: both sidebar tabs have a Generate button)."""
    try:
        button = page.get_by_test_id("workspace-generate-btn")
        for index in range(button.count()):
            if button.nth(index).is_visible():
                return button.nth(index)
    except Exception:
        pass
    return page.get_by_role("button", name="Tạo ra", exact=True)
