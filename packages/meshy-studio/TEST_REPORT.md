# Test report

Date: 2026-11-10. Environment: Windows 11, Python 3.13, Google Chrome (system), Blender 5.2 (installed), no Meshy credits spent
by any of the tests below.

## Summary
| Suite | Result |
|---|---|
| Static audit (`python -m pyflakes app tools/meshy_mcp_server.py`) | clean (only an unused import in a test helper) |
| Automated tests (`test.bat` / `python -m pytest -q`) | **99 passed, 0 failed** |
| Real-EXE GUI test (`python tools/gui_exe_test.py`) | **27 passed, 0 failed** |
| Live end-to-end against Meshy with the restructured engine | **NOT RUN** (spends credits; needs the owner's permission) |
| Live IMAP against a real mailbox | **NOT RUN** (no test mailbox credentials) |

## Phase A - static audit
- pyflakes: no unused code in `app/` after cleanup; one-off probe scripts were deleted, older one-off scripts moved to `tools/legacy/`.
- Credential leakage: log redaction covers passwords, tokens/API keys/TOTP secrets, cookies, bearer headers and OTP codes (unit-tested,
  including the exported log). No secret is written to the SQLite file; passwords live in Windows Credential Manager.
- Concurrency review: one shared SQLite connection, every read/write holds one re-entrant lock; claiming a job is one transaction
  (60 jobs claimed by 6 threads: each exactly once). Accounts are reserved under a lock. A found race: round-robin skipped accounts
  when one dropped out of the list - fixed (least-recently-used) with a test.
- Bugs found by the new tests and fixed: Blender timeout used to abort packaging (now a warning, GLB/PNG kept); a crashing packager
  could fail an already-exported job (now a warning); delayed Meshy cards could cause a second Generate click (now exactly one);
  submitted jobs could be manually requeued without server reconciliation (now blocked); worker shutdown leaked thread-owned Playwright
  drivers (now bounded and cleaned in the owner thread).

## Phase B - unit tests (examples)
Queue state machine, cancel/pause/resume/retry/re-queue order, backoff and bounded retries, no auto-retry after submission, restart
recovery (submitted job not re-queued), credit unknown vs 0, credit refresh points, pre-check below 30, account pinning and rotation,
migrations from a legacy database, WAL, image validation, emergency stop, deadline/cancel at step boundaries, settings persistence,
log filter/export/redaction, Library filter and "remove record keeps the file".

## Phase C - integration
- Local fake Meshy page served over HTTP and driven by **real Chrome** (headless): credit read, card counting, "new asset appeared"
  wait, progress wait, tour popup dismissal, hidden-input upload.
- BrowserManager lifecycle: launches a real profile window and **closes it completely** (no Chrome process left on that profile).
- **Real Blender 5.2** converts a generated GLB to FBX + PNG (binary FBX signature, embedded PNG, size > 0).
- SQLite persistence across close/reopen; legacy database migration.
- Purelymail API list/create/modify paths match the official OpenAPI contract and are covered with injected transport, idempotency,
  post-timeout reconciliation, server confirmation, default-password and credential-safety tests. Live API created `codesketch000002`,
  `listUser` confirmed both numbered mailboxes, and both passed real IMAP login after the password update.
  A headless web login for `codesketch000002@purelymail.com` also reached the authenticated Purelymail Inbox; the browser was closed afterward.
  downloading a real `.meshy` file offline (verified live earlier).

## Phase D - real EXE GUI test (no mouse, no keyboard, no focus)
Driven through Windows UI Automation (Invoke/Select/Value) with PrintWindow screenshots (`output/gui_exe/*.png`). The exe is copied
to a temp folder and started with `MESHY_AUTOSTART=0` (no browser, no network, own database).
Do not run this harness while the owner is using the workstation: despite no mouse/keyboard calls, Windows UI Automation can still disturb
focus/cursor state. Normal development verification must use unit/integration/headless tests and must not launch the app.
Checks (all passed): window opens (10.0 s cold start); each of the 7 pages shows its own controls; real Windows file dialog opens and
3 images are queued in one go; export folder unchanged by the picker; 3 jobs in SQLite; queue lists names and positions; Pause,
Resume, Cancel (the cancelled job leaves, the others move up: gate #1, crystal #2); Emergency Stop pauses the queue; Resume queue;
Settings shows Chrome/Blender checks; window closes; **reopen: jobs still listed, none lost or duplicated**.
Not driven: drag & drop from Explorer (needs the mouse), "Open in Explorer", the Meshy browser flow inside the exe.
Explorer-style `text/uri-list` drop is covered in-process with a real Qt `QDropEvent` (two images queued, invalid file rejected).
The first rebuilt EXE exposed a QtCore startup failure: PyInstaller had captured an incompatible ICU 78 from the build environment.
The spec now excludes foreign ICU DLLs, the archive contains none, and the rebuilt EXE passed all 27 GUI checks.
The Purelymail-ready rebuild also passed all 27 GUI checks (7.6 s cold start, 9.5 s reopen); SHA-256
`9CB7F90378A0E70E8DD50866AB79E9071DAAAF1763BB5AC7DDDB1763AFC9F382`.
Latest headless-verified build after live Purelymail provisioning: 104 tests passed; SHA-256
`8058992A60C8F2BDCD3F9BC752D1FE2E412EE67B4E70B8F4337D79E6FDBEBF1D`. No GUI/UIA test was run, per owner request.
Meshy email-OTP update: 106 tests passed, covering email-only import, Purelymail OTP retrieval and worker routing that never starts Google.
No live Meshy OTP was submitted for `000002`, because the unified sign-in form can create a new account and the owner prohibited automatic signup.
CAPTCHA manual handoff and Google-disable update: 108 tests passed. CAPTCHA is detected in embedded frames, brings the Meshy tab forward once,
waits up to five minutes for manual completion, then resumes fresh-OTP polling. Automatic CAPTCHA solving/bypass is not implemented.
The old running build completed job 12 through legacy account 3 before replacement: `Export/Pull_20261110_142418/Pull.glb`.
CAPTCHA account-pinning regression: manual verification pauses the job on its original account, never releases/rotates the browser,
and Resume pins the same account. Full suite: 108 passed. Updated EXE staged as `MeshyAIStudio.next.exe` while the old app holds the main EXE.
Note: the first GUI test runs used the mouse and global keys and could have clicked other windows; that was stopped and removed.

## Phase E - end to end
- Mock E2E (unit): image -> queue -> account reserved -> run -> valid GLB -> Library record -> Completed, submitted exactly once, log
  lines written. Failure variants: quota, bad credentials, crash, timeout, cancel mid-run, restart mid-run.
- Live E2E: `python tools/live_e2e.py --image <png> --spend-credits [--account-id N]` (refuses to run without the flag). Last live
  runs of the earlier engine: jobs completed with GLB 9,365-9,536 triangles + 3 textures (see docs/owner-requests.md OR-028 and OR-031).
- Reconciled continuation after a live Texture failure: job 11's existing base task was selected from Assets (no second Generate), then
  Texture and Remesh 10K completed. Export: `Export/Pull_20261110_123712/Pull.glb`, 9,008 triangles, 3 PNG textures and FBX. The account
  retained 95 credits, so rotation did not occur. Regression tests cover selecting the newest asset and full 10-card list replacement.
