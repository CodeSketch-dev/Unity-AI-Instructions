---
name: rigor-switch
description: "Project-level 'rigor: minimal|standard|full' line in AGENTS.md that sets how much process agents apply. Use when starting a project, tuning process overhead, or deciding how much planning and testing a task needs."
triggers: rigor, process level, how much process, minimal standard full, overhead, muc do quy trinh, toi gian, day du
---

# Rigor switch

A one-line dial so agents stop guessing how much ceremony to use.

## Declare
In the project `AGENTS.md` add a line such as `rigor: minimal` (or `standard`, `full`). Missing line = `minimal` for solo or live games, `standard` for team projects. A task note may override for one task (`rigor: full` on a risky migration).

## Levels
**minimal** (default for solo/live): act directly; short plan only for multi-step work; compile + Console + one targeted Play check; log feedback; no spec docs; run `regression-suite` only for the touched row; report in a few lines.

**standard**: adds a written plan (`spec-then-plan`, light), tests for logic and data changes, screenshot evidence for UI, `scope-check` at batch end, a handoff note for shared areas.

**full**: adds a spec with acceptance criteria, `gate-check` at phase boundaries, `consistency-check` after number changes, `test-evidence-review` before "done", `soak-test` before release, a `tech-debt` pass each milestone, skill edits scored with `skill-quality-rubric`.

## Rules
- Never lower the safety rules (data loss, destructive git, credentials) at any level.
- Raise the level for: save-format changes, monetization code, large refactors, release candidates.
- Do not ask which level to use; read the line, apply it, and mention it in the report only when it changed the work.
