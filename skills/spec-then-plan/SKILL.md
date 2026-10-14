---
name: spec-then-plan
description: "Workflow for non-trivial work: clarify, compare approaches, spec, task plan with verification, review, execute with checkpoints. Use before any multi-step or risky feature, or on \"plan\"/\"spec\". Skip for small edits."
---

# Spec, then plan, then execute

Most rework in the first projects came from starting to code before the intent, constraints and verification were written down. This skill is the team's standard for planning; it needs no external plugin. Documents live in the project: `docs/specs/YYYY-MM-DD-<topic>-design.md` and `docs/plans/YYYY-MM-DD-<topic>.md` (if the project already uses another docs path such as `docs/superpowers/{specs,plans}`, follow it). Templates are in `assets/`.

## Phase 1: Understand (before any design)
1. Read the project's feedback notes, existing specs/plans, relevant code and reference projects. Do not ask what the repo can answer.
2. State the goal in one sentence, who it is for, and what "done" looks like in observable terms.
3. Ask the human only questions that change the design (gameplay intent, public API, data loss, budget, fidelity level). Batch them (max 4), each with a recommended default. Make small decisions yourself and list them as assumptions.
4. Scope check: if the request spans independent subsystems, split into separate spec/plan pairs and order them.

## Phase 2: Choose an approach
Give 2-3 viable approaches with trade-offs (effort, risk, performance on low-end mobile, fit with the installed framework, reversibility) and **a recommendation**. Don't narrate approaches you won't pursue beyond the decision. Record the chosen one and why in the spec.

## Phase 3: Write the spec
Use `assets/spec-template.md`. It must contain: goal, constraints (framework, platform, perf, reference fidelity labels), architecture (components, data, events, ownership), data/config/assets chain, UX/behavior details, edge cases, risks, and **acceptance criteria that can be checked** (Console clean, Play path X works, screenshot matches reference at 3 ratios, numbers within target band). Present it to the human in a short summary and wait for approval when the decision is theirs (design, fidelity, scope). Self-review before presenting: no TBDs, no contradictions, every requirement testable, nothing out of scope slipped in.

## Phase 4: Write the plan
Use `assets/plan-template.md`. A good plan is executable by someone with no context:
- **Global constraints** and **review focus** (the failure modes most likely here: domain reload, null configs, duplicate subscriptions, pooling, save/load).
- **Tasks in dependency order**, each small enough to verify alone, with: files to create/modify (exact paths), interfaces consumed/produced, numbered steps, the exact verification (command, MCP check, Play path, screenshot) and the expected result.
- Tests first where logic is testable (formulas, parsers, state machines, data migrations) via EditMode tests; wiring and visuals are verified through Editor inspection, Play Mode and screenshots (see `done-means-wired`, `unity-qa-playtest`).
- A **final integration task**: wiring, save, compile, Console, Play from the real entry flow, report.
- Self-review: spec coverage (every acceptance criterion maps to a task), no placeholder steps, names and signatures consistent across tasks.

## Phase 5: Execute
- One task at a time: implement, verify, mark done in the plan checkboxes, then continue. Don't batch-claim completion.
- Subagents (if available) for independent tasks with disjoint files; give each the exact task text and constraints; review their output before accepting. Don't parallelize edits to the same scene/prefab.
- When reality contradicts the plan, stop, update the spec/plan, tell the human what changed and why, then continue. Never silently drift.
- Re-read `docs/feedback-notes.md` between tasks (`feedback-notes-sync`); new feedback may change the plan.

## Phase 6: Close
Run the acceptance criteria, report verified vs unverified, update the plan status, and put durable lessons in the feedback notes or the relevant skill.

## Right-sizing
Keep the process cheap as well as rigorous (`token-efficient-workflow`): query indexes instead of exploring, reuse recipes (`clone-feature-recipes`), and write the spec to the size of the decision, not the size of the feature.
Tiny fix: act directly. Single-system change: short spec (half a page) + checklist plan. New system or pipeline stage: full documents. The rigor should match the cost of being wrong.
