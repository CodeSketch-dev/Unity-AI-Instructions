from __future__ import annotations

import threading
from typing import Any, Callable

from app.automation.meshy_email_login import CODE_FIELD, EmailLoginOutcome, _captcha_visible, _click_named

TRIPO_URL = "https://studio.tripo3d.ai/workspace/generate"


class TripoEmailLogin:
    """Sign in to an EXISTING, explicitly imported Tripo account through the mailbox code ("Verification Code Login").

    Steps (selectors from the live dialog): Sign up/Log in -> Continue with Email -> Enter Email -> Send Code -> code field -> verify.
    The mailbox is polled from the moment the code is requested, exactly like MeshyEmailLogin."""

    def __init__(self, otp_provider: Callable[..., str | None], max_polls: int = 300):
        self._otp_provider = otp_provider
        self._max_polls = max_polls

    @staticmethod
    def logged_in(page: Any) -> bool:
        try:
            return page.get_by_text("Sign up/Log in", exact=False).count() == 0 and page.get_by_text("Generate", exact=False).count() > 0
        except Exception:
            return False

    def attempt(self, page: Any, address: str) -> EmailLoginOutcome:
        try:
            if self.logged_in(page):
                return EmailLoginOutcome.AUTHENTICATED
            opener = page.get_by_text("Sign up/Log in", exact=False)
            if opener.count() and opener.first.is_visible():
                opener.first.click()
            if not _click_named(page, ("Continue with Email",)):
                with_email = page.get_by_text("Continue with Email", exact=False)
                if with_email.count():
                    with_email.first.click()
            email = page.locator('input[type="email"], input[placeholder*="email" i]').first
            email.wait_for(state="visible", timeout=10000)
            email.fill(address)
            baseline = self._otp_provider(address, sender="tripo", subject="verification", within_minutes=5)
            if not _click_named(page, ("Send Code", "Send code")):
                return EmailLoginOutcome.FAILED
            found: dict[str, str | None] = {"code": None}
            arrived, stop = threading.Event(), threading.Event()

            def watch() -> None:
                while not stop.is_set():
                    try:
                        candidate = self._otp_provider(address, sender="tripo", subject="verification", within_minutes=5)
                    except Exception:  # transient IMAP hiccup: the next poll retries
                        candidate = None
                    if candidate and candidate != baseline:
                        found["code"] = candidate
                        arrived.set()
                        return
                    stop.wait(0.3)

            threading.Thread(target=watch, daemon=True, name="tripo-otp-watch").start()
            saw_captcha = False
            try:
                for tick in range(self._max_polls * 4):
                    page.wait_for_timeout(50)
                    if arrived.wait(0.2):
                        break
                    if tick % 4 == 0 and not saw_captcha and _captcha_visible(page):
                        page.bring_to_front()  # the owner solves it; the code is read meanwhile
                        saw_captcha = True
            finally:
                stop.set()
            code = found["code"]
            if not code:
                return EmailLoginOutcome.MANUAL_VERIFICATION if saw_captcha else EmailLoginOutcome.OTP_UNAVAILABLE
            field = page.locator(CODE_FIELD).first
            field.wait_for(state="visible", timeout=20000)
            field.fill(code)
            _click_named(page, ("Verify", "Continue", "Log in", "Login", "Submit", "Confirm"))
            page.wait_for_timeout(1500)
            return EmailLoginOutcome.AUTHENTICATED if self.logged_in(page) else EmailLoginOutcome.FAILED
        except Exception:
            return EmailLoginOutcome.FAILED
