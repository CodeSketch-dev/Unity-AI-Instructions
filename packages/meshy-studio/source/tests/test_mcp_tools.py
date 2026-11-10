import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.glb_fixture import make_mesh_glb
from tests.test_mcp_server import ROOT, call, rpc


def run(tmp_path, *calls):
    out = rpc(tmp_path, [call(name, **args) for name, args in calls])
    return [(json.loads(r["result"]["content"][0]["text"]) if not r["result"].get("isError") else r["result"]["content"][0]["text"])
            for r in out]


def test_full_tool_list_is_exposed(tmp_path):
    names = {t["name"] for t in rpc(tmp_path, [("tools/list", {})])[0]["result"]["tools"]}
    assert {"app_status", "launch_app", "generate_model", "generate_models", "job_status", "wait_for_jobs", "list_jobs", "cancel_jobs",
            "pause_jobs", "resume_jobs", "retry_jobs", "list_accounts", "import_accounts", "list_models", "inspect_model",
            "unity_import", "blender_status", "blender_inspect", "blender_decimate", "blender_convert", "blender_atlas",
            "triangle_budget_guide", "workflow_guide"} <= names


def test_per_item_polycount_modes_and_rig_reach_the_job(tmp_path):
    a, b = tmp_path / "gate.png", tmp_path / "rock.png"
    a.write_bytes(b"x"); b.write_bytes(b"x")
    result, status = run(tmp_path,
                         ("generate_models", {"items": [{"image_path": str(a), "polycount": 12000},
                                                        {"image_path": str(b), "mode": "automatic", "rig": True, "rig_type": "humanoid"},
                                                        {"image_path": str(tmp_path / "nope.txt")}]}),
                         ("job_status", {"job_id": 1}))
    assert [q["options"]["polycount"] for q in result["queued"]][0] == 12000
    assert result["queued"][1]["options"] == {"mode": "automatic", "polycount": 3000, "rig": True, "rig_type": "humanoid"}
    assert len(result["rejected"]) == 1 and "nope.txt" in result["rejected"][0]["image_path"]
    assert status["options"]["mode"] == "topology" and status["status"] == "Pending"
    assert result["queued"][0]["app_running"] is False and "warning" in result["queued"][0]


def test_polycount_is_clamped_to_meshy_limits(tmp_path):
    img = tmp_path / "a.png"; img.write_bytes(b"x")
    low, high = run(tmp_path, ("generate_model", {"image_path": str(img), "polycount": 5}),
                    ("generate_model", {"image_path": str(img), "polycount": 10**6}))
    assert low["options"]["polycount"] == 100 and high["options"]["polycount"] == 30000


def test_captcha_waiting_job_is_reported_to_the_agent_and_resumable(tmp_path):
    from app.core.database import Database
    img = tmp_path / "a.png"; img.write_bytes(b"x")
    (tmp_path / "data").mkdir()
    database = Database(tmp_path / "data" / "meshy.sqlite3")
    job = database.create_job(str(img))
    database.update_job(job, status="Paused", error="CAPTCHA waiting on account #1: solve it")
    database.close()
    status, waited, status_app, resumed = run(tmp_path, ("job_status", {"job_id": job}), ("wait_for_jobs", {"job_ids": [job], "timeout_s": 5}),
                                              ("app_status", {}), ("resume_jobs", {"job_ids": [job]}))
    assert status["needs_user"] == "captcha" and "CAPTCHA" in status["hint"]
    assert waited["needs_owner"] == [job] and not waited["timed_out"]  # returns at once, no 5 s wait
    assert status_app["jobs_waiting_for_owner"] == [job] and any("CAPTCHA" in b for b in status_app["blockers"])
    assert resumed["resumed"] == 1


def test_retry_refuses_jobs_already_submitted_to_meshy(tmp_path):
    from app.core.database import Database
    img = tmp_path / "a.png"; img.write_bytes(b"x")
    (tmp_path / "data").mkdir()
    database = Database(tmp_path / "data" / "meshy.sqlite3")
    submitted, local = database.create_job(str(img)), database.create_job(str(img))
    database.update_job(submitted, status="Failed", submitted=1)
    database.update_job(local, status="Failed")
    database.close()
    (result,) = run(tmp_path, ("retry_jobs", {"job_ids": [submitted, local]}))
    assert result["refused_already_submitted"] == [submitted] and result["requeued"] == 1


