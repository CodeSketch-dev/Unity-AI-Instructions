"""Tripo tools: image -> textured GLB/FBX through the official Tripo API (needs the API key saved in the Tripo tab)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.mcp import context
from app.mcp.registry import BOOL, INT, STR, schema, tool
from app.security.credentials import KeyringCredentialStore
from app.tripo.options import DEFAULT_FACES, MAX_FACES, MIN_FACES, TripoOptions
from app.tripo.service import TripoService


def service() -> TripoService:
    return TripoService(context.DATA, context.export_dir, KeyringCredentialStore())


def _options(args: dict) -> TripoOptions:
    base = TripoOptions()
    return TripoOptions(args.get("model_version", base.model_version), int(args.get("face_limit", DEFAULT_FACES)), bool(args.get("texture", True)),
                        bool(args.get("pbr", False)), args.get("texture_quality", "detailed"), args.get("texture_alignment", "original_image"),
                        bool(args.get("smart_low_poly", True)), bool(args.get("quad", False)), True, "default",
                        bool(args.get("download", False))).normalized()


@tool("tripo_balance", "Tripo API credits left (one HD generation costs tens of credits).", schema())
def tripo_balance(args: dict) -> dict[str, Any]:
    return {"balance": service().balance()}


@tool("tripo_generate", "Queue Tripo image-to-3D jobs (official API, runs in this MCP process until finished; poll tripo_status). "
                        "Each job writes <export>/tripo/<name>_<time>/ with GLB, textures and FBX. Spends Tripo credits.",
      schema(["images"], images={"type": "array", "items": STR}, model_version=STR,
             face_limit={"type": "integer", "minimum": MIN_FACES, "maximum": MAX_FACES},
             texture=BOOL, pbr=BOOL, smart_low_poly=BOOL, quad=BOOL, download=BOOL,
             texture_quality={"type": "string", "enum": ["standard", "detailed"]},
             texture_alignment={"type": "string", "enum": ["original_image", "geometry"]}, wait=BOOL))
def tripo_generate(args: dict) -> dict[str, Any]:
    svc, opts = service(), _options(args)
    ids = [svc.submit(Path(image), opts) for image in args["images"]]
    if args.get("wait"):
        svc.wait_all()
    return {"job_ids": ids, "jobs": [svc.job(i) for i in ids]}


@tool("tripo_status", "Status of Tripo jobs (all recent when job_ids is omitted).", schema(job_ids={"type": "array", "items": INT}))
def tripo_status(args: dict) -> dict[str, Any]:
    svc, wanted = service(), set(args.get("job_ids") or [])
    jobs = [j for j in svc.jobs() if not wanted or j["id"] in wanted]
    return {"jobs": jobs[-30:]}
