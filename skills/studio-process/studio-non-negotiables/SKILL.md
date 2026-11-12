---
name: studio-non-negotiables
description: "The short list of studio gates no agent may skip (verification, UI measurement, prefab-first, proof before delete, single Editor writer, no unrequested commit...), each with how it is enforced and what evidence proves it. Use at the start of every task (pre-flight) and before reporting done."
triggers: bat buoc, khong duoc bo qua, chuan ngay tu dau, lam dung ngay, rework, refactor lai, pre-flight, checklist, non-negotiable, gate, quality first time
---

# Studio non-negotiables (right first time)

Owner principle: be fast, beautiful and correct from the FIRST pass. Rework and later refactors cost far more tokens and time than care now. A few minutes of pre-flight and real verification beat a day of fixing. Never trade a gate for speed; get speed from reuse, parallel agents, batching and narrow searches instead.

## Pre-flight (before the first edit, every non-trivial task)
1. Read what already exists: matching skills (router hint / `skills/INDEX.md`), the reference prefab/project, `docs/feedback-notes.md`, the project's AGENTS rules. Do not re-research what a skill answers.
2. Write the plan with ACCEPTANCE NUMBERS (what is measured, expected value) and the verification for each step.
3. Name what could go wrong (rework risks) and how the plan avoids it; check for a sibling feature to copy structure from instead of inventing.

## The gates (each: enforced by, evidence required)
| # | Gate | Enforced by | Evidence |
|---|---|---|---|
| 1 | Nothing is "done" without verification: compile clean, Console read, relevant tests with PASS/SKIP counts, Play check of the touched path | `verification-before-completion`, stop hook | command output / counts in the report; unverified items listed as unverified |
| 2 | UI work: `ui-always` set, text and icons centred (<=1 px by script), outline, autofit, Play screenshot looked at, layout audit totals | UI hooks + `ui-layout-audit` | dx/dy numbers, audit before/after, screenshot path |
| 3 | UI is authored in Edit Mode in the source prefab; runtime only shows/fills data | `ui-edit-mode-authoring`, audit rules | prefab opened in Edit Mode, grep for runtime restyle = 0 |
| 4 | Managers/world pieces/maps are prefabs placed in the scene; per-minigame prefabs and code (share only currency bar and few common buttons) | `scene-authored-prefabs`, `minigame-consistency-contract` | hierarchy listing, 0 missing scripts |
| 5 | Deleting or replacing anything: prove it is unused first (GUID/path/class scans), delete the old in the same change | `tech-debt` | scan output |
| 6 | One Editor writer at a time; re-read files before editing; never overwrite newer work | `editor-lane-single-writer`, `multi-agent-coexistence` | lock/heartbeat, merged-change note |
| 7 | Defect reported once = class swept everywhere and written into a skill/audit rule | `minigame-consistency-contract` | list of screens/minigames audited |
| 8 | No commit/push unless the owner asks; destructive actions confirmed; secrets never printed | git hook + AGENTS safety | none needed |
| 9 | Framework: prefer SketchEngine APIs; follow installed package APIs, never invent | `house-style-foundation` | file:line of the API used |
| 10 | Superpowers skills and coding discipline on every task (assumptions as Rulings, simplest code, surgical diffs, success criteria first) | AGENTS + router reminder | plan/ledger with Ruling lines |
| 11 | Performance target low-end Android: no per-frame allocations, pooled spawns, batched draw calls; claims need profiler evidence or "not measured" | `mobile-perf-audit` | numbers or explicit not-measured |
| 12 | Project rules: landscape only, money text without `$`, claim blocking popups before Play tests, Play only with the Editor lock | project AGENTS.md | screenshot/test notes |
| 13 | Visual evidence: anything player-visible (UI, VFX, camera, art, animation) is not done until the game was launched, the change observed, and a screenshot saved; the report lists the saved path and what it shows. Compile or unit tests alone never close a visual item | `qa-playmode-smoke`, `creative-director` review, report check | screenshot path(s) + one line of what was observed; "not launched" = item stays open |

## Adding or changing a gate
A gate is critical only if it has an ENFORCEMENT (hook, tool, audit rule, or a required line of evidence in reports). Prose alone is not a gate. When a mistake costs rework, add the gate here, link its skill, add the audit/hook if possible, publish.

## Reporting
Every final report lists: gates touched, evidence (numbers, paths), what is unverified. Missing evidence = not done.
