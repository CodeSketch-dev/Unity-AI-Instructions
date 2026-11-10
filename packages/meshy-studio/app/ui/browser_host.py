from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from typing import Any

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QWidget


class BrowserHostWidget(QWidget):
    """Hosts a headed Playwright Chromium top-level window inside this QWidget on Windows."""

    state_changed = Signal(str)

    def __init__(self, browser_manager: Any, parent: QWidget | None = None):
        super().__init__(parent)
        self.browser_manager = browser_manager
        self._playwright = None
        self._context = None
        self._page = None
        self._hwnd: int | None = None
        self._account_id: int | None = None
        self._onboarding_timer = QTimer(self)
        self._onboarding_timer.setInterval(1500)
        self._onboarding_timer.timeout.connect(self._finish_onboarding)
        self.setMinimumSize(640, 420)

    @property
    def hosted(self) -> bool:
        return self._hwnd is not None

    @property
    def page(self) -> Any:
        return self._page

    @property
    def context(self) -> Any:
        return self._context

    def start(self, account_id: int) -> bool:
        if self._context is not None:
            return self.hosted
        self._account_id = account_id
        self._playwright, self._context = self.browser_manager.launch(account_id, headless=False)
        self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        try:
            self._page.bring_to_front()
            self._page.evaluate("document.title = 'Meshy AI Studio - Meshy Sign In'")
            login_button = self._page.get_by_role("button", name="Đăng nhập")
            if login_button.count():
                login_button.first.click(timeout=5000)
            google_button = self._page.get_by_role("button", name="Tiếp tục với Google")
            if google_button.count():
                google_button.first.click(timeout=5000)
            close_restore = self._page.get_by_role("button", name="Close")
            if close_restore.count():
                close_restore.last.click(timeout=1500)
            model_tab = self._page.get_by_role("radio", name="Mô hình")
            if model_tab.count():
                model_tab.click(timeout=5000)
        except Exception:
            pass
        # Never match the host application's own window; only adopt Chrome's
        # top-level window created for the Meshy page.
        self._hwnd = _find_window_any(("Không gian làm việc", "Google Chrome"), timeout_seconds=8)
        if self._hwnd is None:
            self.state_changed.emit("browser_window_not_found")
            return False
        _set_parent_and_resize(self._hwnd, int(self.winId()), self.width(), self.height())
        self._onboarding_timer.start()
        self.state_changed.emit("embedded")
        return True

    def _finish_onboarding(self) -> None:
        if self._page is None:
            return
        try:
            solo = self._page.get_by_role("button", name="Một mình")
            if solo.count():
                solo.first.click(timeout=800)
            company = self._page.get_by_role("button", name="Tôi tự")
            if company.count():
                company.first.click(timeout=800)
            role = self._page.get_by_role("button", name="Thành viên nhóm")
            if role.count():
                role.first.click(timeout=800)
            for option in ("Hình ảnh sản phẩm", "In 3D", "Trò chơi & XR", "Sửa chữa AI", "In Đa Màu", "Gửi tới Slicer", "Phân tách Tự động", "Google", "Một mình"):
                choice = self._page.get_by_role("button", name=option)
                if choice.count():
                    choice.first.click(timeout=800)
                    break
            cont = self._page.get_by_role("button", name="Tiếp tục")
            if cont.count() and cont.first.is_enabled():
                cont.first.click(timeout=1000)
                self._onboarding_timer.stop()
            done = self._page.get_by_role("button", name="Hoàn thành", exact=True)
            if done.count() and done.first.is_visible() and done.first.is_enabled():
                done.first.click(timeout=1000)
                self._onboarding_timer.stop()
        except Exception:
            pass

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if self._hwnd is not None:
            _move_window(self._hwnd, self.width(), self.height())

    def stop(self) -> None:
        self._onboarding_timer.stop()
        if self._context is not None:
            self._context.close()
        close_driver = getattr(self.browser_manager, "close_thread_driver", None)
        if close_driver is not None:
            close_driver()
        self._context = self._playwright = self._page = None
        self._hwnd = None
        self.state_changed.emit("stopped")


def _find_window_any(titles: tuple[str, ...], timeout_seconds: int) -> int | None:
    if not hasattr(ctypes, "windll"):
        return None
    user32 = ctypes.windll.user32
    found: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd: int, _: int) -> bool:
        buffer = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buffer, 512)
        if user32.IsWindowVisible(hwnd) and any(title.lower() in buffer.value.lower() for title in titles):
            found.append(hwnd)
            return False
        return True

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        user32.EnumWindows(callback, 0)
        if found:
            return found[0]
        time.sleep(0.1)
    return None


def _set_parent_and_resize(hwnd: int, parent: int, width: int, height: int) -> None:
    user32 = ctypes.windll.user32
    # Convert Chrome's top-level window into a true child window so its
    # non-client frame does not consume space or float outside the host.
    GWL_STYLE = -16
    WS_CHILD = 0x40000000
    WS_VISIBLE = 0x10000000
    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    style = (style | WS_CHILD | WS_VISIBLE) & ~(WS_CAPTION | WS_THICKFRAME)
    user32.SetWindowLongW(hwnd, GWL_STYLE, style)
    user32.SetParent(hwnd, parent)
    user32.ShowWindow(hwnd, 5)
    # Recalculate non-client metrics after removing the top-level frame.
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
    _move_window(hwnd, width, height)


def _move_window(hwnd: int, width: int, height: int) -> None:
    ctypes.windll.user32.MoveWindow(hwnd, 0, 0, max(1, width), max(1, height), True)

