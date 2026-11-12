---
name: studio-harness
description: "Use when running or extending unattended agent work: pick a backlog task, run it through the harness (limits, scope check, verifiers), read or update the progress file, or feed repeated failures into new skills and lint rules."
triggers: harness, unattended, backlog, progress file, agent runs agent, tu van hanh, tu dong hoan toan, train agent, huan luyen agent, run loop
---

# Studio harness

Why: an agent's "done" is not evidence, and a long run forgets itself. The harness runs a task, checks it with commands the agent cannot argue with, and writes what happened to a file the next agent reads. Code: `tools/harness/`; data: `data/harness/`; progress: `docs/log/harness/`.

## The five parts
| Part | Where |
|---|---|
| Guide file | `AGENTS.md` + the task `brief` (the runner adds scope rules and the verifier list) |
| Progress file | `docs/log/harness/progress.jsonl` (append-only, one record per attempt) + generated `progress.md`. Read it at session start; never edit it by hand |
| Tests | `verify` commands in the task file (argument lists, exit 0 = pass). They, not the agent, decide |
| Permissions | `data/harness/permissions.json` profiles, enforced twice: CLI flags to the agent AND a before/after git scope check (`owns` globs, forbidden paths, no commits) |
| Tools | `claude -p` and `codex exec` adapters; hooks and skills load as in a normal session |

## Run
```
python tools/harness/cli.py status            # progress, open ledger rows, STOP switch
python tools/harness/cli.py next              # next task that has not passed
python tools/harness/cli.py run --agent claude --model haiku --max-tasks 3
python tools/harness/cli.py mine              # repeated failures -> candidates + train tasks
```
Halt a running loop: create `~/.claude/harness.STOP`. Hard limits are code: max tasks, 2 attempts per task (the second brief carries the failing evidence), halt after 3 consecutive failures, per-command timeouts, one lock per task id.

## Add a task
Create `data/harness/tasks/<id>.json`: `id, title, brief, owns[], verify[{name, cmd[], timeout}], permission (read-only | repo-edit), max_attempts, kind (work | train)`. Write verifiers that compare against ground truth (count files, run the test suite), not that the agent said so. A task with no verifier is rejected at load.

## Statuses
`pass`; `fail-verify` (a verifier failed, evidence in the record); `fail-scope` (changed a file outside `owns`, a forbidden path, or committed); `fail-agent` (the CLI crashed or timed out). Never mark a task done by editing the file: fix the cause and rerun.

## Agents training agents
`mine` groups failures by signature (numbers and paths stripped). A signature seen twice becomes a candidate and a `train-<sig>` task. The trainer agent follows `capture-pattern-with-lint` and may only ADD a new skill and/or lint rule (verifier `check_added.py` rejects edits to existing skills; the lint tests, layout lint and skill lint must pass). Lint hits from projects (`.claude/lint/hits.jsonl`) show which rules fire; count them with `miner.mine_lint_hits`.

## What the scope check catches (and what it cannot)
Scope is judged against the state before attempt 1, so a rework attempt cannot launder an earlier violation. Caught: files outside `owns`, forbidden paths, commits and HEAD moves, new/changed branches, tags, hooks and git config, edits to `~/.claude/settings.json` and instruction files, renames (source path too), forging the progress file (restored and flagged), secrets in output tails (masked). Not caught: network calls, pushes of commits that already exist, anything outside the repo that is not watched, symlink writes. The profiles stop an honest agent's mistakes; for an untrusted agent also use the Codex sandbox or a separate git worktree. Re-run a passed task with `run --only <id> --force` (verifiers compare to live ground truth, so a stale report fails on purpose).

## Not automatic on purpose
Publishing (`publish.bat`), pushing, deleting data, spending money, credentials: a person or an explicit instruction. The harness never commits.
