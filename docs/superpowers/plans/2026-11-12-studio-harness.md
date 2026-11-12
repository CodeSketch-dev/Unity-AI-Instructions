# Studio Harness Implementation Plan (spec + plan)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (native). Steps use checkbox syntax.

**Goal:** A harness that lets agents (Claude Code, Codex) run backlog tasks unattended inside hard limits, verify every result with commands the agent cannot argue with, record progress to a file any later agent reads, and mine repeated failures into new lint rules and skills (agents training agents).

**Architecture:** The five parts of a harness map to five pieces. Guide file = `AGENTS.md` + task briefs; progress file = append-only `docs/log/harness/progress.jsonl` + generated `progress.md`; tests = per-task verifier commands run by the runner; permissions = profiles in `data/harness/permissions.json` enforced twice (CLI flags to the agent AND a post-run git-diff scope check the agent cannot bypass); tools = adapters for `claude -p` and `codex exec`. The training loop is: failures -> `miner` groups them by signature -> candidates + a `train` task whose agent follows `capture-pattern-with-lint`, accepted only if the publish gate and new rule tests pass.

**Tech Stack:** Python 3 stdlib + pytest, `claude`/`codex` CLIs (flags verified: `-p --permission-mode --allowedTools --disallowedTools --output-format --max-turns --model`; `exec --sandbox -C --json`).

**Spec:** owner messages 2026-11-12 ("harness", "agents train agents", "studio automatic 100%"), ledger OR-015.

## Global Constraints

- The harness never commits, pushes, publishes or edits `~/.claude` settings. Publishing stays an explicit `publish.bat` step (stop 3 of the four always-ask categories).
- Hard limits are code, not prose: max tasks per run, max attempts per task, max consecutive failures (3), per-command timeouts, a STOP file checked before every task.
- A task passes only when its verifier commands exit 0; an agent's "done" counts for nothing. Scope: every file changed during the run must match the task's `owns` globs and no forbidden pattern (`.git/`, `settings`, secrets).
- Progress records are append-only JSON lines (one object per attempt) with evidence tails; secrets are never logged.
- Files live per `docs/REPO-LAYOUT.md`: code in `tools/harness/`, data in `data/harness/`, tests in `tools/tests/test_harness_*.py`.

## Review Focus

1. Pre-existing dirty files in the working tree must not be blamed on (or hidden from) the agent: scope check compares before/after content hashes.
2. A hung agent or verifier must not hang the loop: timeouts kill the process tree and record `timeout`.
3. A corrupt or half-written progress line must not stop `status`/`mine`.
4. Two runs started at once must not both take the same task: lock file per task id.
5. Verifier commands come from task files; they run with `shell=False` argument lists only.

## Tasks (each: failing test first, watch it fail, minimal code, suite green)

### Task 1: tasks + progress (`tools/harness/tasks.py`, `progress.py`)
Produces: `load_tasks(dir) -> list[Task]`, `Task(id, title, brief, owns, verify, permission, kind, max_attempts, agent)`; `append(path, record)`, `read(path) -> list[dict]` (skips corrupt lines), `done_ids(records)`, `next_task(tasks, records)` (first task without a `pass` record), `write_summary(records, md_path)`.
- [ ] Tests: schema validation errors name the field; corrupt line skipped; next_task skips passed ids; summary lists last status per task.

### Task 2: scope + permissions (`scope.py`)
Produces: `snapshot(repo) -> dict[path, sha1]` over `git status --porcelain -uall`; `changed_since(before, after) -> list[str]`; `check_scope(changed, owns, forbidden) -> list[str]` (violations).
- [ ] Tests (real temp git repo): clean change inside owns passes; change outside owns flagged; pre-existing dirty file unchanged is ignored; pre-existing dirty file modified further is flagged; forbidden pattern flagged even inside owns.

### Task 3: verify (`verify.py`)
Produces: `run_verifiers(verify, cwd) -> (ok, results)`, `signature(result) -> str` (sha1 of the normalised first error line, digits and paths stripped).
- [ ] Tests: exit 0 passes; non-zero fails with tail; timeout recorded and process killed; same error with different numbers/paths gives the same signature.

### Task 4: agents + runner (`agents.py`, `runner.py`)
Produces: `Agent.run(brief, task, cwd) -> AgentResult(exit, tail, seconds)`; `ClaudeAgent`, `CodexAgent` (command builders, unit-tested without launching), `FakeAgent`; `run_task(task, agent, repo, progress_path, rework_brief)`, `run_loop(tasks, agent, repo, progress_path, max_tasks, stop_file, max_consecutive_failures)`.
- [ ] Tests (FakeAgent): pass path records `pass`; failing verifier -> second attempt receives a brief containing the failing evidence; out-of-scope edit -> `fail-scope`; STOP file halts before the next task; three consecutive failures halt the loop; per-task lock prevents a second runner.
- [ ] Command-builder tests: Claude command contains `-p`, `--permission-mode`, the profile's `--allowedTools`/`--disallowedTools`, `--max-turns`; Codex command contains `exec`, `--sandbox`, `-C`.

### Task 5: miner + lint hits (`miner.py`, `tools/lint/run_lint.py`)
Produces: `mine(records, min_count=2) -> list[Candidate(signature, count, task_ids, example)]`; `write_candidates(candidates, md_path)` (dedupe by signature); `make_train_task(candidate, dir) -> Path`; lint engine appends `{ts,file,rule}` to `hits.jsonl` beside `run_lint.py` (cap 512 KB); `mine_lint_hits(paths) -> Counter`.
- [ ] Tests: two failures with one signature become one candidate; candidates file is idempotent; train task has owns `skills/**`, `tools/lint/rules/**`, `tools/lint/tests/**` and verifiers = lint tests + layout lint; lint run writes a hit line; cap stops writes.

### Task 6: CLI, data, docs
Produces: `tools/harness/cli.py` (`status`, `next`, `run --agent claude|codex|fake --max-tasks N`, `mine`), `data/harness/permissions.json` (profiles `read-only`, `repo-edit`), a sample read-only task, skill `studio-harness` (`studio-process` group), AGENTS.md + digest lines, `publish_gate.py` also runs `tools/tests/test_harness_*.py`.
- [ ] Tests: CLI `status` on an empty progress file exits 0; profile file parses and every task's `permission` exists.
- [ ] Live smoke: `cli.py run --agent claude` on the read-only sample task (cheap model, max 3 turns); record the real result honestly.

### Task 7: verify, review, publish
- [ ] Full suite equals baseline plus new tests (2 pre-existing failures unchanged), layout lint 0, skill lint 0 errors, requesting-code-review pass with Review Focus, `publish.bat`.

## Self-Review
Spec coverage: guide file (briefs + AGENTS rules, Task 6), progress file (Task 1, 4), tests (Task 3, 4), permissions (Task 2, 4, 6), tools (Task 4), agents-train-agents (Task 5, train task through the same runner). Interfaces named identically across tasks. Out of scope on purpose: auto-publish, auto-edit of existing skills (owner rule: skill edits need owner permission, so the trainer only adds new skills/rules under the gate), cloud runs.
