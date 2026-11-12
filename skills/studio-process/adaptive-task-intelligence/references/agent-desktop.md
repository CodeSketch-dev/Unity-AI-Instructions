# agent-desktop integration (vercel-labs/agent-desktop, Apache-2.0)

Status on this machine (checked 2026-11-10): NOT installed (`which agent-desktop` empty). Not installed automatically.

## What it is (from its README)
Accessibility-tree CLI for agents: JSON envelope `{version, ok, command, data|error}`, actionable elements carry refs `@<snapshot_id>:e<n>`; macOS, Windows 10 1809+ (UI Automation), Linux. No model inside; the agent runs observe-act-verify.

## Install (owner decision required; low risk, global npm package)
```
npm install -g agent-desktop
agent-desktop status
```
Windows PowerShell: quote refs (`'@s8f3k2p9:e8'`); the adapter passes argv lists so quoting is not an issue there. Risks: it can read any app's accessibility tree and, with `--headed`, drive real input: keep it behind the normal permission prompts; never feed it credentials.

## Adapter (`tools/adaptive/ui_adapter.py`)
- `snapshot(app, root=None, skeleton=False, compact=True, window_id=None)`: scoped args only (`--app`, `-i`, `--compact`, `--skeleton`, `--root <ref>`, `--window-id`). Too large (>400 refs or >200 KB) or failed -> `{ok: False, fallback: ...}`; use skeleton then `--root` on one branch, else vision.
- `resolve(tree, role, name)`: local lookup in the fetched tree, no extra process call; ambiguous -> None.
- `click(ref, app, role, name)`: refs validated locally (bare `@e8` rejected); `STALE_REF`/`AMBIGUOUS_TARGET` -> one re-snapshot + re-resolve, only when `error.disposition.retry == "safe"`; otherwise `fallback: vision`.
- Every call logs op, ms, ok, reason. Timeouts are per call; runner is injectable for tests.
- Not documented in the README summary, so NOT assumed: timeouts defaults, `find/get/wait` flags, tree child key name (walker is generic), exact error-code list. Run `agent-desktop <command> --help` before adding calls.

## Verification status
Tested against a fake runner only (`tools/tests/test_adaptive.py`, AdapterTests). Not verified against the real binary or any Unity UI: first real use must record outcomes with `cli.py record` so the selector learns whether accessibility beats vision per app.
