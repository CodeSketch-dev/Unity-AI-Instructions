"""Read-only guidance tools: the recommended workflow and triangle budgets, so the AI can decide detail per object."""
from __future__ import annotations

from app.mcp.registry import schema, tool, STR

BUDGETS = [
    {"role": "hero", "examples": "main gate, centrepiece, player-facing landmark", "polycount": "12000-30000"},
    {"role": "large_prop", "examples": "big building, large statue, big machine", "polycount": "5000-12000"},
    {"role": "medium_prop", "examples": "lantern, chest, tree, vehicle", "polycount": "1500-5000"},
    {"role": "small_prop", "examples": "rock, barrel, flower, crate, pickup", "polycount": "300-1500"},
    {"role": "tiny_or_distant", "examples": "pebble, grass tuft, far background item", "polycount": "100-400"},
]


@tool("triangle_budget_guide", "Triangle budgets per object role for a low-end mobile game. Pass `role` for one row. These are starting points: "
                               "give detail where the player looks, save it elsewhere, then check the total with inspect_model.",
      schema(role=STR))
def triangle_budget_guide(args: dict) -> dict:
    rows = [r for r in BUDGETS if not args.get("role") or r["role"] == args["role"]]
    return {"budgets": rows, "meshy_range": "100-30000 triangles per model in topology mode (remesh in automatic mode is capped at 10000)",
            "mobile_rule": "Aim for a whole scene far below 100K visible triangles; merge props into one atlas to save draw calls "
                           "(blender_atlas), and decimate (blender_decimate) anything that came out denser than needed."}


@tool("workflow_guide", "How to use this MCP end to end (generate, wait, post-process, hand off to Unity). Read once at the start.", schema())
def workflow_guide(args: dict) -> dict:
    return {"steps": [
        "1. app_status: if app_running is false call launch_app (the visible window is needed: the owner solves any CAPTCHA).",
        "2. Concept: use the owner's images, or make concept art first (e.g. with Codex image generation) and save PNG/JPG/WebP files.",
        "3. generate_models: one item per object, with a polycount per object (triangle_budget_guide). mode=topology gives exact "
        "triangles and a texture in one pass; mode=automatic gives Meshy's dense mesh remeshed to 10K.",
        "4. wait_for_jobs (repeat while timed_out). If needs_owner is not empty, tell the owner to solve the CAPTCHA in the Meshy window, "
        "then call resume_jobs. Never try to bypass a CAPTCHA.",
        "5. Check each result with job_status / inspect_model (triangles, size). Too dense: blender_decimate. Wrong format: blender_convert.",
        "6. Many props for one scene: blender_atlas packs them into ONE texture and ONE material, each model exported separately.",
        "7. unity_import copies the files into the project's Assets; then use the Unity MCP to refresh, place and set import settings.",
        "Credits: each model costs about 15 (topology, textured) or 30 (automatic). Failed jobs that were already submitted are never "
        "retried automatically (retry_jobs refuses them): ask the owner."]}
