from pathlib import Path

from app.automation.meshy_adapter import MeshyLoginState, MeshyWebAdapter, MeshyWebError


class Locator:
    def __init__(self, visible=True, selected="true"):
        self.visible = visible
        self.selected = selected
        self.clicked = False

    def is_visible(self):
        return self.visible

    def click(self):
        self.clicked = True

    def get_attribute(self, name):
        return self.selected if name == "aria-selected" else None


class FakePage:
    def __init__(self, login=False, model=False, verification=False):
        self.login = Locator(login)
        self.model = Locator(model)
        self.model_tab = Locator(model)
        self.verification = Locator(verification)
        self.clicked = []

    def locator(self, selector):
        return self.verification

    def get_by_role(self, role, name, exact=True):
        if name == "Đăng nhập": return self.login
        if name == "Mô hình": return self.model
        if name == "Hình ảnh thành 3D": return self.model_tab
        if name == "Tiếp tục với Google": return Locator(True)
        return Locator(False)


def test_login_state_classification():
    assert MeshyWebAdapter.classify_login_state(FakePage(login=True)) == MeshyLoginState.LOGIN_REQUIRED
    assert MeshyWebAdapter.classify_login_state(FakePage(model=True)) == MeshyLoginState.AUTHENTICATED
    assert MeshyWebAdapter.classify_login_state(FakePage(verification=True)) == MeshyLoginState.MANUAL_VERIFICATION


def test_model_tab_uses_observed_accessible_names():
    page = FakePage(model=True)
    MeshyWebAdapter.open_model_tab(page)
    assert page.model.clicked


def test_google_login_starts_but_does_not_accept_credentials():
    page = FakePage(login=True)
    MeshyWebAdapter.start_manual_google_login(page)
    assert page.login.clicked


def test_upload_rejects_unsupported_format(tmp_path: Path):
    path = tmp_path / "input.gif"
    path.write_bytes(b"gif")
    try:
        MeshyWebAdapter.upload_image(FakePage(), path)
    except ValueError as error:
        assert "JPG" in str(error)
    else:
        raise AssertionError("unsupported image accepted")

