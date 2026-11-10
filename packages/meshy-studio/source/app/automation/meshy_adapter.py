from __future__ import annotations

import re
import logging
from enum import StrEnum
from pathlib import Path
from typing import Any


LOG = logging.getLogger('meshy.adapter')


class MeshyWebError(RuntimeError):
    pass


class MeshyLoginState(StrEnum):
    AUTHENTICATED = "authenticated"
    LOGIN_REQUIRED = "login_required"
    MANUAL_VERIFICATION = "manual_verification"
    UNKNOWN = "unknown"


class MeshyWebAdapter:
    WORKSPACE_URL = "https://www.meshy.ai/vi/workspace?sidebar=image"

    def __init__(self, browser_manager: Any):
        self.browser_manager = browser_manager

    def open_profile(self, account_id: int, *, headless: bool = False) -> tuple[Any, Any]:
        return self.browser_manager.launch(account_id, headless=headless, url=self.WORKSPACE_URL)

    @staticmethod
    def classify_login_state(page: Any) -> MeshyLoginState:
        if _visible(page, "text=CAPTCHA") or _visible(page, "text=MFA") or _visible(page, "text=verification"):
            return MeshyLoginState.MANUAL_VERIFICATION
        # Guests also see the workspace; the header "Đăng nhập" may be a link, not a button.
        if _visible_role(page, "button", "Đăng nhập") or _visible_role(page, "link", "Đăng nhập"):
            return MeshyLoginState.LOGIN_REQUIRED
        if _visible_role(page, "radio", "Mô hình") or _visible(page, "text=Mô hình"):
            # Guests see the same sidebar; only a signed-in session shows the upgrade button.
            return MeshyLoginState.UNKNOWN if _lacks_account_marker(page) else MeshyLoginState.AUTHENTICATED
        return MeshyLoginState.UNKNOWN

    @staticmethod
    def open_model_tab(page: Any) -> None:
        import time
        # Stable test ids first: the tabs are icon-only and have no accessible name.
        # Poll: the workspace may still be (re)loading right after goto/login.
        try:
            tab = page.get_by_test_id("workspace-image-to-3d-tab")
            rail = page.get_by_test_id("workspace-sidebar-model-btn")
            end = time.monotonic() + 30
            while time.monotonic() < end:
                if tab.count() and tab.first.is_visible():
                    if tab.first.get_attribute("aria-selected") != "true":
                        tab.first.click(timeout=3000)
                    return
                if rail.count() and rail.first.is_visible():
                    rail.first.click(force=True, timeout=3000)
                page.wait_for_timeout(1500)
        except Exception:
            pass
        deadline = time.monotonic() + 20
        initial_model = page.get_by_role("radio", name="Mô hình", exact=True)
        try:
            initial_model.click()
        except Exception:
            rail = page.locator("[data-testid='workspace-sidebar-model-btn']")
            if rail.count() and rail.first.is_visible():
                rail.first.click(force=True, timeout=3000)
        while time.monotonic() < deadline:
            tab = page.get_by_role("tab", name="Hình ảnh thành 3D", exact=True)
            try:
                if tab.count() and tab.first.is_visible():
                    if _is_selected(tab.first) is False:
                        tab.first.click()
                    return
            except AttributeError:
                if tab.is_visible():
                    return
            model = page.get_by_role("radio", name="Mô hình", exact=True)
            try:
                model.click(timeout=1500)
            except Exception:
                rail = page.locator("[data-testid='workspace-sidebar-model-btn']")
                model_text = page.get_by_text("Mô hình", exact=True)
                try:
                    if rail.count() and rail.first.is_visible():
                        rail.first.click(force=True, timeout=1500)
                    else:
                        model_text.locator("xpath=..").click(timeout=1500)
                except Exception:
                    try:
                        model_text.click(timeout=1500, force=True)
                    except Exception:
                        pass
            try:
                page.wait_for_timeout(700)
            except Exception:
                pass
        raise MeshyWebError("Meshy Image-to-3D tab was not found")

    @staticmethod
    def start_manual_google_login(page: Any) -> None:
        login = page.get_by_role("button", name="Đăng nhập", exact=True)
        if not login.is_visible():
            login = page.get_by_role("link", name="Đăng nhập", exact=True)
        if login.is_visible():
            login.click()
        google = page.get_by_role("button", name="Tiếp tục với Google", exact=True)
        for _ in range(16):  # the sign-in modal animates in after the click
            if google.is_visible():
                google.click()
                return
            page.wait_for_timeout(500)

    @staticmethod
    def logout_account(page: Any, email: str | None = None) -> bool:
        """Log out through Meshy's profile menu before rotating accounts."""
        try:
            for selector in ("button[aria-label*='profile' i]", "button[aria-label*='account' i]", "[data-testid*='profile' i]", "[data-testid*='avatar' i]"):
                button = page.locator(selector)
                if button.count() and button.first.is_visible():
                    button.first.click(force=True, timeout=1200)
                    break
            if email:
                prefix = email.split("@", 1)[0][:12]
                owner = page.get_by_text(prefix, exact=False)
                if owner.count() and owner.first.is_visible():
                    owner.first.click(force=True, timeout=1200)
            for name in ("Đăng xuất", "Log out", "Logout"):
                item = page.get_by_text(name, exact=True)
                if item.count() and item.first.is_visible():
                    item.first.click(force=True, timeout=1500)
                    return True
        except Exception:
            pass
        return False

    @classmethod
    def wait_for_authenticated(cls, page: Any, timeout_ms: int = 120_000) -> MeshyLoginState:
        import time
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            _advance_onboarding(page)
            state = cls.classify_login_state(page)
            if state in (MeshyLoginState.AUTHENTICATED, MeshyLoginState.MANUAL_VERIFICATION):
                return state
            page.wait_for_timeout(500)
        return cls.classify_login_state(page)

    @staticmethod
    def upload_image(page: Any, image_path: str | Path) -> None:
        path = Path(image_path)
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ValueError("Meshy accepts JPG, JPEG, PNG, or WebP images")
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("Image exceeds Meshy's 20 MB limit")
        # The hidden file input in the active tab panel is the reliable path;
        # clicking the drop-zone text does not always open a file chooser.
        try:
            hidden = page.locator("[role='tabpanel'][data-state='active'] input[type='file']")
            if hidden.count():
                hidden.first.set_input_files(str(path))
                return
        except Exception:
            pass
        with page.expect_file_chooser() as chooser_info:
            page.get_by_text("Nhấp / Kéo & Thả / Dán Hình ảnh", exact=False).click()
        chooser_info.value.set_files(str(path))

    @staticmethod
    def select_generation_mode(page: Any, topology: bool) -> None:
        """Form tabs: High detail (Meshy's own dense mesh, default) or Smart Topology. Best effort for High detail."""
        label = "Smart Topology" if topology else "Chi tiết cao"
        tab = page.get_by_text(label, exact=True)
        try:
            if tab.count() and tab.first.is_visible():
                tab.first.click(force=True, timeout=3000)
                page.wait_for_timeout(500)
                return
        except Exception:
            pass
        if topology:
            raise MeshyWebError("Smart Topology tab was not found")

    @staticmethod
    def configure_topology(page: Any, polycount: int, texture_model: str = "meshy7") -> bool:
        """Smart Topology form (verified against the live page): Kết cấu (texture) ON reveals the Mô hình options, so
        pick Meshy 7 and 2K, then the polygon count. The mesh and its texture come out of ONE generation, so the
        separate texture step is not needed afterwards (returns True = already textured)."""
        MeshyWebAdapter.select_generation_mode(page, True)
        MeshyWebAdapter._set_texture_toggle(page, True)
        MeshyWebAdapter._pick_model(page, "Meshy N1" if texture_model == "n1" else "Meshy 7")
        MeshyWebAdapter._pick_model(page, "2K")
        field = MeshyWebAdapter._polygon_field(page)
        field.click(timeout=3000)
        field.fill(str(int(polycount)))
        field.press("Enter")
        field.press("Tab")
        page.wait_for_timeout(300)
        value = re.sub(r"\D", "", field.input_value() or "")
        if value != str(int(polycount)):
            raise MeshyWebError(f"Polygon count could not be set (wanted {polycount}, form shows {value or 'nothing'})")
        return True

    @staticmethod
    def _pick_model(page: Any, name: str) -> None:
        """Click the model option (segmented control) whose whole text is `name`, by DOM text so role/test-id changes do not matter.
        The form re-renders after the Smart Topology tab opens, so retry for ~10 s."""
        import time
        end = time.monotonic() + 10
        while time.monotonic() < end:
            clicked = page.evaluate(_PICK_TEXT_JS, name)
            if clicked:
                page.wait_for_timeout(400)
                return
            page.wait_for_timeout(500)
        raise MeshyWebError(f"{name} model option was not found")

    @staticmethod
    def _polygon_field(page: Any) -> Any:
        """The numeric box next to the polygon slider: found by its label, else by being the only visible all-digit text input."""
        label = page.get_by_text("Số lượng đa giác", exact=True)
        if label.count():
            field = label.first.locator("xpath=ancestor::div[.//input][1]").locator("input").last
            if field.count():
                return field
        for index in range(page.locator("input").count()):
            candidate = page.locator("input").nth(index)
            try:
                if candidate.is_visible() and re.fullmatch(r"\d{2,6}", candidate.input_value() or ""):
                    return candidate
            except Exception:
                continue
        raise MeshyWebError("Polygon count input was not found")

    @staticmethod
    def _set_texture_toggle(page: Any, on: bool) -> None:
        """The 'Kết cấu' switch (a button with role=switch): set it and verify aria-checked, or raise before anything is spent."""
        label = page.get_by_text("Kết cấu", exact=True).first
        switch = label.locator("xpath=ancestor::div[.//*[@role='switch']][1]").locator("[role='switch']").first
        for _ in range(3):
            if (switch.get_attribute("aria-checked") == "true") == on:
                page.wait_for_timeout(500)
                return
            switch.click(force=True, timeout=3000)
            page.wait_for_timeout(800)
        raise MeshyWebError("The Kết cấu (texture) switch could not be set")

    RIG_CARDS = {"humanoid": "Nhân hình", "quadruped": "Chó bốn chân", "auto": "Giàn khoan thông minh"}

    @staticmethod
    def apply_rig(page: Any, rig_type: str) -> bool:
        """Viewer toolbar -> Rig -> pick a character type -> confirm. Selectors come from screenshots, not live runs."""
        try:
            dismiss_onboarding(page, 6)
            if _busy_cards(page) or not MeshyWebAdapter.open_latest_asset(page):
                return False
            button = None
            for test_id in ("viewer-rig-btn", "viewer-rigging-btn", "viewer-auto-rig-btn", "viewer-animate-btn"):
                candidate = page.get_by_test_id(test_id)
                if candidate.count() and candidate.first.is_visible():
                    button = candidate.first
                    break
            if button is None:
                for name in ("Rig", "Áp rig", "Rigging", "Hoạt ảnh"):
                    candidate = page.get_by_role("button", name=re.compile(name, re.I))
                    if candidate.count() and candidate.first.is_visible():
                        button = candidate.first
                        break
            if button is None:
                return False
            button.click(force=True, timeout=3000)
            title = page.get_by_text("Áp rig cho mô hình", exact=False)
            title.first.wait_for(state="visible", timeout=8000)
            card = page.get_by_text(MeshyWebAdapter.RIG_CARDS.get(rig_type, "Giàn khoan thông minh"), exact=False)
            card.first.click(force=True, timeout=3000)
            page.wait_for_timeout(500)
            for name in ("Áp rig", "Xác nhận", "Bắt đầu", "Tạo ra", "Áp dụng"):
                confirm = _widest(page.get_by_role("button", name=name, exact=True))
                if confirm is not None and confirm.is_visible() and confirm.is_enabled():
                    confirm.click(force=True, timeout=3000)
                    return True
            return True  # picking a card may start rigging by itself; the caller verifies a new asset appeared
        except Exception:
            LOG.warning("rig step failed", exc_info=True)
            return False

    @staticmethod
    def optimize_remesh_10k(page: Any) -> bool:
        """Viewer toolbar -> Remesh -> fixed 10K, triangle topology -> confirm (keeps texture)."""
        try:
            dismiss_onboarding(page, 6)
            if _busy_cards(page):
                return False
            # Remesh must run on the newest card (the textured one); the viewer may still show the base mesh.
            if not MeshyWebAdapter.open_latest_asset(page):
                return False
            item = page.get_by_test_id("viewer-remesh-menu-remesh-btn")
            for _ in range(3):
                page.get_by_test_id("viewer-remesh-btn").first.click(force=True, timeout=3000)
                try:
                    item.first.wait_for(state="visible", timeout=2500)
                    break
                except Exception:
                    continue
            item.first.click(force=True, timeout=3000)
            page.get_by_test_id("remesh-texture-confirm-btn").first.wait_for(state="visible", timeout=8000)
            # Defaults are Fixed / 10K / Triangle; click them anyway inside the popup so a changed default cannot slip through.
            for label in ("Cố định", "10K", "Triangle"):
                _click_last_visible(page, label)
            page.get_by_test_id("remesh-texture-confirm-btn").first.click(force=True, timeout=3000)
            return True
        except Exception:
            LOG.warning('remesh step failed', exc_info=True)
            return False

    @staticmethod
    def apply_texture(page: Any) -> bool:
        """Open Meshy's texture tool and submit the free 2K texture pass."""
        try:
            dismiss_onboarding(page, 6)
            # After generation Meshy can leave the Image-to-3D form open. The texture toolbar exists only after selecting
            # the generated model from Assets, so explicitly reconcile to the newest existing asset before continuing.
            if not MeshyWebAdapter.open_latest_asset(page):
                return False
            title = page.get_by_text("Độ phân giải texture", exact=False)
            if not (title.count() and title.first.is_visible()):
                button = page.get_by_test_id("viewer-edit-texture-btn")
                button.first.wait_for(state="visible", timeout=30000)  # viewer may still be loading the mesh
                button.first.click(force=True, timeout=3000)
            title.first.wait_for(state="visible", timeout=10000)
            option = page.get_by_text("2K", exact=True)
            if option.count() and option.first.is_visible():
                option.first.click(force=True, timeout=1500)
            submit = _widest(page.get_by_role("button", name="Kết cấu", exact=True))
            if submit is not None and submit.is_visible() and submit.is_enabled():
                submit.click(force=True, timeout=3000)
                return True
        except Exception:
            LOG.warning('texture step failed', exc_info=True)
        return False

    @staticmethod
    def open_latest_asset(page: Any) -> bool:
        """Open Assets and select the newest card without starting or spending on any remote task."""
        try:
            assets = page.get_by_test_id("workspace-sidebar-assets-btn")
            if assets.count() and assets.first.is_visible():
                assets.first.click(force=True, timeout=3000)
            cards = page.locator("[data-testid='assets-card']")
            cards.first.wait_for(state="visible", timeout=30000)
            cards.first.click(force=True, timeout=3000)
            page.wait_for_timeout(4000)
            return True
        except Exception:
            LOG.warning("could not select the newest Meshy asset", exc_info=True)
            return False

    @staticmethod
    def read_credits(page: Any) -> int | None:
        """The credit balance shown above the upgrade button in the sidebar."""
        try:
            text = page.evaluate("""() => {
                const button = document.querySelector("[data-testid='sidebar-upgrade-btn']");
                return button && button.parentElement ? button.parentElement.innerText : '';
            }""")
            match = re.search(r"\d[\d.,]*", text or "")
            return int(re.sub(r"[.,]", "", match.group(0))) if match else None
        except Exception:
            return None

    @staticmethod
    def count_cards(page: Any) -> int:
        try:
            return page.locator("[data-testid='assets-card']").count()
        except Exception:
            return 0

    @staticmethod
    def latest_asset_id(page: Any) -> str | None:
        """Task id encoded in the newest asset preview URL; stable even when the list is capped at 10 cards."""
        try:
            source = page.locator("[data-testid='assets-card']").first.locator("img").first.get_attribute("src") or ""
            match = re.search(r"/tasks/([^/]+)/", source)
            return match.group(1) if match else None
        except Exception:
            return None

    @classmethod
    def wait_for_new_asset(cls, page: Any, before: int | str | None, timeout_ms: int = 90_000) -> bool:
        """Generate was clicked: wait until a NEW asset card appears (old cards must not count)."""
        import time
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if isinstance(before, str):
                current = cls.latest_asset_id(page)
                if current is not None and current != before:
                    return True
            elif cls.count_cards(page) > int(before or 0):
                return True
            page.wait_for_timeout(1000)
        return False

    @staticmethod
    def wait_for_cards_idle(page: Any, timeout_ms: int = 600_000) -> bool:
        """Wait until no new asset card is still processing (texture / remesh jobs)."""
        import time
        deadline = time.monotonic() + timeout_ms / 1000
        page.wait_for_timeout(3000)
        while time.monotonic() < deadline:
            _advance_onboarding(page)  # the daily check-in popup appears while a job runs
            if not _busy_cards(page):
                return True
            page.wait_for_timeout(3000)
        return False

    @staticmethod
    def wait_for_model_ready(page: Any, timeout_ms: int = 900_000) -> bool:
        """Wait for a real viewer asset before texture/remesh actions."""
        import time
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            try:
                body = page.locator("body").inner_text().lower()
                busy = re.search(r"(?<![\d.])(?:[0-9]|[1-9][0-9])%", body)
                if "đang tạo mô hình" not in body and "generating" not in body and "processing" not in body and not busy:
                    if page.locator("[data-testid='assets-card']").count() or "topology" in body:
                        return True
            except Exception:
                pass
            page.wait_for_timeout(1500)
        return False


