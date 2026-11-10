# Meshy MCP

One server for Claude Code and Codex: it drives the **running** Meshy AI Studio app (the owner solves CAPTCHAs in its window),
headless Blender, and a file hand-off into Unity.

## Register (once per machine)
Double-click `source\tools\register_mcp.bat` (registers `meshy` for the claude and codex CLIs it finds), then restart the sessions.
Manual form: `claude mcp add --scope user meshy -- python <...>\source\tools\meshy_mcp_server.py` (same for `codex mcp add`).

## Tools
| Area | Tools |
|---|---|
| App | `app_status` (blockers, credits, captcha waits), `launch_app` |
| Generate | `generate_model`, `generate_models` (each item has its own `mode` / `polycount` / `rig`), `wait_for_jobs`, `job_status`, `list_jobs` |
| Control | `cancel_jobs`, `pause_jobs`, `resume_jobs` (after a CAPTCHA), `retry_jobs` (refuses jobs already submitted to Meshy) |
| Accounts | `list_accounts`, `import_accounts` |
| Library | `list_models`, `inspect_model` (GLB, no Blender) |
| Blender (headless) | `blender_status`, `blender_inspect`, `blender_decimate`, `blender_convert`, `blender_atlas` |
| Unity | `unity_import` (copies models + textures into `Assets/...`; use the Unity MCP to refresh and place) |
| Guidance | `workflow_guide`, `triangle_budget_guide` |

## Typical flow (the AI decides the detail per object)
1. `app_status` -> `launch_app` if the exe is not running.
2. Images from the owner, or concept art made with Codex image generation.
3. `generate_models`: hero pieces 12000-30000 triangles, props 300-5000, background 100-400 (`triangle_budget_guide`).
4. `wait_for_jobs`; if `needs_owner` is set, ask the owner to solve the CAPTCHA, then `resume_jobs`.
5. `inspect_model` / `blender_decimate` to hit the budget; `blender_atlas` packs many props into ONE texture + ONE material.
6. `unity_import`, then the Unity MCP to refresh, place and set import settings.

`blender_atlas` re-unwraps every mesh (`unwrap: smart`, default) because Meshy's own UVs are shredded into hundreds of tiny islands,
bakes the original colours into one shared `atlas.png` and exports each model alone next to `atlas_manifest.json`.

Secrets never appear in tool output; `import_accounts` takes a file path. The exe must be running for jobs to execute.
