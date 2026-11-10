from __future__ import annotations

import io
import json
import os
import re
import struct
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

BLENDER_ZIP = "https://download.blender.org/release/Blender4.2/blender-4.2.3-windows-x64.zip"
Log = Callable[[str], None]

# glTF material slots -> file name suffix
_SLOTS = (
    ("pbrMetallicRoughness", "baseColorTexture", "basecolor"),
    ("pbrMetallicRoughness", "metallicRoughnessTexture", "metallic_roughness"),
    (None, "normalTexture", "normal"),
    (None, "occlusionTexture", "occlusion"),
    (None, "emissiveTexture", "emissive"),
)

# Runs inside Blender: import the GLB, export an FBX with embedded textures.
_BLENDER_SCRIPT = """
import bpy, sys
glb, fbx = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
bpy.ops.export_scene.fbx(filepath=fbx, path_mode='COPY', embed_textures=True, axis_forward='-Z', axis_up='Y',
                         apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True)
"""


def safe_name(text: str) -> str:
    return re.sub(r"[^\w.-]+", "_", text).strip("_") or "model"


def job_folder(base: Path, image_path: str | Path, now: float | None = None) -> Path:
    """<base>/<image name>_<timestamp>; never reuses an existing folder."""
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(now))
    folder = Path(base) / f"{safe_name(Path(image_path).stem)}_{stamp}"
    candidate, counter = folder, 2
    while candidate.exists():
        candidate = folder.with_name(f"{folder.name}_{counter}")
        counter += 1
    candidate.mkdir(parents=True)
    return candidate


def _read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError("Not a GLB file")
    offset, document, binary = 12, {}, b""
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == 0x4E4F534A:
            document = json.loads(chunk.decode("utf-8"))
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + length
    return document, binary


def extract_textures_png(glb: Path, out_dir: Path, stem: str) -> list[Path]:
    """Decode every texture embedded in the GLB (Meshy ships WebP) and save it as PNG."""
    from PIL import Image  # bundled in the exe; pip install Pillow when running from source

    document, binary = _read_glb(glb)
    views, images = document.get("bufferViews", []), document.get("images", [])
    textures = document.get("textures", [])
    names: dict[int, str] = {}
    for material in document.get("materials", []):
        for parent, slot, suffix in _SLOTS:
            info = (material.get(parent) if parent else material) or {}
            reference = info.get(slot)
            if reference is not None:
                texture = textures[reference["index"]]
                source = texture.get("source")
                if source is None:  # WebP textures live in an extension block
                    source = next((ext.get("source") for ext in texture.get("extensions", {}).values() if "source" in ext), None)
                names.setdefault(source, suffix)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, image in enumerate(images):
        view = views[image["bufferView"]] if "bufferView" in image else None
        if view is None:
            continue
        start = view.get("byteOffset", 0)
        raw = binary[start:start + view["byteLength"]]
        target = out_dir / f"{safe_name(stem)}_{names.get(index, f'texture{index}')}.png"
        Image.open(io.BytesIO(raw)).save(target, format="PNG")
        written.append(target)
    return written


def png_glb(glb: Path, dest: Path) -> Path:
    """Copy of the GLB whose WebP textures are re-encoded as PNG, so the FBX embeds PNG, not WebP."""
    from PIL import Image

    document, binary = _read_glb(glb)
    blob = bytearray(binary)
    views = document.setdefault("bufferViews", [])
    for image in document.get("images", []):
        if "bufferView" not in image:
            continue
        view = views[image["bufferView"]]
        raw = bytes(binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]])
        buffer = io.BytesIO()
        Image.open(io.BytesIO(raw)).save(buffer, format="PNG")
        while len(blob) % 4:
            blob.append(0)
        views.append({"buffer": view.get("buffer", 0), "byteOffset": len(blob), "byteLength": buffer.tell()})
        blob += buffer.getvalue()
        image["bufferView"] = len(views) - 1
        image["mimeType"] = "image/png"
    for texture in document.get("textures", []):
        ext = texture.pop("extensions", {})
        if texture.get("source") is None:
            texture["source"] = next((e["source"] for e in ext.values() if "source" in e), None)
    for key in ("extensionsUsed", "extensionsRequired"):
        if key in document:
            document[key] = [name for name in document[key] if name != "EXT_texture_webp"]
    while len(blob) % 4:
        blob.append(0)
    document["buffers"][0]["byteLength"] = len(blob)
    text = json.dumps(document, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    dest.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    return dest


def find_blender(root: Path) -> Path | None:
    configured = os.environ.get("MESHY_BLENDER")
    candidates = [Path(configured)] if configured else []
    for base in (os.environ.get("PROGRAMFILES", r"C:\Program Files"), r"D:\Program Files"):
        candidates += sorted(Path(base).glob("Blender Foundation/Blender */blender.exe"), reverse=True)
    candidates += sorted((Path(root) / "tools" / "blender").glob("*/blender.exe"), reverse=True)
    return next((path for path in candidates if path.is_file()), None)


def ensure_blender(root: Path, log: Log = print) -> Path | None:
    """Installed Blender, or a portable copy downloaded once (~340 MB) next to the app."""
    found = find_blender(root)
    if found is not None:
        return found
    log("Blender not found: downloading a portable copy for FBX export (first time only, ~340 MB)...")
    try:
        target = Path(root) / "tools" / "blender"
        target.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(BLENDER_ZIP, headers={"User-Agent": "MeshyAIStudio"})
        with urllib.request.urlopen(request, timeout=120) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        archive.extractall(target)
    except Exception as error:
        log(f"Blender download failed ({type(error).__name__}); FBX will be skipped.")
        return None
    return find_blender(root)


def export_fbx(blender: Path, glb: Path, fbx: Path, runner: Callable[..., Any] = subprocess.run) -> bool:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as script:
        script.write(_BLENDER_SCRIPT)
    try:
        result = runner([str(blender), "--background", "--python", script.name, "--", str(glb), str(fbx)],
                        capture_output=True, text=True, timeout=600,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return result.returncode == 0 and fbx.is_file() and fbx.stat().st_size > 0
    finally:
        try:
            os.unlink(script.name)
        except OSError:
            pass


def package_model(glb: Path, root: Path, log: Log = print) -> dict[str, Any]:
    """Next to the GLB: textures/*.png and <stem>.fbx. Failures become warnings, never lose the GLB."""
    stem = glb.stem
    out: dict[str, Any] = {"textures": [], "fbx": None, "warnings": []}
    try:
        out["textures"] = extract_textures_png(glb, glb.parent / "textures", stem)
    except Exception as error:
        out["warnings"].append(f"PNG export failed: {type(error).__name__}: {error}")
    blender = ensure_blender(root, log)
    if blender is None:
        out["warnings"].append("Blender unavailable: FBX skipped")
    else:
        with tempfile.TemporaryDirectory() as scratch:
            try:
                source = png_glb(glb, Path(scratch) / glb.name)
            except Exception as error:
                out["warnings"].append(f"PNG re-encode failed ({type(error).__name__}); FBX may embed WebP")
                source = glb
            try:
                if export_fbx(blender, source, glb.with_suffix(".fbx")):
                    out["fbx"] = glb.with_suffix(".fbx")
                else:
                    out["warnings"].append("FBX export failed (Blender returned an error)")
            except Exception as error:  # e.g. subprocess.TimeoutExpired: the GLB and PNGs must survive
                out["warnings"].append(f"FBX export failed: {type(error).__name__}")
    return out
