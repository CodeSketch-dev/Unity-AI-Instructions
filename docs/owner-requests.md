# Owner request ledger (append-only)

| ID | Date | Owner words (short) | Area | Status | Evidence |
|---|---|---|---|---|---|
| OR-001 | 2026-11-12 | Lint-Triggered Skills: PostToolUse lint hook, custom rules whose errors are micro-prompts pointing to a skill file, meta-skill `capture-pattern-with-lint`, one sample skill + rule | lint / skills | IN PROGRESS | plan docs/superpowers/plans/2026-11-12-repo-restructure-and-lint-triggered-skills.md |
| OR-002 | 2026-11-12 | Directory structure is too messy; re-tier it (chose full restructure) | repo layout | IN PROGRESS | same plan, Tasks 1-2 |
| OR-003 | 2026-11-12 | Always use superpowers skills; after restructure other agents authoring skills must follow the standard with guidance, automation and lint | process / standard | IN PROGRESS | same plan, Task 7 |
| OR-004 | 2026-11-12 | Design intent (pasted): Claude Code and Codex share one brain through terminal lint output; skills cost zero startup tokens and load only when the linter fires | lint design | IN PROGRESS | plan Global Constraints (path + zero-context rules) |
| OR-005 | 2026-11-12 | Era of the harness: after the restructure/lint work, build a harness where agents train agents so the studio ships full games automatically (guide file, progress file, tests, permissions, tools) | harness / self-training | OPEN | queued after OR-001..004; needs brainstorming + own plan (reuse studio-self-training, studio-loop-runbook, lint, evals/) |
| OR-006 | 2026-11-12 | Codex and Claude must share the same studio AI instructions and both be able to add/update skills themselves | shared brain | OPEN | sync.bat already copies AGENTS.md + skills to both; gap = Codex has no hooks (needs run_lint.py + publish via terminal); folded into plan Tasks 4, 6, 7 |
| OR-007 | 2026-11-12 | Confirmed: run sync into each Unity project so Claude and Codex both work (lint engine + hook must be installed per project) | sync / lint | OPEN | plan Task 4 per-project install |
| OR-008 | 2026-11-12 | Lint must work the same way for Claude and Codex (shared, synced into projects) | lint | OPEN | plan Task 4 (--changed mode, identical messages test) |
| OR-009 | 2026-11-12 | After sync, gitignore the synced files so nothing stray is pushed to the Unity project repo | git hygiene | OPEN | already covered by sync managed ignore block (/.claude/); plan Task 4 adds check-ignore verification |
