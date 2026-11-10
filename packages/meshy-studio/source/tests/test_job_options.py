from pathlib import Path

from app.automation.meshy_worker import MeshyWebWorker
from app.core.database import Database
from app.core.job_options import DEFAULT_POLYCOUNT, GenMode, JobOptions, RigType
from app.core.pipeline import PipelineService
from tests.test_meshy_worker import Adapter, Page
from app.automation.meshy_adapter import MeshyLoginState


def test_defaults_and_clamp():
    o = JobOptions()
    assert o.mode == GenMode.TOPOLOGY and o.polycount == DEFAULT_POLYCOUNT == 3000 and not o.rig and not o.remesh
    assert JobOptions(polycount=5).normalized().polycount == 100
    assert JobOptions(polycount=10**6).normalized().polycount == 30000


def test_legacy_row_is_automatic_with_remesh():
    legacy = JobOptions.from_json(None)
    assert legacy.mode == GenMode.AUTOMATIC and legacy.remesh and not legacy.rig
    assert JobOptions.from_json("not json").mode == GenMode.AUTOMATIC


def test_roundtrip_and_job_row(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    opts = JobOptions(GenMode.TOPOLOGY, 4500, True, RigType.QUADRUPED)
    job_id = db.create_job("a.png", "", options=opts.to_json())
    got = JobOptions.from_json(db.get_job(job_id).options)
    assert got == opts


def test_enqueue_stores_options(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    service = PipelineService(db, object())
    job_id = service.enqueue(str(img), "", JobOptions(GenMode.AUTOMATIC, 3000, True, RigType.HUMANOID))
    got = JobOptions.from_json(db.get_job(job_id).options)
    assert got.mode == GenMode.AUTOMATIC and got.rig and got.rig_type == RigType.HUMANOID


class StepAdapter(Adapter):
    def __init__(self, page):
        super().__init__(page)
        self.steps = []
    def configure_topology(self, page, polycount): self.steps.append(("topology", polycount))
    def select_generation_mode(self, page, topology): self.steps.append(("mode", topology))
    def count_cards(self, page): return 0
    def wait_for_new_asset(self, page, before, timeout_ms=90_000): return True
    def wait_for_cards_idle(self, page, timeout_ms=600_000): return True
    def apply_texture(self, page): self.steps.append("texture"); return True
    def optimize_remesh_10k(self, page): self.steps.append("remesh"); return True
    def apply_rig(self, page, rig_type): self.steps.append(("rig", rig_type)); return True
    def open_latest_asset(self, page): return True


def _run(tmp_path, options):
    adapter = StepAdapter(Page(MeshyLoginState.AUTHENTICATED))
    worker = MeshyWebWorker(object(), adapter)  # no export_dir: stops after the steps with "No output"
    worker.run_one(1, tmp_path / "a.png", options=options)
    return adapter.steps


def test_topology_skips_remesh_and_sets_polycount(tmp_path):
    steps = _run(tmp_path, JobOptions(GenMode.TOPOLOGY, 3000))
    assert steps == [("topology", 3000), "texture"]


def test_automatic_remeshes_and_rigs_last(tmp_path):
    steps = _run(tmp_path, JobOptions(GenMode.AUTOMATIC, 3000, True, RigType.HUMANOID))
    assert steps == [("mode", False), "texture", "remesh", ("rig", "humanoid")]


def test_no_options_behaves_like_before(tmp_path):
    steps = _run(tmp_path, None)
    assert steps == [("mode", False), "texture", "remesh"]


def test_topology_textured_in_form_skips_the_separate_texture_step(tmp_path):
    class InForm(StepAdapter):
        def configure_topology(self, page, polycount): self.steps.append(("topology", polycount)); return True
    adapter = InForm(Page(MeshyLoginState.AUTHENTICATED))
    MeshyWebWorker(object(), adapter).run_one(1, tmp_path / "a.png", options=JobOptions(GenMode.TOPOLOGY, 1500))
    assert adapter.steps == [("topology", 1500)]
