# Meshy AI Studio

Windows desktop app (Python + PySide6) that turns images into textured ~10K-triangle GLB/FBX/PNG with the Meshy
web app, plus a Purelymail mailbox manager. Claude Code / Codex drive it through an MCP server.

## Honest status
See `IMPLEMENTATION_STATUS.md` (what works, what is mock/untested/blocked), `TEST_REPORT.md` (90 tests + 27 real-EXE GUI checks) and
`KNOWN_LIMITATIONS.md`. Not claimed production-ready: the restructured engine has not been run live against Meshy yet.

## Run / build
- `run.bat` - start from source (`pip install -r requirements.txt` first, Python 3.12+, Chrome installed).
- `test.bat` - static check + all automated tests. `python tools\gui_exe_test.py` - drives the built exe (UI Automation only: no mouse/keyboard/focus).
- `..\publish.bat` (one level up, next to the exe) - installs deps, tests, builds the one-file exe to `..\MeshyAIStudio.exe`. Models default to `..\Export`; data and profiles stay in this `source` folder.
- `python tools\live_e2e.py --image X --spend-credits` - ONE real job against Meshy (spends ~30 credits; refuses without the flag).
- `tools\make_team_package.bat` - small shareable folder (exe + accounts.txt + README).

## Modules
- **Generation queue** (page *Generation Queue*): drop/choose several images; previews, queue position, cancel one or
  many (the rest move up), retry. Running job stops at its next step. Retry with exponential backoff (30 s, 60 s, ... 10 min),
  max 2 retries, only for failures BEFORE the job was submitted to Meshy (a submitted job is never re-submitted automatically);
  interrupted jobs are restored on restart. Up to 3 parallel jobs (Settings), each on its own account.
- **Meshy accounts** (page *Accounts*): import a single `email` for Purelymail OTP login, or legacy
  `email|password[|recovery|totp]` for Google login. Email-only accounts never fall back to Google.
  (a model needs 30), automatic rotation, rest period after quota, "Use selected account" to pin one yourself,
  low-credit warning. No credit = the job is *Paused* (not failed); it resumes when an account is back or you pick one.
  The app never creates Meshy accounts.
- **Export** (main page): choose the export folder; each model gets `<name>_<time>/` with GLB, FBX (Blender, headless) and
  `textures/*.png`.
- **Purelymail** (page *Purelymail*): save the API token, track mailboxes (status, expiry warning), create a mailbox when the
  official API token is configured, check IMAP
  login, read mail and show the verification code of messages you are waiting for.
  IMAP `imap.purelymail.com:993` (SSL) is from Purelymail's Technical Setup page. The management API request schema is not
  bundled defaults follow Purelymail's published OpenAPI contract: header `Purelymail-Api-Token`,
  `POST /api/v0/listUser`, and `POST /api/v0/createUser`. Tokens and mailbox passwords stay in Windows Credential Manager.
- **Emergency stop** (top right): stops the running job at its next step, pauses the queue, closes all browsers.
  *Resume queue* continues.
- **Logs** (page *Logs*): `data/logs/app.log` (rotating, passwords/tokens redacted).

## MCP (Claude Code / Codex)
See `docs/mcp-setup.md`. Tools: `generate_model`, `job_status`, `list_jobs`, `cancel_jobs`, `list_accounts`,
`import_accounts`, `list_exports`.

## Data (per machine, never commit)
`data/` (SQLite, settings, logs), `profiles/` (browser sessions), `Export/`, `docs/vendor/` (decoder, auto-downloaded).
Secrets live in the Windows credential store.
