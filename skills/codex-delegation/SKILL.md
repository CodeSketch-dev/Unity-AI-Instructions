---
name: codex-delegation
description: "Delegate well-specified CODE-ONLY tasks to the Codex CLI (cheap model) as a managed worker to save Claude tokens: write a brief, run codex exec in the background, then compile/test/review yourself. Use for pure logic, tests, data tables, boilerplate; keep design and Editor work on Claude."
triggers: codex, delegate, tiet kiem token, save tokens, luna, codex exec, worker, giao viec
---

# Codex delegation (manager pattern)

Command: `codex exec --skip-git-repo-check -C <repo> --dangerously-bypass-approvals-and-sandbox -m gpt-5.6-luna --disable hooks --disable codex_hooks -o <out> -` with the brief on stdin (full access is owner-approved; `-s workspace-write` made Codex stop after its first message without writing files). MCP connection errors in its log are noise: Codex has no Editor access. Wrapper: Tools/codex/run_codex_task.sh <brief.md> [model] (log in Temp/codex/<name>.log.txt, last message in <name>.out.txt).

Delegate (cheap, specified, verifiable): pure static classes + their NUnit tests, data tables, mechanical refactors, localisation strings, test updates after a rebalance, boilerplate for a pattern already in the repo.
Keep on Claude: design, anything needing the Editor/Play/screenshots, UI judgement, art direction, review, commits.

Brief (Temp/codex/<name>.md): role + code style, "CODE-ONLY: only these paths, no Unity, no git", files to READ first (spec + 1-2 analogous files), exact signatures and spec values, tests with assertions, constraints (no per-frame allocation, determinism), "you cannot compile".

Manager loop: start the wrapper in the background, keep working, then `git status`/`git diff` to confirm only owned files changed, refresh + compile in the Editor, run the tests, read the Console, fix or re-brief, commit.
REVIEW THE TESTS, not just the code: Codex wrote a "simulation" whose key metric was never computed (hard-coded 0) and a miscalibrated "stuck" check; it compiled apart from an ambiguous `Random` (qualify System.Random). A sim must actually step the model and show the BAD baseline failing the thresholds before the fix passes them.

## Protocol lessons (agent-agnostic: Codex, Kimi, any CLI worker)
- FAKE "completed": never start the wrapper as `(script &)` or `script &` inside a background Bash call. The launcher exits at once and the harness reports "completed" while the worker still runs. Start the wrapper ITSELF with run_in_background so the notification fires when the worker really ends.
- Truth source is a status file, not the notification: the wrapper writes `<name>.status` = `RUNNING pid start`, then `DONE exit=N final=yes|NO_FINAL_MESSAGE dirty_delta=K`. Read it (`Tools/codex/codex_status.sh`). `final=NO_FINAL_MESSAGE` = worker died or stopped early: re-run once, then do it yourself.
- A run can stop after reading files with no output: always check created files + status before trusting a report.
- Other CLIs (kimi etc.): same wrapper with `AGENT_CMD='<cli reading stdin, printing final message>'`; the contract (brief on stdin, status file, out/log files, manager reviews diff, compiles, tests, commits) stays identical.
- Model: terra (smarter) for logic/tests touching real APIs; luna for mechanical edits. Briefs name files to read, owned paths, exact signatures; the worker never touches git/Unity.
- Commit only owned paths (`git add <paths>`): the Editor regenerates baked assets that a broad add sweeps in.