def _visible(page: Any, selector: str) -> bool:
    try:
        locator = page.locator(selector)
        try:
            return any(locator.nth(index).is_visible() for index in range(locator.count()))
        except AttributeError:
            return locator.is_visible()
    except Exception:
        return False


def _widest(locator: Any) -> Any | None:
    """The dialog's submit button shares its label with a small toolbar toggle; take the wide one."""
    try:
        best, best_width = None, -1.0
        for index in range(locator.count()):
            item = locator.nth(index)
            box = item.bounding_box() if item.is_visible() else None
            if box and box["width"] > best_width:
                best, best_width = item, box["width"]
        return best if best is not None else (locator.first if locator.count() else None)
    except Exception:
        return None


def _click_last_visible(page: Any, text: str) -> None:
    """The remesh popup floats above the page, so its label is the last visible match."""
    matches = page.get_by_text(text, exact=True)
    for index in range(matches.count() - 1, -1, -1):
        if matches.nth(index).is_visible():
            matches.nth(index).click(force=True, timeout=1500)
            return


def _busy_cards(page: Any) -> bool:
    """True while any of the newest asset cards still shows a progress percentage."""
    try:
        return any(page.evaluate(
            r'''() => [...document.querySelectorAll("[data-testid='assets-card']")].slice(0, 3).map(c => /\d+%/.test(c.innerText))'''))
    except Exception:
        return False


