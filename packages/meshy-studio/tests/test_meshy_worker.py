from types import SimpleNamespace
from pathlib import Path

from app.automation.meshy_adapter import MeshyLoginState
from app.automation.meshy_worker import MeshyWebWorker, WorkerState


class Locator:
    def __init__(self, visible=True, enabled=True, count=1):
        self.visible, self.enabled, self._count, self.clicked = visible, enabled, count, False

    def is_visible(self): return self.visible
    def is_enabled(self): return self.enabled
    def click(self, **kw): self.clicked = True
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


def test_worker_stops_at_manual_google_login(tmp_path: Path):
    page = Page(MeshyLoginState.LOGIN_REQUIRED)
    adapter = Adapter(page)
    result = MeshyWebWorker(object(), adapter).run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.WAITING_FOR_LOGIN
    assert adapter.started_google


def test_worker_clicks_generate_once_and_keeps_context_open(tmp_path: Path):
    page = Page(MeshyLoginState.AUTHENTICATED, body="Generating")
    adapter = Adapter(page)
    worker = MeshyWebWorker(object(), adapter)
    result = worker.run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.GENERATING
    assert page.generate.clicked
    assert 1 in worker._contexts
    assert adapter.context.close_called is False


def test_worker_does_not_rotate_on_ordinary_error(tmp_path: Path):
    page = Page(MeshyLoginState.UNKNOWN)
    worker = MeshyWebWorker(object(), Adapter(page))
    result = worker.run_one(1, tmp_path / "a.png")
    assert result.state == WorkerState.FAILED
    assert 1 in worker._contexts



def test_rotation_moves_on_after_invalid_credentials(tmp_path: Path):
    from types import SimpleNamespace
    from app.core.scheduler import Scheduler
    from app.automation.meshy_worker import WorkerResult

    class W(MeshyWebWorker):
        def run_one(self, account_id, image_path, *, account_key=None, wait_for_login_ms=120_000):
            state = WorkerState.INVALID_CREDENTIALS if account_id == 1 else WorkerState.GENERATING
            return WorkerResult(state, account_id, "x")
    accounts = [SimpleNamespace(id=i, email=f"{i}@x.com", priority=i, authorized=True, session_valid=False, status="Ready", active_jobs=0) for i in (1, 2)]
    seen = []
    result = W(object(), Adapter(Page(MeshyLoginState.AUTHENTICATED))).run_with_rotation(
        accounts, tmp_path / "a.png", Scheduler(), on_result=lambda a, r: seen.append((a.id, r.state)))
    assert result.account_id == 2 and result.state == WorkerState.GENERATING
    assert seen == [(1, WorkerState.INVALID_CREDENTIALS), (2, WorkerState.GENERATING)]


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
    worker = MeshyWebWorker(object(), FullAdapter(page), export_dir=tmp_path, exporter=FakeExporter())
    result = worker.run_one(1, tmp_path / "gate.png")
    assert result.state == WorkerState.COMPLETED
    assert result.result_path.endswith("gate_acc1_10k.glb")
    assert calls == ["idle", "texture", "idle", "remesh", "idle", "export"]


def test_worker_fails_when_remesh_cannot_start(tmp_path: Path):
    class NoRemesh(Adapter):
        def optimize_remesh_10k(self, page): return False
    worker = MeshyWebWorker(object(), NoRemesh(Page(MeshyLoginState.AUTHENTICATED)))
    assert worker.run_one(1, tmp_path / "a.png").state == WorkerState.FAILED


def test_rotation_closes_the_browser_of_the_account_it_leaves(tmp_path: Path):
    from types import SimpleNamespace
    from app.core.scheduler import Scheduler
    from app.automation.meshy_worker import WorkerResult
    closed = []

    class Manager:
        def close_account(self, account_id, context=None): closed.append(account_id)

    class W(MeshyWebWorker):
        def run_one(self, account_id, image_path, *, account_key=None, wait_for_login_ms=120_000):
            return WorkerResult(WorkerState.QUOTA_LIMITED if account_id == 1 else WorkerState.GENERATING, account_id, "x")
        def context_for(self, account_id): return object(), Context(Page(MeshyLoginState.AUTHENTICATED))
    accounts = [SimpleNamespace(id=i, email=f"{i}@x.com", priority=i, authorized=True, session_valid=False, status="Ready", active_jobs=0) for i in (1, 2)]
    adapter = Adapter(Page(MeshyLoginState.AUTHENTICATED)); adapter.logout_account = lambda page, email=None: True
    W(Manager(), adapter).run_with_rotation(accounts, tmp_path / "a.png", Scheduler())
    assert closed == [1]


def test_close_stray_tabs_keeps_only_workspace_page():
    class Tab:
        def __init__(self): self.closed = False
        def close(self): self.closed = True
    keep, oauth, blank = Tab(), Tab(), Tab()
    MeshyWebWorker.close_stray_tabs(SimpleNamespace(pages=[keep, oauth, blank]), keep)
    assert (keep.closed, oauth.closed, blank.closed) == (False, True, True)
