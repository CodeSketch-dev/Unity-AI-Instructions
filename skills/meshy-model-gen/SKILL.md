---
name: meshy-model-gen
description: "Generate a textured ~10K-triangle GLB from an image through the Meshy MCP (packages/meshy-studio): generate_model, job_status, accounts, quota rotation. Use when asked to gen/make a 3D model from an image or to set up the Meshy tool."
triggers: meshy, gen model, generate model, image to 3d, glb, 3d model from image, tao model 3d, gen model 3d, remesh, meshy mcp, tai model
---

# Meshy model generation (MCP)
- Tool lives in `packages/meshy-studio` of this repo. First time on a machine: run its `setup.ps1`, register the MCP (`claude mcp add meshy -- python <repo>\packages\meshy-studio\tools\meshy_mcp_server.py`), import accounts with `import_accounts(file_path)`. Details in its README.
- To make a model: `generate_model(image_path)` (png/jpg/webp, <= 20 MB, use forward slashes or a JSON-escaped path) -> `job_id`. Poll `job_status(job_id)` every ~60 s (a job takes 3-8 min); done when `status` is `Completed`, then `result_folder` (a per-model sub-folder of the export folder chosen in the app, default `Export/`) holds `<name>.glb`, `<name>.fbx` and `textures/*.png` (basecolor, normal, metallic_roughness); `files` lists them and `result_path` is the GLB. FBX needs Blender (found automatically, or downloaded once).
- Queue: several images can be queued; `cancel_jobs([ids])` cancels queued jobs (others move up) and stops a running one at its next step; `list_jobs` shows `queue_position`. A job `Paused` means no account has the 30 credits a model needs: report it, the owner picks another account in the app.
- The server starts the headless runner itself; do not drive the browser or Meshy UI by hand, and never type account credentials anywhere. Import accounts from a file only.
- `list_accounts` shows health: `Quota Limited` rests 24 h, `Needs verification` / `Invalid credentials` need the owner (Google CAPTCHA or phone, wrong password). Tell the owner which accounts and stop; never try to bypass a CAPTCHA.
- A job `Pending` with error "No account with credits available; waiting" means every account is resting or out of credits: report it, do not loop.
- Failure diagnosis: screenshots of failed pages are in the tool's `output/diagnostics/`; look at the newest one before changing anything. Meshy changes its UI, tours and popups often; fix selectors in `app/automation/meshy_adapter.py` and add a test.
- Verify a result before using it: triangle count (~10K) and texture images > 0 (the exporter checks this; `inspect_glb`), then import into the project.
- Rebuilding the exe: `tools\build_exe.bat` (tests, one-file build, copies `MeshyAIStudio.exe` to the project root).
