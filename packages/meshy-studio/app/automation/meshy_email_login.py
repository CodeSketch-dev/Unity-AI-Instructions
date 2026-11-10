from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable


class EmailLoginOutcome(StrEnum):
    AUTHENTICATED = "authenticated"
    OTP_UNAVAILABLE = "otp_unavailable"
    FAILED = "failed"
    MANUAL_VERIFICATION = "manual_verification"


class MeshyEmailLogin:
    """Authenticate an explicitly imported existing Meshy account through its mailbox OTP."""

    def __init__(self, otp_provider: Callable[..., str | None], max_polls: int = 300):
        self._otp_provider = otp_provider
        self._max_polls = max_polls

    def attempt(self, page: Any, address: str) -> EmailLoginOutcome:
        try:
            login = page.get_by_role("button", name="Đăng nhập", exact=True)
            if not login.is_visible():
                login = page.get_by_role("link", name="Đăng nhập", exact=True)
            if login.is_visible():
                login.click()
            email = page.locator('input[type="email"]').first
            email.wait_for(state="visible", timeout=10000)
            email.fill(address)
            baseline = self._otp_provider(address, sender="meshy", subject="verification", within_minutes=5)
            if not _click_named(page, ("Nhận mã", "Get code", "Send code")):
                return EmailLoginOutcome.FAILED
            code = None
            saw_captcha = False
            for _ in range(self._max_polls):
                page.wait_for_timeout(1000)
                if _captcha_visible(page):
                    if not saw_captcha:
                        page.bring_to_front()
                        saw_captcha = True
                    continue
                code = self._otp_provider(address, sender="meshy", subject="verification", within_minutes=5)
                if code and code != baseline:
                    break
                code = None
            if not code:
                return EmailLoginOutcome.MANUAL_VERIFICATION if saw_captcha else EmailLoginOutcome.OTP_UNAVAILABLE
            field = page.locator('input[maxlength="6"], input[inputmode="numeric"], input[name*="code" i]').first
            field.wait_for(state="visible", timeout=10000)
            field.fill(code)
            _click_named(page, ("Tiếp tục", "Xác minh", "Continue", "Verify", "Đăng nhập"))
            return EmailLoginOutcome.AUTHENTICATED
        except Exception:
            return EmailLoginOutcome.FAILED


def _click_named(page: Any, names: tuple[str, ...]) -> bool:
    for name in names:
        button = page.get_by_role("button", name=name, exact=True)
        if button.count() and button.first.is_visible() and button.first.is_enabled():
            button.first.click()
            return True
    return False


def _captcha_visible(page: Any) -> bool:
    markers = ("drag the correct item", "verify you are human", "captcha", "funcaptcha", "arkose", "hcaptcha")
    try:
        frames = getattr(page, "frames", []) or []
        for frame in [page, *frames]:
            try:
                text = frame.locator("body").inner_text(timeout=300).lower()
                if any(marker in text for marker in markers):
                    return True
            except Exception:
                pass
        for iframe in page.locator("iframe").all():
            value = " ".join(filter(None, (iframe.get_attribute("src"), iframe.get_attribute("title")))).lower()
            if any(marker in value for marker in markers):
                return True
    except Exception:
        pass
    return False
