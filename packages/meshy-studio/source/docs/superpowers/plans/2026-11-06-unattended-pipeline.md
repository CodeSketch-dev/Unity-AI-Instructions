# Unattended Pipeline + MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native) to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Owner buys Gmail accounts, imports the list once, then drops an image in the app (or calls an MCP tool from Claude Code/Codex) and the model is generated with no human or AI in the loop, rotating accounts when credits run out.

**Architecture:** SQLite `jobs` table is the single queue. One `PipelineService` (no Qt) claims PENDING jobs and drives `MeshyWebWorker.run_with_rotation`, persisting job and account state. The GUI embeds it; `python -m app.runner` runs it headless; the MCP server only enqueues/reads and spawns the runner if none holds the lock file. Account health (quota cooldown, bad password, needs verification) is persisted so rotation survives restarts.

**Tech Stack:** Python 3.12, PySide6, Playwright, sqlite3, keyring, stdlib TOTP (no new deps), pytest.

**Spec:** Owner messages OR-017, OR-018 in `docs/owner-requests.md`.

## Global Constraints

- Secrets only via `CredentialStore`; never logged, never in MCP output or job `error` text.
- Sequential: one Meshy job at a time (OR-006). Contexts stay open (OR-005).
- Rotate only on quota / not-logged-in / manual-verification / invalid-credentials; NOT on ordinary failures (existing test `test_worker_does_not_rotate_on_ordinary_error` stays green).
- Quota cooldown: 24 h. Invalid-credentials accounts: `authorized=False` until owner re-enables.
- Money-spending/paid-upgrade controls are never clicked.

## Review Focus

- Empty account pool / all accounts exhausted: job must end `Quota Limited`/`Failed` with a clear error, not hang or loop.
- App killed mid-job: on restart `recover_jobs()` returns it to Pending, not stuck Generating.
- Two runners started (GUI + MCP spawn): second must refuse via lock file.
- Dropped file that is not an image / >20 MB / missing: rejected at enqueue.
- TOTP secret with spaces/lowercase; clock-step boundary.
- Google challenge with no TOTP stored: account marked `Needs verification`, rotation continues.

---

### Task 1: TOTP + 2FA step in Google login
**Files:** Create `app/security/totp.py` (done); Modify `app/automation/google_login.py`; Test `tests/test_totp.py`, `tests/test_google_login.py`
**Interfaces:** Produces `totp_now(secret: str, *, at: float|None=None, digits=6, step=30) -> str`; `GoogleOAuthLogin.attempt` unchanged signature.
- [ ] Test `test_totp_rfc6238_vector`: secret `GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ` (ASCII "12345678901234567890"), `at=59`, digits=8 → `"94287082"`; `test_totp_accepts_spaces_lowercase`.
- [ ] Test `test_google_login_enters_totp_when_challenge_and_secret_present` using the fake page in the existing test file: store `totp`; assert code field filled with `totp_now(...)` and outcome AUTHENTICATED.
- [ ] Test `test_google_login_manual_when_challenge_without_totp`.
- [ ] Implement: in `attempt`, when `_challenge_visible` and `credentials.get(key,"totp")`, click "Try another way"→authenticator option if no `input[name=totpPin]`/`input[type=tel]` visible, fill code, Next; else keep returning MANUAL_VERIFICATION.
- [ ] Run `python -m pytest tests/test_totp.py tests/test_google_login.py -q` → pass.

### Task 2: Account health persistence
**Files:** Modify `app/core/database.py`, `app/core/models.py`; Test `tests/test_database_jobs.py`
**Interfaces:** Produces `Account.cooldown_until: str|None = None` (last field); `Database.mark_account(account_id, status, *, cooldown_hours: float=0, authorized: bool|None=None, session_valid: bool|None=None)`; `Database.release_expired_cooldowns() -> int`; `Database.claim_next_job() -> Job|None` (atomically sets status `Checking Account`).
- [ ] Tests: migration adds `cooldown_until` to an existing DB; `mark_account(..., "Quota Limited", cooldown_hours=24)` then `release_expired_cooldowns()` after forcing past timestamp resets status to `Ready`; `claim_next_job` returns oldest Pending once, then None.
- [ ] Implement with `ALTER TABLE accounts ADD COLUMN cooldown_until TEXT` guarded by `PRAGMA table_info`.
- [ ] Run pytest for the file → pass.

