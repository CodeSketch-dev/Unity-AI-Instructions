---
name: meshy-model-gen
description: "Generate textured ~10K-triangle GLB/FBX assets through the Meshy queue with email OTP, CAPTCHA handoff, crash safety and credit-aware rotation. Use when generating 3D models or operating Meshy Studio."
triggers: meshy, gen model, generate model, image to 3d, glb, fbx, 3d model from image, tao model 3d, gen model 3d, remesh, meshy mcp, tai model, purelymail, otp, captcha
---

# Meshy model generation (MCP)
- Tool lives in `packages/meshy-studio` (double-click `publish.bat` there to build `MeshyAIStudio.exe`; code is in its `source` folder, models go to `Export` beside the exe). Or run `source/setup.ps1`, register its MCP, then import authorized existing accounts. An email-only line (`user@example.com`) selects email OTP; legacy password rows are retained for migration but Google login is disabled.
- Per-job modes (always model Meshy 7): Topology (default) = Smart Topology tab + polygon count (100-30000, default 3000) -> Texture -> download, NO remesh (remesh caps at 10K tris); Automatic = Meshy's dense mesh -> Texture -> Remesh 10K -> download. Optional rig last (humanoid / four-legged / automatic). Rig selectors are from screenshots only (unverified live); a rig failure exports the unrigged model with a warning.
- Canonical paid flow is Generate -> Texture 2K -> Remesh 10K -> download GLB -> convert FBX and extract PNG textures. Never click Generate twice when the first click may have reached the server; reconcile the remote asset/task first.
- `generate_model(image_path)` (PNG/JPG/WEBP, <=20 MB) returns `job_id`. Poll `job_status` about every 60 s. `Completed` requires a non-empty GLB with triangles plus the export folder's FBX and PNG textures.
- Queue several images, but reserve one account per active job. Rotate only after confirmed credit exhaustion. A submitted job is never automatically requeued after a crash or downstream Texture/Remesh failure.
- Purelymail credentials/API tokens belong in Windows Credential Manager. Read OTP through readonly IMAP and reject an OTP that was already present before requesting the new code.
- If CAPTCHA appears, never solve or bypass it. Bring that Meshy tab forward once, retain the same browser/account/job, wait for the owner, and continue OTP afterward. Timeout pauses the job; Resume pins the same account instead of rotating.
- Run unit/integration/headless tests by default. Do not launch the desktop app or UI Automation while the owner works; CAPTCHA handoff is the explicit focus-stealing exception.
- Traps learned (Meshy Studio): (1) inspect the LIVE page before guessing selectors: open the logged-in profile with Playwright when the app is closed (read-only, no Generate click) and dump `innerText`/roles; e.g. the Meshy 7 / 2K options only exist while the Kết cấu (texture) `role=switch` is ON. (2) Failure snapshots must use a fixed path (a callable `export_dir` has no `.parent` and the bare `except` hid it). (3) Check which exe is running (`Win32_Process` start time/path): a locked exe means the build never replaced it and the owner is testing old code; only one instance owns the runner lock. (4) A non-login failure must never mark an account invalid or trigger creating mailboxes. (5) Poll the OTP mailbox in a background thread from the moment the code is requested so it is typed in right after the CAPTCHA. (6) A conditional-import patch skipped by a substring check caused a NameError that tests missed: add a test for every new branch with real values.
- Layout: `publish.bat` + `MeshyAIStudio.exe` + `Export/` beside a single `source/` folder; default Purelymail key and shared password are built-in fallbacks (obfuscated, not secure).
- MCP (source/tools/register_mcp.bat registers it for Claude + Codex): app_status/launch_app, generate_models with per-item polycount, wait_for_jobs (returns needs_owner on CAPTCHA), blender_* (decimate, convert, atlas = one texture + one material), unity_import, triangle_budget_guide. Keep the exe running; never bypass CAPTCHA.
- Tests must never open real windows: tests/conftest.py stubs os.startfile (a button-audit test once opened dozens of Explorer windows on the owner's desktop).
- A job `Pending` with error "No account with credits available; waiting" means every account is resting or out of credits: report it, do not loop.
- Failure diagnosis: screenshots of failed pages are in the tool's `output/diagnostics/`; look at the newest one before changing anything. Meshy changes its UI, tours and popups often; fix selectors in `app/automation/meshy_adapter.py` and add a test.
- Verify before reporting: tests pass, EXE builds, job is Completed, GLB triangles are near/below 10K, FBX exists and texture PNG count is non-zero. State clearly when live Meshy, IMAP, drag/drop or EXE GUI was not exercised.
- Rebuilding the exe: `tools\build_exe.bat` (tests, one-file build, copies `MeshyAIStudio.exe` to the project root).

## Texture crispness traps (measured on a 12.9k-tri Meshy pagoda)
- Do NOT use the FBX from `unity_import` directly: its UVs came out damaged (wrong colours, soft). Convert the GLB with `blender_atlas` `unwrap:"keep"` (one model, 2048) and bind the atlas to a URP/Lit material: correct, crisp.
- `unwrap:"smart"` shreds bevel-heavy Meshy meshes into thousands of tiny islands (texture gets worse even at 4K, even after weld). Use `keep` for such models; Meshy's own UVs are the better packing.
- A white render means no material texture bound (FBX has none); bind atlas.png to `_BaseMap` yourself.
