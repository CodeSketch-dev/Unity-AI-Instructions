"""Library, model inspection and Unity hand-off tools (file based; Unity itself is driven by the Unity MCP)."""
from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path
from typing import Any

from app.mcp import context
from app.mcp.registry import BOOL, STR, schema, tool

TEXTURE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MODEL_SUFFIXES = {".glb", ".fbx"}


def glb_info(path: str | Path) -> dict[str, Any]:
    """Pure-Python GLB summary (no Blender): triangles, meshes, materials, images, real size from POSITION min/max."""
    path = Path(path)
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise ValueError("not a GLB file")
    length, _kind = struct.unpack_from("<II", data, 12)
    doc = json.loads(data[20:20 + length].decode("utf-8"))
    accessors = doc.get("accessors", [])
    tris = 0
    lo, hi = [1e18] * 3, [-1e18] * 3
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            index = primitive.get("indices")
            tris += accessors[index if index is not None else primitive["attributes"]["POSITION"]]["count"] // 3
            pos = accessors[primitive["attributes"]["POSITION"]]
            if "min" in pos and "max" in pos:
                lo = [min(a, b) for a, b in zip(lo, pos["min"])]
                hi = [max(a, b) for a, b in zip(hi, pos["max"])]
    return {"path": str(path), "bytes": path.stat().st_size, "triangles": tris, "meshes": len(doc.get("meshes", [])),
            "materials": len(doc.get("materials", [])), "images": len(doc.get("images", [])),
            "skinned": bool(doc.get("skins")), "size_xyz": [round(h - l, 4) for l, h in zip(lo, hi)] if tris else [0, 0, 0]}


@tool("list_models", "Models in the app's Library (exported GLB/FBX with textures): name, triangles, formats, folder, source image. "
                     "Optional text filter.", schema(search=STR))
def list_models(args: dict) -> list:
    database = context.db()
    try:
        needle = str(args.get("search", "")).lower()
        rows = []
        for m in database.list_models():
            if needle and needle not in (m["name"] or "").lower() and needle not in (m["folder"] or "").lower():
                continue
            exists = Path(m["file_path"] or "").is_file()
            rows.append({"id": m["id"], "job_id": m["job_id"], "name": m["name"], "triangles": m["triangles"], "formats": m["formats"],
                         "folder": m["folder"], "file_path": m["file_path"], "source_image": m["source_image"], "exists": exists})
        return rows
    finally:
        database.close()


@tool("inspect_model", "Fast inspection of a .glb (no Blender needed): triangles, meshes, materials, texture count, skinned or not, real "
                       "size. For .fbx/.obj use blender_inspect.", schema(["path"], path=STR))
def inspect_model(args: dict) -> dict:
    return glb_info(args["path"])


def _unity_assets(project: str, dest: str) -> tuple[Path, Path]:
    root = Path(project).resolve()
    if not (root / "Assets").is_dir() or not (root / "ProjectSettings").is_dir():
        raise ValueError(f"{project} is not a Unity project (needs Assets and ProjectSettings)")
    target = (root / dest).resolve()
    if root / "Assets" != target and (root / "Assets") not in target.parents:
        raise ValueError("dest must be inside the project's Assets folder")
    return root, target


@tool("unity_import", "Copy finished models into a Unity project's Assets folder (model files + textures, original names kept) so the "
                      "Unity MCP can refresh, place and optimise them. Takes model files or job/atlas result folders. Never overwrites "
                      "unless overwrite=true. Returns the Assets/... paths to use with the Unity MCP.",
      schema(["unity_project", "paths"], unity_project=STR, paths={"type": "array", "items": STR},
             dest={"type": "string", "description": "Folder inside Assets, default Assets/_Art/3D/Meshy"}, overwrite=BOOL))
def unity_import(args: dict) -> dict:
    root, target = _unity_assets(args["unity_project"], args.get("dest") or "Assets/_Art/3D/Meshy")
    overwrite = bool(args.get("overwrite", False))
    copied, skipped = [], []

    def put(source: Path, subfolder: str = "") -> None:
        folder = target / subfolder if subfolder else target
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / source.name
        if destination.exists() and not overwrite:
            skipped.append(str(destination.relative_to(root)).replace("\\", "/"))
            return
        shutil.copy2(source, destination)
        copied.append(str(destination.relative_to(root)).replace("\\", "/"))

    for raw in args["paths"]:
        source = Path(raw)
        if source.is_dir():  # a job folder or an atlas folder: models + textures
            for model in sorted(p for p in source.iterdir() if p.suffix.lower() in MODEL_SUFFIXES):
                put(model)
            for texture in sorted(source.glob("*.png")) + sorted((source / "textures").glob("*.png")):
                put(texture, "Textures" if (source / "textures") in texture.parents else "")
        elif source.is_file():
            put(source)
        else:
            raise ValueError(f"not found: {raw}")
    return {"copied": copied, "skipped_existing": skipped,
            "next": "Call the Unity MCP to refresh assets (and set import settings / place the models); the .meta files are created by Unity."}