def test_inspect_model_reads_a_glb_without_blender(tmp_path):
    glb = make_mesh_glb(tmp_path / "m.glb", triangles=24)
    (info,) = run(tmp_path, ("inspect_model", {"path": str(glb)}))
    assert info["triangles"] == 24 and info["images"] == 1 and info["skinned"] is False


def test_unity_import_copies_models_and_textures_inside_assets_only(tmp_path):
    project = tmp_path / "Game"
    (project / "Assets").mkdir(parents=True); (project / "ProjectSettings").mkdir()
    job = tmp_path / "Export" / "gate_1"
    (job / "textures").mkdir(parents=True)
    (job / "gate.glb").write_bytes(b"g"); (job / "gate.fbx").write_bytes(b"f"); (job / "textures" / "gate_basecolor.png").write_bytes(b"p")
    copied, again, escape, notproject = run(
        tmp_path,
        ("unity_import", {"unity_project": str(project), "paths": [str(job)]}),
        ("unity_import", {"unity_project": str(project), "paths": [str(job)]}),
        ("unity_import", {"unity_project": str(project), "paths": [str(job)], "dest": "../Outside"}),
        ("unity_import", {"unity_project": str(tmp_path), "paths": [str(job)]}))
    assert sorted(copied["copied"]) == ["Assets/_Art/3D/Meshy/Textures/gate_basecolor.png", "Assets/_Art/3D/Meshy/gate.fbx",
                                        "Assets/_Art/3D/Meshy/gate.glb"]
    assert again["copied"] == [] and len(again["skipped_existing"]) == 3  # never overwrites silently
    assert "inside the project" in escape and "not a Unity project" in notproject


def test_budget_and_workflow_guides(tmp_path):
    budget, flow = run(tmp_path, ("triangle_budget_guide", {"role": "hero"}), ("workflow_guide", {}))
    assert budget["budgets"][0]["role"] == "hero" and "blender_atlas" in json.dumps(flow)


def _blender():
    sys.path.insert(0, str(ROOT))
    from app.automation.model_export import find_blender
    return find_blender(ROOT)


@pytest.mark.skipif(_blender() is None, reason="Blender not installed")
def test_blender_decimate_atlas_and_inspect_on_a_real_mesh(tmp_path):
    sys.path.insert(0, str(ROOT))
    from app.mcp import blender
    # A small real mesh: an icosphere-like model exported by Blender itself keeps the test independent of Meshy output.
    seed = tmp_path / "seed.glb"
    script = tmp_path / "seed.py"
    script.write_text("import bpy\nbpy.ops.wm.read_factory_settings(use_empty=True)\nbpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4)\n"
                      "bpy.ops.export_scene.gltf(filepath=r'%s', export_format='GLB')\n" % seed, encoding="utf-8")
    subprocess.run([str(_blender()), "--background", "--python", str(script)], capture_output=True, timeout=300)
    assert seed.is_file()
    info = blender.blender_inspect({"input": str(seed)})
    assert info["triangles"] == 1280 and info["meshes"] == 1
    small = blender.blender_decimate({"input": str(seed), "target_tris": 400, "output": str(tmp_path / "small.glb")})
    assert 320 <= small["triangles_after"] <= 480 and small["triangles_before"] == 1280
    atlas = blender.blender_atlas({"inputs": [{"path": str(seed), "name": "ball"}, {"path": str(tmp_path / "small.glb"), "name": "smallball"}],
                                   "output_dir": str(tmp_path / "atlas"), "atlas_size": 256, "formats": ["glb"]})
    assert atlas["materials"] == 1 and atlas["textures"] == 1
    assert (tmp_path / "atlas" / "atlas.png").is_file() and (tmp_path / "atlas" / "ball.glb").is_file()
    after = blender.blender_inspect({"input": str(tmp_path / "atlas" / "smallball.glb")})
    assert after["materials"] == 1 and list(after["images"]) == ["atlas"]
