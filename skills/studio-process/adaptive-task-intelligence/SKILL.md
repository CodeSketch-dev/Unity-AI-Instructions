---
name: adaptive-task-intelligence
description: "Choose the cheapest reliable method for a task (API, CLI, UI automation, vision), verify, measure and learn per category and environment. Use when a task has several viable methods, when automating Unity or Windows apps, or when asked to benchmark or optimise how the agent works."
triggers: adaptive, tool selection, which method, benchmark method, ui automation or vision, agent-desktop, accessibility tree, screenshot or api, task performance, token cost, latency, perf memory, learn from results, chon cong cu, phuong an nhanh nhat, tiet kiem token, do hieu suat, tu hoc, windows automation, ui automation
---

# Adaptive task intelligence

Loop: CLASSIFY -> SELECT -> EXECUTE -> VERIFY -> MEASURE -> LEARN -> CONTINUE. Tools: `tools/adaptive/` (stdlib Python, `py -I tools/adaptive/cli.py --help`). Data: `~/.claude/adaptive/perf.db` (or `$ADAPTIVE_HOME`), never in git, aggregates only.

## 1. Fast path first
`cli.py classify "<task>"` is a regex pass (no model). `fast_path: true` (trivial/simple, not critical) -> take `candidates[0]`, verify, record, done; no scoring, no extra reading. Evaluation must never cost more than the task. Critical (delete, deploy, publish, money, credentials) -> accuracy profile, mandatory verification, no exploration.

## 2. Select (only when several methods are plausible)
`cli.py select --category C --env "os=windows|app=<name>|ver=<x>" [--profile balanced|speed|tokens|accuracy]`.
- Hierarchy is a prior, not a rule: direct API/SDK/Editor API/test framework > deterministic CLI/logs/telemetry > targeted UI Automation (scoped snapshot) > screenshot + vision > hybrid. See `references/tool-hierarchy.md` for per-task defaults.
- Data overrides the prior only with >=5 effective verified samples in the exact (category, env). Other apps' data is never reused; a changed `ver` flags `env_changed` and falls back to the prior.
- Success means VERIFIED success. Tokens are UNKNOWN unless the runtime reported them; unknown terms are dropped, never guessed.
- Bounded exploration (every 10th run, never when critical, skipped when the best is cheap and reliable) finds better methods. Regressions demote a method; overconfident predictions are corrected from outcomes.

## 3. Execute and verify
Use `loop.run([Step(...)])` or the same discipline by hand: timeout on every attempt, max attempts, STOP switch (`cli.py stop` / `resume`), at most one safe retry for idempotent steps, then the next method. A non-idempotent step that fails is never retried or replaced unless a `state_check` proves it was not applied; otherwise report `needs_manual_check`. No way to verify = stop, do not claim success.
- Do not use screenshots/vision for anything a deterministic assertion can verify. Do not read a whole accessibility tree: `agent-desktop` adapter is scoped (`--app`, `--root`, `--skeleton`, `--compact`), validates refs, recovers STALE_REF once when `retry: safe`, and falls back to vision (`references/agent-desktop.md`). It is NOT installed here; never install without the owner's OK.

## 4. Measure and learn
Record every method run: `cli.py record --category C --env E --method M --success 1 --verified 1 --latency-ms N [--in-tok N --out-tok N]`. Real session tokens: `cli.py metrics --transcript <jsonl>`. Never store prompts, secrets, screenshots (free text is redacted and capped at 200 chars). `cli.py report [--category C]` shows aggregates.

## 5. Learn into skills (gated)
`cli.py propose` writes proposals only when a method has >=20 effective samples, lb >= 0.9 and is >=30% faster than the default. Editing a skill needs the owner's explicit permission: `cli.py apply <proposal> --skill S --allow-skill-edit` (backup, adds a delimited LEARNED block, lint score before/after, auto-restore on drop); undo with `cli.py rollback-skill S`. Learned preferences never override safety rules or mandatory instructions, never come from one benchmark, and respect `skill-architect` (dependencies, no duplicate skills).

## 6. Control
View: `report`, `health`. Soft reset (undoable, backed up): `reset --category C [--env E --method M]`, `reset-undo <id>`. Backup/restore: `backup`, `restore <file>`. Reproduce the real benchmark: `py -I tools/adaptive/bench.py`. Tests: `py -I tools/tests/test_adaptive.py`.
