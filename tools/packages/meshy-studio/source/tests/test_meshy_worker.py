import time
from types import SimpleNamespace
from pathlib import Path

from app.automation.meshy_adapter import MeshyLoginState
from app.automation.meshy_worker import MeshyWebWorker, WorkerState
from app.automation.meshy_email_login import EmailLoginOutcome


class Locator:
    def __init__(self, visible=True, enabled=True, count=1):
        self.visible, self.enabled, self._count, self.clicked, self.click_count = visible, enabled, count, False, 0

    def is_visible(self): return self.visible
    def is_enabled(self): return self.enabled
    def click(self, **kw): self.clicked = True; self.click_count += 1
    def count(self): return self._count
    def inner_text(self): return ""


class Page:
    def __init__(self, state, body="Generating"):
        self.state = state
        self.body = body
        self.model = Locator(True)
        self.tab = Locator(True)
        self.generate = Locator(True, True)
        self.preview = Locator(True, count=1)

    def get_by_role(self, role, name, exact=True):
        if name == "Đăng nhập": return Locator(self.state == MeshyLoginState.LOGIN_REQUIRED)
        if name == "Tiếp tục với Google": return Locator(True)
        if name == "Mô hình": return self.model
        if name == "Hình ảnh thành 3D": return self.tab
        if name == "Tạo ra": return self.generate
        return Locator(False)

    def get_by_text(self, text, exact=False): return Locator(True)
    def wait_for_timeout(self, ms): pass
    def locator(self, selector):
        return self.preview if selector == "img" else Locator(True)


class Context:
    def __init__(self, page): self.pages = [page]; self.close_called = False
    def close(self): self.close_called = True


class Adapter:
    def __init__(self, page): self.page = page; self.generate_calls = 0; self.context = None
    def open_profile(self, account_id, headless=False): self.context = Context(self.page); return object(), self.context
    def classify_login_state(self, page): return self.page.state
    def start_manual_google_login(self, page): self.started_google = True
    def wait_for_authenticated(self, page, timeout_ms=120_000): return self.page.state
    def open_model_tab(self, page): self.opened_model = True
    def upload_image(self, page, image_path): self.uploaded = True
    def _unused(self): pass


def test_worker_does_not_start_google_login(tmp_path: Path):
    page = Page(MeshyLoginState.LOGIN_REQUIRED)
    adapter = Adapter(page)
    result = MeshyWebWorker(object(), adapter).run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.INVALID_CREDENTIALS
    assert not hasattr(adapter, "started_google")


def test_worker_uses_email_otp_without_starting_google(tmp_path: Path):
    page = Page(MeshyLoginState.LOGIN_REQUIRED)
    adapter = Adapter(page)

    class EmailLogin:
        def attempt(self, actual_page, address):
            assert address == "box@purelymail.com"
            actual_page.state = MeshyLoginState.AUTHENTICATED
            return EmailLoginOutcome.AUTHENTICATED

    worker = MeshyWebWorker(object(), adapter, email_login=EmailLogin(), auth_mode=lambda key: "email_otp")
    result = worker.run_one(1, tmp_path / "a.png", account_key="box@purelymail.com")
    assert not hasattr(adapter, "started_google")
    assert result.state == WorkerState.FAILED and "No output" in result.message


def test_worker_rejects_legacy_google_account_before_opening_browser(tmp_path: Path):
    adapter = Adapter(Page(MeshyLoginState.AUTHENTICATED))
    worker = MeshyWebWorker(object(), adapter, auth_mode=lambda key: "google")
    result = worker.run_one(1, tmp_path / "a.png", account_key="legacy@example.com")
    assert result.state == WorkerState.INVALID_CREDENTIALS
    assert adapter.context is None


def test_worker_clicks_generate_once_and_keeps_context_open(tmp_path: Path):
    page = Page(MeshyLoginState.AUTHENTICATED, body="Generating")
    adapter = Adapter(page)
    worker = MeshyWebWorker(object(), adapter)
    submitted, progress = [], []
    worker.on_submitted = submitted.append
    worker.on_progress = progress.append
    result = worker.run_one(1, tmp_path / "a.png")
    assert page.generate.click_count == 1 and submitted == [1]  # exactly one paid submission attempt
    assert result.state == WorkerState.FAILED and "No output" in result.message  # no export folder: never a pretend success
    assert progress[0] == 10 and 1 in worker._contexts
    assert adapter.context.close_called is False


def test_worker_never_clicks_generate_again_when_remote_card_is_delayed(tmp_path: Path):
    class SlowRemote(Adapter):
        def count_cards(self, page): return 3
        def wait_for_new_asset(self, page, before, timeout_ms=90_000): return False

    page = Page(MeshyLoginState.AUTHENTICATED)
    worker = MeshyWebWorker(object(), SlowRemote(page))
    submitted = []
    worker.on_submitted = submitted.append
    result = worker.run_one(1, tmp_path / "slow.png")
    assert result.state == WorkerState.FAILED
    assert page.generate.click_count == 1 and submitted == [1]


def test_worker_does_not_rotate_on_ordinary_error(tmp_path: Path):
    page = Page(MeshyLoginState.UNKNOWN)
    worker = MeshyWebWorker(object(), Adapter(page))
    result = worker.run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.FAILED
    assert 1 in worker._contexts




