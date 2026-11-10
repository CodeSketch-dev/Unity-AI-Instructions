import io
import json
import struct
from pathlib import Path

import pytest
from PIL import Image

from app.automation import model_export as m
from app.settings import Settings


def make_glb(path: Path) -> Path:
    def encode(color, fmt):
        buffer = io.BytesIO(); Image.new("RGB", (4, 4), color).save(buffer, format=fmt); return buffer.getvalue()
    images = [encode((255, 0, 0), "WEBP"), encode((0, 0, 255), "WEBP")]
    blob, views = b"", []
    for raw in images:
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(raw)})
        blob += raw + b"\0" * (-len(raw) % 4)
    document = {
        "asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}], "bufferViews": views,
        "images": [{"bufferView": 0, "mimeType": "image/webp"}, {"bufferView": 1, "mimeType": "image/webp"}],
        "textures": [{"extensions": {"EXT_texture_webp": {"source": 0}}}, {"extensions": {"EXT_texture_webp": {"source": 1}}}],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}, "normalTexture": {"index": 1}}],
        "extensionsUsed": ["EXT_texture_webp"],
    }
    text = json.dumps(document).encode(); text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(blob), 0x004E4942) + blob
    path.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    return path


def test_textures_become_named_pngs(tmp_path):
    glb = make_glb(tmp_path / "gate.glb")
    files = m.extract_textures_png(glb, tmp_path / "textures", "gate")
    assert sorted(f.name for f in files) == ["gate_basecolor.png", "gate_normal.png"]
    assert Image.open(files[0]).format == "PNG"


def test_png_glb_replaces_webp_everywhere(tmp_path):
    out = m.png_glb(make_glb(tmp_path / "a.glb"), tmp_path / "b.glb")
    document, binary = m._read_glb(out)
    assert all(i["mimeType"] == "image/png" for i in document["images"])
    assert all("extensions" not in t and t["source"] in (0, 1) for t in document["textures"])
    assert "EXT_texture_webp" not in document["extensionsUsed"]
    view = document["bufferViews"][document["images"][0]["bufferView"]]
    assert binary[view["byteOffset"]:view["byteOffset"] + 4] == b"\x89PNG"


def test_job_folder_is_unique_and_safe(tmp_path):
    first = m.job_folder(tmp_path, "C:/x/My Model!.png", now=0)
    second = m.job_folder(tmp_path, "C:/x/My Model!.png", now=0)
    assert first != second and first.parent == tmp_path and "!" not in first.name and " " not in first.name


def test_fbx_export_uses_blender_and_checks_output(tmp_path):
    glb = tmp_path / "a.glb"; glb.write_bytes(b"x")
    fbx = tmp_path / "a.fbx"
    def runner(cmd, **kw):
        assert "--background" in cmd and str(glb) in cmd and str(fbx) in cmd
        fbx.write_bytes(b"fbx"); return type("R", (), {"returncode": 0})()
    assert m.export_fbx(Path("blender.exe"), glb, fbx, runner) is True
    fbx.unlink()
    assert m.export_fbx(Path("blender.exe"), glb, fbx, lambda cmd, **kw: type("R", (), {"returncode": 0})()) is False


def test_package_model_keeps_glb_when_blender_missing(tmp_path, monkeypatch):
    glb = make_glb(tmp_path / "gate.glb")
    monkeypatch.setattr(m, "ensure_blender", lambda root, log=print: None)
    result = m.package_model(glb, tmp_path, log=lambda msg: None)
    assert len(result["textures"]) == 2 and result["fbx"] is None
    assert any("FBX skipped" in w for w in result["warnings"]) and glb.exists()


def test_settings_export_dir_default_and_roundtrip(tmp_path):
    settings = Settings(tmp_path)
    assert settings.export_dir == tmp_path / "Export"
    settings.export_dir = tmp_path / "elsewhere"
    assert Settings(tmp_path).export_dir == tmp_path / "elsewhere"


@pytest.mark.skipif(m.find_blender(Path(__file__).parent) is None, reason="Blender is not installed")
def test_blender_converts_a_real_glb_to_fbx_and_png(tmp_path):
    from glb_fixture import make_mesh_glb
    glb = make_mesh_glb(tmp_path / "gate.glb", triangles=12)
    result = m.package_model(glb, Path(__file__).parent, log=lambda msg: None)
    assert result["fbx"] is not None and result["warnings"] == []
    fbx = result["fbx"].read_bytes()
    assert fbx.startswith(b"Kaydara FBX Binary") and len(fbx) > 1000
    assert len(result["textures"]) == 1 and Image.open(result["textures"][0]).format == "PNG"


def test_blender_failure_is_reported_not_swallowed(tmp_path, monkeypatch):
    import subprocess
    glb = make_glb(tmp_path / "gate.glb")
    assert m.export_fbx(Path("blender.exe"), glb, tmp_path / "a.fbx", lambda cmd, **kw: type("R", (), {"returncode": 1})()) is False

    def hang(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, 1)
    with pytest.raises(subprocess.TimeoutExpired):
        m.export_fbx(Path("blender.exe"), glb, tmp_path / "a.fbx", hang)
    monkeypatch.setattr(m, "ensure_blender", lambda root, log=print: Path("blender.exe"))
    monkeypatch.setattr(m, "export_fbx", lambda *a, **k: hang(["blender"]))
    result = m.package_model(glb, tmp_path, log=lambda msg: None)  # a hung Blender becomes a warning, files survive
    assert result["fbx"] is None and any("TimeoutExpired" in w for w in result["warnings"]) and glb.exists()
    assert len(result["textures"]) == 2
