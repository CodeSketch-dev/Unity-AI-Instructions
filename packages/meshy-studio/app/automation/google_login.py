from __future__ import annotations

from enum import StrEnum
from typing import Any

from app.security.credentials import CredentialStore
from app.security.totp import totp_now


class GoogleLoginOutcome(StrEnum):
    AUTHENTICATED = "authenticated"
    MANUAL_VERIFICATION = "manual_verification"
    INVALID_CREDENTIALS = "invalid_credentials"
    CREDENTIALS_UNAVAILABLE = "credentials_unavailable"
    WAITING = "waiting"


class GoogleOAuthLogin:
    """Fill standard Google fields using CredentialStore only."""

    def __init__(self, credentials: CredentialStore):
        self.credentials = credentials

    def attempt(self, page: Any, account_key: str) -> GoogleLoginOutcome:
        email = self.credentials.get(account_key, "email")
        password = self.credentials.get(account_key, "password")
        if not email or not password:
            return GoogleLoginOutcome.CREDENTIALS_UNAVAILABLE
        try:
            chooser = page.get_by_text("Use another account", exact=True)
            if chooser.count() and chooser.first.is_visible():
                chooser.first.click(timeout=1200)
                page.wait_for_timeout(500)
        except Exception:
            pass
        email_field = None
        for _ in range(20):
            email_field = _first_visible(page, (
                lambda: page.get_by_role("textbox", name="Email or phone", exact=True),
                lambda: page.get_by_label("Email or phone", exact=True),
            ))
            if email_field is not None:
                break
            page.wait_for_timeout(500)
        if email_field is None:
            return GoogleLoginOutcome.WAITING
        email_field.fill(email)
        _click_next(page)
        page.wait_for_timeout(500)
        if _challenge_visible(page):
            return GoogleLoginOutcome.MANUAL_VERIFICATION
        password_field = None
        for _ in range(24):  # the password step slides in after the email Next
            password_field = _first_visible(page, (
                lambda: page.locator('input[type="password"]').first,
                lambda: page.get_by_role("textbox", name="Enter your password", exact=True),
            ))
            if password_field is not None or _challenge_visible(page):
                break
            page.wait_for_timeout(500)
        if password_field is None and _challenge_visible(page):
            return GoogleLoginOutcome.MANUAL_VERIFICATION
        if password_field is None:
            return GoogleLoginOutcome.WAITING
        password_field.fill(password)
        _click_next(page)
        # New Workspace-managed accounts may show an onboarding notice and
        # the Meshy consent screen after the password step. Keep the same
        # OAuth page alive and advance those explicit controls automatically.
        totp_secret = self.credentials.get(account_key, "totp")
        totp_done = False
        for _ in range(24):
            page.wait_for_timeout(500)
            if totp_secret and not totp_done and _challenge_visible(page):
                totp_done = _enter_totp(page, totp_secret)
                continue
            for name in ("I understand", "Continue", "Allow"):
                try:
                    button = page.get_by_role("button", name=name, exact=True)
                    if button.count() and button.first.is_visible() and button.first.is_enabled():
                        button.first.click(timeout=1200)
                        break
                except Exception:
                    pass
            try:
                continue_as = page.get_by_role("button", name="Continue as", exact=False)
                if continue_as.count() and continue_as.first.is_visible() and continue_as.first.is_enabled():
                    continue_as.first.click(timeout=1200)
            except Exception:
                pass
            if "accounts.google.com" not in str(getattr(page, "url", "")):
                return GoogleLoginOutcome.AUTHENTICATED
        if _challenge_visible(page) and "accounts.google.com" in str(getattr(page, "url", "")):
            return GoogleLoginOutcome.MANUAL_VERIFICATION
        if _text_visible(page, "Wrong password") or _text_visible(page, "Couldn\'t find your Google Account"):
            return GoogleLoginOutcome.INVALID_CREDENTIALS
        return GoogleLoginOutcome.AUTHENTICATED if "accounts.google.com" not in str(getattr(page, "url", "")) else GoogleLoginOutcome.WAITING


def _first_visible(page: Any, factories: tuple[Any, ...]) -> Any | None:
    for factory in factories:
        try:
            locator = factory()
            if locator.is_visible():
                return locator
        except Exception:
            continue
    return None


def _click_next(page: Any) -> None:
    button = page.get_by_role("button", name="Next", exact=True)
    if button.is_visible():
        button.click()


def _text_visible(page: Any, text: str) -> bool:
    try:
        return page.get_by_text(text, exact=False).first.is_visible()
    except Exception:
        return False


def _challenge_visible(page: Any) -> bool:
    try:
        body = page.locator("body").inner_text().lower()
    except Exception:
        body = ""
    return any(marker in body for marker in ("captcha", "2-step verification", "mfa", "verify it\'s you", "device verification", "xác minh"))



def _enter_totp(page: Any, secret: str) -> bool:
    """Fill the Google Authenticator code; open the alternate-method list if needed."""
    def code_field() -> Any | None:
        return _first_visible(page, (
            lambda: page.locator("input[name='totpPin']").first,
            lambda: page.locator("input[type='tel']").first,
        ))
    field = code_field()
    if field is None:
        for label in ("Try another way", "Get a verification code from the Google Authenticator app", "Google Authenticator"):
            try:
                item = page.get_by_text(label, exact=False)
                if item.count() and item.first.is_visible():
                    item.first.click(timeout=1500)
                    page.wait_for_timeout(700)
            except Exception:
                pass
        field = code_field()
    if field is None:
        return False
    field.fill(totp_now(secret))
    _click_next(page)
    return True
