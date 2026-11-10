# Test report

Date: 2026-11-10. Environment: Windows 11, Python 3.13, Google Chrome (system), Blender 5.2 (installed), no Meshy credits spent
by any of the tests below.

## Summary
| Suite | Result |
|---|---|
| Static audit (`python -m pyflakes app tools/meshy_mcp_server.py`) | clean (only an unused import in a test helper) |
| Automated tests (`test.bat` / `python -m pytest -q`) | **90 passed, 0 failed** |
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
  could fail an already-exported job (now a warning).

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
- Not done: IMAP against a real server (fake IMAP only); Purelymail API mock server (the API is disabled, nothing to mock);
  downloading a real `.meshy` file offline (verified live earlier).

## Phase D - real EXE GUI test (no mouse, no keyboard, no focus)
Driven through Windows UI Automation (Invoke/Select/Value) with PrintWindow screenshots (`output/gui_exe/*.png`). The exe is copied
to a temp folder and started with `MESHY_AUTOSTART=0` (no browser, no network, own database).
Checks (all passed): window opens (7.5 s cold start); each of the 7 pages shows its own controls; real Windows file dialog opens and
3 images are queued in one go; export folder unchanged by the picker; 3 jobs in SQLite; queue lists names and positions; Pause,
Resume, Cancel (the cancelled job leaves, the others move up: gate #1, crystal #2); Emergency Stop pauses the queue; Resume queue;
Settings shows Chrome/Blender checks; window closes; **reopen: jobs still listed, none lost or duplicated**.
Not driven: drag & drop from Explorer (needs the mouse), "Open in Explorer", the Meshy browser flow inside the exe.
Note: the first GUI test runs used the mouse and global keys and could have clicked other windows; that was stopped and removed.

## Phase E - end to end
- Mock E2E (unit): image -> queue -> account reserved -> run -> valid GLB -> Library record -> Completed, submitted exactly once, log
  lines written. Failure variants: quota, bad credentials, crash, timeout, cancel mid-run, restart mid-run.
- Live E2E: `python tools/live_e2e.py --image <png> --spend-credits [--account-id N]` (refuses to run without the flag). Last live
  runs of the earlier engine: jobs completed with GLB 9,365-9,536 triangles + 3 textures (see docs/owner-requests.md OR-028 and OR-031).
