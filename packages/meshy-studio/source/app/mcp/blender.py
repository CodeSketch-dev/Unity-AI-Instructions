"""Headless Blender tools: inspect, decimate, convert, and pack several models into one texture atlas."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from app.automation.model_export import find_blender
from app.mcp import context
from app.mcp.registry import INT, STR, schema, tool

SCRIPTS = Path(__file__).resolve().parent / "blender_scripts"
MODEL_SUFFIXES = {".glb", ".gltf", ".fbx", ".obj"}


def blender_exe() -> Path:
    found = find_blender(context.ROOT)
    if found is None:
        raise RuntimeError("Blender was not found. Install Blender or set MESHY_BLENDER to blender.exe "
                           "(the app also downloads a portable copy the first time it exports an FBX).")
    return found


def run_blender(script: str, payload: dict, timeout: int = 900) -> dict[str, Any]:
    """Runs one of the bundled scripts and returns the JSON the script printed after MESHY_RESULT."""
    command = [str(blender_exe()), "--background", "--python", str(SCRIPTS / script), "--", json.dumps(payload)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for line in reversed((proc.stdout or "").splitlines()):
        if line.startswith("MESHY_RESULT "):
            return json.loads(line[len("MESHY_RESULT "):])
    tail = "\n".join(((proc.stdout or "") + (proc.stderr or "")).splitlines()[-12:])
    raise RuntimeError(f"Blender failed (exit {proc.returncode}):\n{tail}")


def _model_path(value: str) -> str:
    path = Path(str(value))
    if path.suffix.lower() not in MODEL_SUFFIXES or not path.is_file():
        raise ValueError(f"model file not found or unsupported: {value}")
    return str(path.resolve())


def _out_path(value: str | None, source: str, suffix: str, tag: str) -> str:
    if value:
        target = Path(value)
    else:
        src = Path(source)
        target = src.with_name(f"{src.stem}_{tag}{suffix or src.suffix}")
    if target.suffix.lower() not in {".glb", ".fbx"}:
        raise ValueError("output must end with .glb or .fbx")
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target.resolve())


@tool("blender_status", "Is headless Blender available, and which version/path.", schema())
def blender_status(args: dict) -> dict:
    try:
        exe = blender_exe()
    except RuntimeError as error:
        return {"available": False, "reason": str(error)}
    proc = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"available": True, "path": str(exe), "version": (proc.stdout or "").splitlines()[0] if proc.stdout else ""}


@tool("blender_inspect", "Open any .glb/.fbx/.obj headless and report triangles, mesh count, materials, texture sizes, UV layers, real-world "
                         "size (x,y,z) and bones.", schema(["input"], input=STR))
def blender_inspect(args: dict) -> dict:
    return run_blender("model_info.py", {"input": _model_path(args["input"])}, timeout=300)


@tool("blender_decimate", "Reduce a model to about target_tris triangles (Blender collapse decimate, UVs and texture kept). Writes a new "
                          ".glb/.fbx; the original is untouched. Use this for pieces that came out too dense.",
      schema(["input", "target_tris"], input=STR, target_tris=INT, output=STR))
def blender_decimate(args: dict) -> dict:
    source = _model_path(args["input"])
    target = int(args["target_tris"])
    if target < 4:
        raise ValueError("target_tris must be at least 4")
    return run_blender("decimate.py", {"input": source, "output": _out_path(args.get("output"), source, "", f"{target}tris"),
                                       "target_tris": target})


@tool("blender_convert", "Convert between .glb and .fbx (textures embedded/copied). Lossless: no decimation.",
      schema(["input", "output"], input=STR, output=STR))
def blender_convert(args: dict) -> dict:
    source = _model_path(args["input"])
    return run_blender("decimate.py", {"input": source, "output": _out_path(args["output"], source, "", "converted"), "target_tris": 0})


@tool("blender_atlas", "Pack several models into ONE shared texture atlas and ONE material (best for draw calls and memory). Each "
                       "input is {path, name?}; the original base colours are baked into atlas.png through packed UVs, and every "
                       "model is exported on its own (fbx by default) next to atlas.png + atlas_manifest.json. Static meshes only. "
                       "Texel density is equalised across models unless density='keep'.",
      schema(["inputs", "output_dir"],
             inputs={"type": "array", "items": {"type": "object", "required": ["path"], "properties": {"path": STR, "name": STR}}},
             output_dir=STR, atlas_size={"type": "integer", "enum": [512, 1024, 2048, 4096]},
             formats={"type": "array", "items": {"type": "string", "enum": ["fbx", "glb"]}},
             margin_px=INT, density={"type": "string", "enum": ["equalize", "keep"]},
             unwrap={"type": "string", "enum": ["smart", "keep"], "description": "smart (default): re-unwrap every mesh into few large clean islands, then bake the original look into them (Meshy UVs are shredded into hundreds of tiny islands that waste atlas space). keep: reuse Meshy UVs."},
             angle_limit={"type": "number", "description": "Smart unwrap angle in degrees (default 66; higher = fewer, larger islands)."}))
def blender_atlas(args: dict) -> dict:
    inputs = []
    seen: set[str] = set()
    for item in args["inputs"]:
        path = _model_path(item["path"])
        name = "".join(c if c.isalnum() or c in "-_" else "_" for c in (item.get("name") or Path(path).stem)) or "model"
        while name in seen:
            name += "_2"
        seen.add(name)
        inputs.append({"path": path, "name": name})
    if len(inputs) < 1:
        raise ValueError("give at least one model")
    output = Path(args["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    return run_blender("atlas.py", {"inputs": inputs, "output_dir": str(output.resolve()),
                                    "atlas_size": int(args.get("atlas_size", 2048)), "formats": args.get("formats") or ["fbx"],
                                    "margin_px": int(args.get("margin_px", 8)), "density": args.get("density", "equalize"),
                                    "unwrap": args.get("unwrap", "smart"), "angle_limit": float(args.get("angle_limit", 66))},
                       timeout=1800)