def test_worker_exports_after_texture_and_remesh(tmp_path: Path):
    calls = []

    class FullAdapter(Adapter):
        def apply_texture(self, page): calls.append("texture"); return True
        def optimize_remesh_10k(self, page): calls.append("remesh"); return True
        def wait_for_cards_idle(self, page, timeout_ms=0): calls.append("idle"); return True

    class FakeExporter:
        def export_latest(self, context, page, target):
            calls.append("export")
            return {"path": target, "triangles": 9445, "images": 3}

    page = Page(MeshyLoginState.AUTHENTICATED)
    packaged = []
    packager = lambda glb: packaged.append(glb) or {"textures": [1, 2, 3], "fbx": "x.fbx", "warnings": []}
    worker = MeshyWebWorker(object(), FullAdapter(page), export_dir=lambda: tmp_path, exporter=FakeExporter(), packager=packager)
    result = worker.run_one(1, tmp_path / "gate.png")
    assert result.state == WorkerState.COMPLETED
    folder = Path(result.result_path).parent
    assert folder.parent == tmp_path and folder.name.startswith("gate_")  # one sub-folder per model
    assert result.result_path.endswith("gate.glb") and packaged == [Path(result.result_path)]
    assert "3 PNG textures" in result.message and "FBX yes" in result.message
    assert calls == ["idle", "texture", "idle", "remesh", "idle", "export"]


def test_worker_fails_when_remesh_cannot_start(tmp_path: Path):
    class NoRemesh(Adapter):
        def optimize_remesh_10k(self, page): return False
    worker = MeshyWebWorker(object(), NoRemesh(Page(MeshyLoginState.AUTHENTICATED)))
    assert worker.run_one(1, tmp_path / "a.png").state == WorkerState.FAILED



def test_close_stray_tabs_keeps_only_workspace_page():
    class Tab:
        def __init__(self): self.closed = False
        def close(self): self.closed = True
    keep, oauth, blank = Tab(), Tab(), Tab()
    MeshyWebWorker.close_stray_tabs(SimpleNamespace(pages=[keep, oauth, blank]), keep)
    assert (keep.closed, oauth.closed, blank.closed) == (False, True, True)


def test_low_credit_stops_before_generate_and_reports_balance(tmp_path: Path):
    seen = []

    class CreditAdapter(Adapter):
        def read_credits(self, page): return 15

    page = Page(MeshyLoginState.AUTHENTICATED)
    worker = MeshyWebWorker(object(), CreditAdapter(page))
    worker.on_credits = lambda account_id, balance: seen.append((account_id, balance))
    result = worker.run_one(7, tmp_path / "a.png")
    assert result.state == WorkerState.QUOTA_LIMITED and "15" in result.message
    assert seen == [(7, 15)] and not page.generate.clicked  # no credit was spent


def test_enough_credit_continues(tmp_path: Path):
    class CreditAdapter(Adapter):
        def read_credits(self, page): return 100
    page = Page(MeshyLoginState.AUTHENTICATED)
    result = MeshyWebWorker(object(), CreditAdapter(page)).run_one(1, tmp_path / "a.png")
    assert page.generate.clicked and result.state != WorkerState.QUOTA_LIMITED


def test_unreadable_credit_is_unknown_not_zero(tmp_path: Path):
    seen = []

    class BlindAdapter(Adapter):
        def read_credits(self, page): return None  # the sidebar could not be read

    page = Page(MeshyLoginState.AUTHENTICATED)
    worker = MeshyWebWorker(object(), BlindAdapter(page))
    worker.on_credits = lambda account_id, balance: seen.append(balance)
    result = worker.run_one(1, tmp_path / "a.png")
    assert result.state != WorkerState.QUOTA_LIMITED and seen == [] and page.generate.clicked


def test_deadline_and_cancel_stop_the_job_at_a_step_boundary(tmp_path: Path):
    page = Page(MeshyLoginState.AUTHENTICATED)
    worker = MeshyWebWorker(object(), Adapter(page))
    worker.deadline = time.monotonic() - 1
    result = worker.run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.FAILED and "Timed out" in result.message and not page.generate.clicked
    worker.deadline = None
    worker.request_cancel()
    assert worker.run_one(1, tmp_path / "a.png").state == WorkerState.CANCELED and not page.generate.clicked


def test_credit_is_refreshed_after_generation_and_a_packaging_crash_keeps_the_glb(tmp_path: Path):
    balances = iter([100, 70, 60])  # before, after generate, after export: the real number each time

    class Full(Adapter):
        def read_credits(self, page): return next(balances)
        def apply_texture(self, page): return True
        def optimize_remesh_10k(self, page): return True
        def wait_for_cards_idle(self, page, timeout_ms=0): return True

    class FakeExporter:
        def export_latest(self, context, page, target):
            from glb_fixture import make_mesh_glb
            return {"path": make_mesh_glb(target, 12), "triangles": 12, "images": 1}

    def exploding_packager(glb):
        raise RuntimeError("blender missing")

    seen = []
    worker = MeshyWebWorker(object(), Full(Page(MeshyLoginState.AUTHENTICATED)), export_dir=tmp_path, exporter=FakeExporter(),
                            packager=exploding_packager)
    worker.on_credits = lambda account_id, balance: seen.append(balance)
    result = worker.run_one(1, tmp_path / "gate.png")
    assert result.state == WorkerState.COMPLETED and Path(result.result_path).is_file()  # the GLB is kept
    assert "post-processing failed" in result.message
    assert seen == [100, 70, 60]
