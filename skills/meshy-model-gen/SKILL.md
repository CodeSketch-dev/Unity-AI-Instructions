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
- A job `Pending` with error "No account with credits available; waiting" means every account is resting or out of credits: report it, do not loop.
- Failure diagnosis: screenshots of failed pages are in the tool's `output/diagnostics/`; look at the newest one before changing anything. Meshy changes its UI, tours and popups often; fix selectors in `app/automation/meshy_adapter.py` and add a test.
- Verify before reporting: tests pass, EXE builds, job is Completed, GLB triangles are near/below 10K, FBX exists and texture PNG count is non-zero. State clearly when live Meshy, IMAP, drag/drop or EXE GUI was not exercised.
- Rebuilding the exe: `tools\build_exe.bat` (tests, one-file build, copies `MeshyAIStudio.exe` to the project root).