def _lacks_account_marker(page: Any) -> bool:
    try:
        marker = page.get_by_test_id("sidebar-upgrade-btn")
        return not (marker.count() and marker.first.is_visible())
    except Exception:
        return False


def _visible_role(page: Any, role: str, name: str) -> bool:
    try:
        return page.get_by_role(role, name=name, exact=True).is_visible()
    except Exception:
        return False


def _is_selected(locator: Any) -> bool:
    try:
        return locator.get_attribute("aria-selected") == "true"
    except Exception:
        return False


_PICK_TEXT_JS = r"""(name) => {
  const norm = s => (s || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  const want = norm(name);
  const hits = [...document.querySelectorAll('button, [role=radio], [role=tab], [role=option], label, div, span')]
    .filter(el => el.offsetParent !== null && norm(el.innerText || el.textContent) === want);
  if (!hits.length) return false;
  hits.sort((a, b) => (a.getBoundingClientRect().width * a.getBoundingClientRect().height) - (b.getBoundingClientRect().width * b.getBoundingClientRect().height));
  const target = hits[0];
  (target.closest('button, [role=radio], [role=tab], [role=option], label') || target).click();
  return true;
}"""

_SURVEY_JS = """() => {
  const buttons = [...document.querySelectorAll('button')].filter(b => b.offsetParent);
  const next = buttons.find(b => b.innerText.trim() === 'Tiếp tục');
  if (!next || !next.disabled) return '';
  let box = next.parentElement;
  while (box && [...box.querySelectorAll('button')].filter(b => b.offsetParent).length < 4) box = box.parentElement;
  if (!box) return '';
  const skip = ['Tiếp tục', 'Quay lại', 'Hoàn thành'];
  const options = [...box.querySelectorAll('button')].filter(b => b.offsetParent && !b.disabled && !skip.includes(b.innerText.trim()));
  const pick = options.find(b => b.innerText.trim() === 'Khác') || options[options.length - 1];
  if (!pick) return '';
  pick.click();
  return pick.innerText.trim();
}"""


