# Implementation status

Date: 2026-11-10. Framework: **Python 3.13 + PySide6 (Qt)** desktop app, Playwright + system Chrome for the Meshy web app,
SQLite (WAL), `keyring` (Windows Credential Manager) for secrets, PyInstaller one-file exe. It is **not** WPF/.NET and was not
rewritten to be.

Legend: **WORKING** = implemented and verified as stated; **PARTIAL** = implemented, part verified; **MOCK** = only exercised
with fakes; **BROKEN** = known failing; **UNTESTED** = implemented, never exercised against the real thing; **BLOCKED** =
cannot be done (technical/policy reason); **NOT IMPLEMENTED**.

Important: the Meshy browser flow (login, onboarding, upload, generate, texture, remesh, export) was verified **live in earlier
sessions, before the job engine was restructured in this session** (one account per job, no automatic re-submission,
concurrency). The restructured engine has been verified with fakes and with the real EXE UI, but **not live against Meshy**
(that spends credits; `tools/live_e2e.py --spend-credits` is ready, see TEST_REPORT.md).

| Area | Feature | Status | Evidence |
|---|---|---|---|
| Engine | Image validation (type, size, empty, missing) | WORKING | unit tests |
| Engine | Queue state machine, FIFO order, cancel one/many (others move up), pause/resume, retry, re-queue to the back | WORKING | unit tests + real EXE GUI test |
| Engine | One account per job, no account runs two jobs at once | WORKING | unit tests (fake workers) |
| Engine | Idempotency: a job already submitted to Meshy is never auto-retried or re-submitted after a restart | WORKING (logic) | unit tests; live behaviour UNTESTED |
| Engine | Retries: exponential backoff 30 s..10 min, max 2, only before submission | WORKING | unit tests |
| Engine | Completed only if the output GLB exists and parses with >0 triangles; Library record written | WORKING | unit tests |
| Engine | Crash/restart recovery (unsubmitted work re-queued, submitted work marked Failed for review) | WORKING | unit tests + real EXE restart (3 jobs survive) |
| Engine | Concurrency 1..3 (thread per slot, own browser driver) | MOCK | unit test with fake workers; never run with real browsers |
| Engine | Job time limit, cancel probe at every step boundary | WORKING | unit tests |
| Engine | Emergency Stop: stops new work, cancels running local jobs at next step, pauses queue, closes browsers | WORKING (local only) | unit tests + real EXE; does **not** cancel a Meshy task already submitted |
| Meshy web flow | Google login (password), TOTP, onboarding/tour/check-in dismissal | PARTIAL | live earlier; TOTP only with a fake page; some accounts blocked by their domain's 2-step policy |
| Meshy web flow | Credit read from the sidebar; unknown never treated as 0; pre-check (needs 30); refresh after submit and after export | WORKING (read) / UNTESTED live after refactor | live earlier (115, 75); unit tests for the logic |
| Meshy web flow | Upload, Generate, Texture 2K, Remesh 10K, GLB download via decoder, PNG, FBX (Blender) | WORKING (live earlier) / UNTESTED live after refactor | live earlier; Blender + PNG verified again with real Blender in tests |
| Meshy web flow | Official Meshy API | NOT IMPLEMENTED / BLOCKED | needs a paid API key; no endpoint is guessed. Whether Meshy permits UI automation of its web app is **unverified** |
| Accounts | Import, rotation (least recently used), pin one account, rest after quota (24 h), invalid/needs-verification flags | WORKING | unit tests |
| Accounts | Auto-creating Meshy accounts to renew free credit | NOT IMPLEMENTED (by decision) | not requested; the app never creates Meshy accounts |
| Purelymail | Track existing mailboxes, expiry warning, IMAP login check, read mail, find OTP | MOCK | unit tests with a fake IMAP; **never run against a real mailbox** (no test mailbox credentials provided) |
| Purelymail | Management API (list/create users) | IMPLEMENTED, LIVE UNVERIFIED | disabled unless the user supplies official endpoint configuration; create requires an explicit payload template; no defaults are guessed |
| Purelymail | Auto-clean of expired mailboxes | NOT IMPLEMENTED | would need the (unverified) management API |
| UI | 7 pages: Generate, Queue, Accounts, Purelymail, Library, Settings, Logs | WORKING | real EXE: all 7 open (27/27 GUI checks) |
| UI | Generate: multi-select file picker, instant queue, thumbnails, rejection list, export folder (persisted) | WORKING | real EXE picker + unit tests |
| UI | Generate: drag & drop from Explorer | PARTIAL | in-process drop test only; the real OLE drag was not driven (needs the mouse) |
| UI | Queue: thumbnail, name, status, progress, account, time, pause/resume/cancel/retry (blocked if already submitted) | WORKING | real EXE + unit tests |
| UI | Library: records, thumbnail, formats, size, search/filter, open file/folder, remove record without deleting files | WORKING (logic) / UNTESTED (real Explorer open) | unit tests with a fake opener |
| UI | Settings: parallel jobs, time limit, retries, output folder, environment checks (Chrome/Blender/decoder), IMAP check | WORKING | unit tests; persisted across restart |
| UI | Logs: level + text filter, export, redaction of passwords/tokens/cookies/OTP | WORKING | unit tests |
| Data | SQLite WAL, versioned migrations (`PRAGMA user_version`), locked access, legacy DB upgrade | WORKING | unit tests |
| Security | Secrets in Windows Credential Manager (not plaintext in files/logs); log redaction | WORKING | unit tests |
| Security | `accounts.txt` in the team package holds plaintext passwords until first start | PARTIAL | by owner decision; see KNOWN_LIMITATIONS |
| Delivery | `run.bat`, `publish.bat`, `test.bat`, one-file x64 exe, team package, MCP server | WORKING | exe built and driven by the GUI test |
| Delivery | Auto-download of decoder / browser / Blender when missing | PARTIAL | decoder download verified live; browser and Blender downloads UNTESTED |

Unused / legacy code: `app/ui/browser_host.py` (old embedded-browser widget, no longer wired), `Scheduler` priority/least-busy
policies (only round robin and manual are used), `tools/legacy/*` (one-off scripts from earlier sessions with hard-coded account
paths; not part of the product). Test hooks in production code: `MESHY_NO_SPAWN`, `MESHY_CREDENTIALS=memory` (MCP server),
`MESHY_AUTOSTART=0` (app).
