from app.automation.meshy_email_login import EmailLoginOutcome, MeshyEmailLogin


class Locator:
    def __init__(self, visible=True):
        self.visible = visible
        self.first = self
        self.value = None
        self.clicked = False

    def is_visible(self): return self.visible
    def is_enabled(self): return True
    def count(self): return 1 if self.visible else 0
    def click(self): self.clicked = True
    def wait_for(self, **kwargs): pass
    def fill(self, value): self.value = value


class Page:
    def __init__(self):
        self.login = Locator()
        self.email = Locator()
        self.code = Locator()
        self.send = Locator()
        self.verify = Locator()
        self.brought_to_front = False

    def get_by_role(self, role, name, exact=True):
        return {"Đăng nhập": self.login, "Nhận mã": self.send, "Tiếp tục": self.verify}.get(name, Locator(False))

    def locator(self, selector):
        return self.email if selector.startswith('input[type="email"]') else self.code

    def wait_for_timeout(self, ms): pass
    def bring_to_front(self): self.brought_to_front = True

    frames = []


def test_email_login_sends_code_reads_purelymail_and_never_uses_google():
    page = Page()
    seen = []
    codes = iter(("111111", "111111", "481675"))
    result = MeshyEmailLogin(lambda address, **filters: seen.append((address, filters)) or next(codes)).attempt(
        page, "box@purelymail.com")
    assert result == EmailLoginOutcome.AUTHENTICATED
    assert page.email.value == "box@purelymail.com" and page.code.value == "481675"
    assert page.send.clicked and page.verify.clicked
    assert seen[0][1]["sender"] == "meshy"


def test_email_login_stops_for_captcha_instead_of_polling_or_bypassing():
    page = Page()
    body = Locator()
    body.inner_text = lambda **kwargs: "Drag the correct item that fits the pattern"
    original = page.locator
    page.locator = lambda selector: body if selector == "body" else original(selector)
    result = MeshyEmailLogin(lambda *args, **kwargs: None, max_polls=2).attempt(page, "box@purelymail.com")
    assert result == EmailLoginOutcome.MANUAL_VERIFICATION
    assert page.brought_to_front


def test_captcha_marker_does_not_block_code_entry_when_the_mail_arrived():
    page = Page()
    body = Locator()
    body.inner_text = lambda **kwargs: "hcaptcha iframe present"
    original = page.locator
    page.locator = lambda selector: body if selector == "body" else original(selector)
    codes = iter((None, "481675"))
    result = MeshyEmailLogin(lambda *args, **kwargs: next(codes), max_polls=3).attempt(page, "box@purelymail.com")
    assert result == EmailLoginOutcome.AUTHENTICATED and page.code.value == "481675"


def test_provider_exception_does_not_abort_login():
    page = Page()
    calls = iter((None, RuntimeError("imap hiccup"), "481675"))

    def provider(*args, **kwargs):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value
    result = MeshyEmailLogin(provider, max_polls=4).attempt(page, "box@purelymail.com")
    assert result == EmailLoginOutcome.AUTHENTICATED and page.code.value == "481675"
