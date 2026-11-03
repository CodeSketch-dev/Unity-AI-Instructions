---
name: codex-delegation
description: "Delegate well-specified CODE-ONLY tasks to the Codex CLI (cheap model) as a managed worker to save Claude tokens: write a brief, run codex exec in the background, then compile/test/review yourself. Use for pure logic, tests, data tables, boilerplate; keep design and Editor work on Claude."
triggers: codex, delegate, tiet kiem token, save tokens, luna, codex exec, worker, giao viec
---

# Codex delegation (manager pattern)

Works with: `codex exec --skip-git-repo-check -C <repo> -s workspace-write -m gpt-5.6-luna --disable hooks --disable codex_hooks -o <out> -` with the brief on stdin. Smoke test: reply PONG. MCP connection errors in the log are noise (Editor MCP servers are not reachable from Codex): Codex has no Editor access.

When to delegate (cheap, specified, verifiable): pure static classes + their NUnit tests, data tables, mechanical refactors/renames, localisation strings, simulators, test updates after a rebalance, boilerplate for a pattern that already exists in the repo.
Keep on Claude: design decisions, anything needing the Unity Editor/Play/screenshots, UI layout judgement, art direction, reviewing results, commits.

Brief template (write it to Temp/codex/<name>.md): role + code style, "CODE-ONLY: edit/create only these paths, do not run Unity or git", files to READ first (spec + 1-2 analogous files), exact API signatures and values from the spec, tests to write with assertions, constraints (no per-frame allocation, determinism), "you cannot compile, do not claim tests pass", ask for a short summary of signatures/assumptions.

Manager loop: start the wrapper in the background (Tools/codex/run_codex_task.sh <brief>), keep working, then `git status` / `git diff` to confirm ONLY owned files changed, refresh + compile in the Editor, run the tests, read the Console, fix or re-brief, then commit. Never trust Codex claims; never let it touch scenes/prefabs/meta. One writer per file: do not give Codex files another agent owns. Log delegated tasks in the backlog LOG.
