from app.automation.google_login import GoogleLoginOutcome, GoogleOAuthLogin
from app.security.credentials import MemoryCredentialStore


class Locator:
    def __init__(self, visible=True): self.visible, self.filled, self.clicked = visible, None, False
    def is_visible(self): return self.visible
    def fill(self, value): self.filled = value
    def click(self): self.clicked = True


class Page:
    url = "https://accounts.google.com/signin"
    def __init__(self, body=""):
        self.body = body; self.email = Locator(); self.password = Locator(); self.next = Locator()
    def get_by_role(self, role, name, exact=True):
        if name == "Email or phone": return self.email
        if name == "Enter your password": return self.password
        if name == "Next": return self.next
        return Locator(False)
    def get_by_label(self, name, exact=True): return self.email
    def locator(self, selector): return self.password if "password" in selector else Body(self.body)
    def wait_for_timeout(self, value): pass
    def get_by_text(self, text, exact=False): return Locator(text.lower() in self.body.lower())


class Body:
    def __init__(self, text): self.text = text
    def inner_text(self): return self.text


def test_google_login_reads_credentials_from_store_and_fills_fields():
    store = MemoryCredentialStore(); store.set("acct", "email", "user@example.com"); store.set("acct", "password", "secret")
    page = Page()
    result = GoogleOAuthLogin(store).attempt(page, "acct")
    assert result == GoogleLoginOutcome.WAITING
    assert page.email.filled == "user@example.com"
    assert page.password.filled == "secret"


def test_google_login_reports_missing_credentials_without_filling():
    page = Page()
    assert GoogleOAuthLogin(MemoryCredentialStore()).attempt(page, "acct") == GoogleLoginOutcome.CREDENTIALS_UNAVAILABLE


def test_google_login_stops_for_mfa_or_captcha():
    store = MemoryCredentialStore(); store.set("acct", "email", "user@example.com"); store.set("acct", "password", "secret")
    assert GoogleOAuthLogin(store).attempt(Page("2-step verification required"), "acct") == GoogleLoginOutcome.MANUAL_VERIFICATION



class TotpPage(Page):
    """Challenge page that shows a code field; leaves Google once Next is clicked."""
    def __init__(self):
        super().__init__(""); self.code = _First(); self.nexts = 0
        self.next = _CountingNext(self)
    def locator(self, selector):
        if "totpPin" in selector or "tel" in selector: return self.code
        return super().locator(selector)


class _First(Locator):
    first = property(lambda self: self)


class _CountingNext(Locator):
    def __init__(self, page): super().__init__(); self.page = page
    def click(self):
        self.page.nexts += 1
        if self.page.nexts == 2:
            self.page.body = "2-step verification"
        if self.page.nexts >= 3:
            self.page.url = "https://www.meshy.ai/workspace"; self.page.body = ""


def test_google_login_enters_totp_when_secret_present():
    from app.security.totp import totp_now
    store = MemoryCredentialStore()
    for kind, value in (("email", "u@example.com"), ("password", "pw"), ("totp", "GEZDGNBVGY3TQOJQ")):
        store.set("acct", kind, value)
    page = TotpPage()
    assert GoogleOAuthLogin(store).attempt(page, "acct") == GoogleLoginOutcome.AUTHENTICATED
    assert page.code.filled == totp_now("GEZDGNBVGY3TQOJQ")