### Task 3: Worker rotation on auth failure + new state
**Files:** Modify `app/automation/meshy_worker.py`; Test `tests/test_meshy_worker.py`
**Interfaces:** Produces `WorkerState.INVALID_CREDENTIALS`, `WorkerState.NEEDS_VERIFICATION` removed → reuse `MANUAL_VERIFICATION`; `run_with_rotation(..., on_result: Callable[[Any, WorkerResult], None] | None = None)` calls `on_result(account, result)` after every attempt.
- [ ] Tests: invalid creds on account A → rotates to B and returns B's result; `on_result` called for both; ordinary FAILED does not rotate.
- [ ] Implement: `run_one` returns INVALID_CREDENTIALS instead of FAILED for rejected Google creds; add it to the rotate set; also check `_poll_visible_status` quota text right after clicking Generate (before wait_ready) and return QUOTA_LIMITED.
- [ ] Run worker tests → pass.

### Task 4: PipelineService + headless runner + lock
**Files:** Create `app/core/pipeline.py`, `app/runner.py`; Test `tests/test_pipeline.py`
**Interfaces:** Produces `PipelineService(database, worker, scheduler, credentials)` with `enqueue(image_path: str, note: str="") -> int` (validates suffix/exists/≤20 MB, raises ValueError), `run_pending() -> int` (processes until no Pending job; returns count), `start_background() -> None` / `stop() -> None` (daemon thread polling every 3 s); `acquire_runner_lock(path) -> bool`.
- [ ] Tests with fake worker: enqueue rejects `.txt`; `run_pending` on success sets job Completed and bumps nothing else; QUOTA result marks account `Quota Limited` 24 h and retries job on next account; all accounts exhausted → job `Quota Limited` with error "No account with credits"; INVALID_CREDENTIALS marks `authorized=False`; MANUAL_VERIFICATION marks `Needs verification`; second `acquire_runner_lock` returns False.
- [ ] Implement: key for credentials is `account.email` (fixes bug where `main.py` passed the password as key); call `recover_jobs()` and `release_expired_cooldowns()` at start of each loop; update job status/progress/error via `Database.update_job`; error text is the `WorkerResult.message` only.
- [ ] `python -m app.runner` builds Database/BrowserManager/KeyringCredentialStore from repo root and runs `start_background()` then blocks.
- [ ] Run `tests/test_pipeline.py` → pass.

### Task 5: GUI auto-run
**Files:** Modify `app/main.py`; Test `tests/test_browser_host.py` untouched; add `tests/test_main_wiring.py`
- [ ] Replace `StartupFlow`/`key_for` password lambda with `PipelineService`; `dropEvent` and "Generate 3D" call `enqueue` (drop = auto-start, no extra click); table shows live account status + cooldown; Generation Queue page lists jobs; runner lock acquired at window creation (if already held by headless runner, GUI only enqueues and says so).
- [ ] Test (offscreen Qt): dropping a PNG creates a Pending job; with `MESHY_AUTOSTART=0` nothing launches a browser.
- [ ] Run full `python -m pytest -q` → all pass.

### Task 6: MCP server for Claude Code / Codex
**Files:** Rewrite `tools/meshy_mcp_server.py` (stdlib stdio JSON-RPC, keep style); Test `tests/test_mcp_server.py`
**Interfaces:** Tools: `generate_model(image_path, note?) -> {job_id}` (enqueue via `PipelineService.enqueue`, spawn `python -m app.runner` detached if lock free), `job_status(job_id)` returns status/progress/error/account email/result_path, `list_jobs(limit?)`, `list_accounts()` (email, status, cooldown, authorized; no secrets), `import_accounts(file_path)` (path only, never inline passwords), `list_exports()`.
- [ ] Tests drive the server over a subprocess pipe against a temp DB (`MESHY_DATA_DIR` env override): `tools/list` names; `generate_model` with bad extension → isError; `import_accounts` with MemoryCredentialStore via `MESHY_CREDENTIALS=memory` test hook; `list_accounts` output contains no password.
- [ ] Docs: `docs/mcp-setup.md` with the `claude mcp add` and Codex config lines.
- [ ] Run tests → pass.

### Task 7: Verify and report
- [ ] `python -m pytest -q` full run; paste counts.
- [ ] Rebuild exe via existing `MeshyAIStudio.spec` only if tests pass.
- [ ] Update OR-017/018 rows with evidence; state unverified: live Google 2FA page, live quota text, live selectors (no real second account tested).

## Self-review
Coverage: bulk import (existing `AccountManager` + MCP import), 2FA (T1), rotation/health (T2–4), drag-to-gen (T5), MCP (T6). Type names consistent (`mark_account`, `claim_next_job`, `on_result`). Known limit: Google may still force phone/CAPTCHA on fresh bought accounts; those are marked `Needs verification` and skipped, not solved.