def dismiss_onboarding(page: Any, max_rounds: int = 15) -> int:
    """New accounts get a multi-step survey; advance it until nothing blocks the workspace."""
    quiet = 0
    for round_number in range(max_rounds):
        _advance_onboarding(page)
        try:
            _ = page.evaluate(_SURVEY_JS)
        except Exception:
            pass
        page.wait_for_timeout(700)
        blocking = False
        try:
            for label in ("Tiếp tục", "Tiếp theo", "Hiểu rồi"):
                cont = page.get_by_role("button", name=label, exact=(label != "Hiểu rồi"))
                blocking = blocking or bool(cont.count() and cont.first.is_visible())
        except Exception:
            pass
        quiet = 0 if blocking else quiet + 1
        if quiet >= 2:
            return round_number
    return max_rounds


def _advance_onboarding(page: Any) -> None:
    """Advance Meshy's first-run survey using DOM controls only."""
    try:
        # Daily reward popup can block the workspace. Claim an enabled reward
        # control when present, then dismiss the informational dialog.
        for reward_name in ("Nhận", "Nhận thưởng", "Claim", "Nhận ngay"):
            reward = page.get_by_role("button", name=reward_name, exact=True)
            if reward.count() and reward.first.is_visible() and reward.first.is_enabled():
                reward.first.click(force=True, timeout=1000)
                break
        for dismiss_name in ("Hiểu rồi", "Đã hiểu", "Đóng", "Bỏ qua"):
            dismiss_info = page.get_by_role("button", name=dismiss_name, exact=True)
            if dismiss_info.count() and dismiss_info.first.is_visible():
                dismiss_info.first.click(force=True, timeout=1000)
        for dismiss in ("Có lẽ sau", "Đóng"):
            button = page.get_by_role("button", name=dismiss, exact=True)
            if button.count() and button.first.is_visible():
                button.first.click(force=True, timeout=800)
        # Close quest/academy and other blocking dialogs when they expose a
        # labelled close control. Never select paid upgrades automatically.
        for close in ("[role='dialog'] button[aria-label='Close']", "[role='dialog'] button[aria-label='Đóng']", "[role='dialog'] button:has-text('×')"):
            loc = page.locator(close)
            if loc.count() and loc.first.is_visible():
                loc.first.click(force=True, timeout=800)
        for name in ("Một mình", "Tôi tự", "Thành viên nhóm", "Hình ảnh sản phẩm", "In 3D", "Trò chơi & XR", "Sửa chữa AI", "In Đa Màu", "Google"):
            button = page.get_by_role("button", name=name, exact=True)
            if button.count() and button.first.is_visible():
                button.first.click(timeout=800)
                break
        # Guided product tour tooltips ("Tiếp theo", "Hiểu rồi!") dim the page and block clicks.
        got_it = page.get_by_role("button", name="Hiểu rồi", exact=False)
        if got_it.count() and got_it.first.is_visible():
            got_it.first.click(force=True, timeout=1000)
        for tour in ("Tiếp theo", "Xong", "Hoàn tất", "Kết thúc", "Bắt đầu"):
            step = page.get_by_role("button", name=tour, exact=True)
            if step.count() and step.first.is_visible() and step.first.is_enabled():
                step.first.click(force=True, timeout=1000)
                break
        cont = page.get_by_role("button", name="Tiếp tục", exact=True)
        if cont.count() and cont.first.is_visible() and cont.first.is_enabled():
            cont.first.click(timeout=1000)
        done = page.get_by_role("button", name="Hoàn thành", exact=True)
        if done.count() and done.first.is_visible() and done.first.is_enabled():
            done.first.click(timeout=1000)
    except Exception:
        pass
