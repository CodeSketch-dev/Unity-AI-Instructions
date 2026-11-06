# Meshy AI Studio — Design Specification

## Goal

Create a Windows desktop application where an authorized user can securely manage Meshy accounts/API credentials, submit images to Meshy's real Image-to-3D service, persist and control a generation queue, preview/download results, and recover work after restart.

## Rulings

- **Ruling: browser automation is the only Meshy production backend.** The app uses isolated persistent Playwright profiles and observed accessible roles/text from Meshy Web. Google OAuth, MFA, CAPTCHA, and device verification remain user-controlled; the app never accepts or logs Google credentials.
- **Ruling: API credentials and account secrets live only in Windows Credential Manager/keyring.** SQLite stores non-secret account metadata and credential references.
- **Ruling: one local worker executes jobs serially by default.** This avoids accidental credit bursts; scheduler policies decide among eligible authorized accounts but never rotate to evade quotas.
- **Ruling: PySide6 native widgets plus QSS.** This minimizes packaging risk while delivering a modern dark UI.
- **Ruling: GLB preview uses trimesh-rendered turntable thumbnails.** Native interactive OpenGL embedding is optional complexity; users can open the file externally from the library.

## Architecture

- `app/core/database.py`: schema, migrations, account/job/model persistence, restart recovery.
- `app/security/credentials.py`: keyring facade with explicit secret names and redaction.
- `app/core/account_manager.py`: parse/import/deduplicate accounts and coordinate secret storage.
- `app/core/scheduler.py`: manual, priority, round-robin, and least-busy selection with reasons and eligibility gates.
- `app/automation/browser_manager.py`: per-account Playwright persistent profile lifecycle.
- `app/automation/google_login.py`: manual-first Google/Meshy login state machine; optional local TOTP generation only for user-owned secrets.
- `app/automation/meshy_adapter.py`: conservative browser adapter using verified accessible names for Model → Image-to-3D, upload, login-state classification, and manual Google handoff; no API endpoint integration.
- `app/core/job_manager.py`: background queue worker, retry/pause/cancel/recovery, downloads, and UI-safe events.
- `app/ui/*`: sidebar shell, chat intake, accounts, queue, library, settings, and logs.

## Data and security

- SQLite stores account email, priority, profile directory, status, authorization flags, jobs, and model metadata.
- Password, TOTP secret, and API key values are stored under distinct keyring service keys; they never enter SQLite or application logs.
- Persistent browser state remains in isolated `profiles/account_<id>` directories. Logs redact bearer tokens, passwords, cookies, and TOTP values.
- “Delete account data” removes database metadata, keyring entries, and the specific account profile after confirmation.

## Real Meshy integration

Verified against Meshy Web on 2026-11-06:

- Workspace exposes radio `Mô hình`, tab `Hình ảnh thành 3D`, image chooser text `Nhấp / Kéo & Thả / Dán Hình ảnh`, and button `Tạo ra`.
- Login modal exposes `Tiếp tục với Google`; password attempt returned `Email hoặc mật khẩu không chính xác` for the supplied test account.
- OAuth completion and live generation remain unverified because this environment cannot complete the Google popup/session handoff.

## UX

- Default page is AI 3D Chat with drop/paste/file image intake, optional note, and task cards.
- Sidebar pages: AI 3D Chat, Accounts, Generation Queue, Model Library, Settings, Logs.
- Queue and account actions are explicit; quota-limited jobs stop and require user action.
- Status messages distinguish waiting for login, generating, downloading, completed, failed, paused, and quota-limited.

## Edge cases

- Invalid/duplicate account lines are reported without exposing secrets.
- Keyring unavailable: import fails closed with an actionable error.
- App restart: active jobs recover to Pending or resume polling when a Meshy task ID exists.
- API 401/403 marks relogin/credential required; 402/429 marks quota limited and does not switch accounts automatically.
- Network errors retry with a bounded count and retain the job.
- Signed model URLs are downloaded promptly; failures retain the remote task metadata for retry.

## Acceptance criteria

1. `pytest` passes with tests for 10-account import, invalid rows, deduplication, secret non-persistence/redaction, profile isolation, all scheduler policies, job restart recovery, quota mapping, API request/response mapping, and responsive worker signaling.
2. SQLite contains no imported password or TOTP secret in file bytes after import.
3. Each account receives a unique resolved profile directory.
4. App starts via `run.bat`; all six pages are reachable; image drop/paste/file enqueue works without blocking the GUI.
5. Web adapter uses only observed accessible names and can open a manual Google flow without accepting credentials; live OAuth/generation is reported unverified until a user completes the flow in a headed profile.
6. `build.bat` produces a PyInstaller build when dependencies are installed; a source ZIP is produced.
7. No real credentials or account data ship in the sample file or archive.

