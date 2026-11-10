# Meshy AI Studio

Unattended image -> textured ~10K-triangle GLB through the Meshy web app, driven by Playwright.
Claude Code / Codex call it through MCP; a headless runner (or the desktop app) does the work.

Flow per job: sign in (Google, TOTP supported) -> dismiss onboarding/tours -> upload -> Generate -> Texture 2K ->
Remesh 10K triangles -> download GLB via the meshy-ai-to-stl decoder -> `<export folder>/<image>_<timestamp>/` with `<image>.glb`, `<image>.fbx` (Blender, headless) and `textures/*.png` (Meshy's WebP converted). The export folder is set in the app (button on the main page) and defaults to `Export/`.
Accounts rotate automatically on quota (24 h rest), bad password, or verification prompts.

## Setup on a new machine
Requirements: Windows, Python 3.12+, Google Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`), git.

```
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Register the MCP server (use the absolute path of this folder):

```
claude mcp add meshy -- python <repo>\packages\meshy-studio\tools\meshy_mcp_server.py
codex mcp add meshy -- python <repo>\packages\meshy-studio\tools\meshy_mcp_server.py
```

Accounts: write a `.txt` with lines `email|password` or `email|password|recovery_email|totp_secret`, then call the
`import_accounts` tool with its path. Passwords go to the Windows credential store, never to files or MCP output.

## Use
`generate_model(image_path)` -> `job_id`; poll `job_status(job_id)` until `Completed`; `result_path` is the GLB.
Other tools: `list_jobs`, `list_accounts`, `list_exports`. The server starts `python -m app.runner` if nothing is running
(only one runner/app may hold `data/runner.lock`). See `docs/mcp-setup.md`.

Desktop app: `python -m app.main` (drop an image to queue it) or `tools\build_exe.bat` for a one-file exe.

## Local state (git-ignored, per machine)
`data/` (SQLite jobs + accounts), `profiles/` (browser sessions), `Export/` (GLBs), `docs/vendor/` (decoder), `dist/`, `build/`.

## Known limits
- Fresh Google accounts may demand phone/CAPTCHA; those accounts are marked "Needs verification" and skipped (never bypassed).
- Meshy's UI changes: selectors use `data-testid` where possible; on failure a screenshot is saved to `output/diagnostics/`.
- Free accounts need >= 30 credits per model (generate 20 + texture 10; remesh is free).

## App modules
## Modules
- **Generation queue** (page *Generation Queue*): drop/choose several images; previews, queue position, cancel one or
  many (the rest move up), retry. Running job stops at its next step. Retry with exponential backoff (30 s, 60 s, ... 10 min),
  max 2 retries; interrupted jobs are restored on restart.
- **Meshy accounts** (page *Accounts*): import `email|password[|recovery|totp]`, credit read from the Meshy sidebar
  (a model needs 30), automatic rotation, rest period after quota, "Use selected account" to pin one yourself,
  low-credit warning. No credit = the job is *Paused* (not failed); it resumes when an account is back or you pick one.
  The app never creates Meshy accounts.
- **Export** (main page): choose the export folder; each model gets `<name>_<time>/` with GLB, FBX (Blender, headless) and
  `textures/*.png`.
- **Purelymail** (page *Purelymail*): save the API token, track existing mailboxes (status, expiry warning), check IMAP
  login, read mail and show the verification code of messages you are waiting for.
  IMAP `imap.purelymail.com:993` (SSL) is from Purelymail's Technical Setup page. **The management API is not documented
  on the public site, so base URL (`https://purelymail.com/api/v0`), header (`Purelymail-Api-Token`) and endpoint names are
  unverified defaults** - check them against the documentation in your Purelymail account before relying on *Sync from API*.
- **Emergency stop** (top right): stops the running job at its next step, pauses the queue, closes all browsers.
  *Resume queue* continues.
- **Logs** (page *Logs*): `data/logs/app.log` (rotating, passwords/tokens redacted).

## MCP (Claude Code / Codex)
See `docs/mcp-setup.md`. Tools: `generate_model`, `job_status`, `list_jobs`, `cancel_jobs`, `list_accounts`,
`import_accounts`, `list_exports`.

