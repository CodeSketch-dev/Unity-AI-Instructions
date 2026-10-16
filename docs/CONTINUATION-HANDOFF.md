# Continuation handoff — 2026-10-16

## Objective

Continue improving this instruction/skill repository so a supplied Roblox GDD and evidence can drive a fast, genre-selectable Unity implementation. This repository is instructions/tools only: never create, modify, copy, commit, or push an external Unity project.

## Non-negotiable user rules

- Reply tersely in Vietnamese; write repository files and docs in English.
- Do not hard-code or infer a named mechanic, project entity, balance value, asset, scene, path, or behavior from a reference project. Skills/templates describe reusable capabilities only; the active GDD/evidence supplies concrete values. Preserve unknowns rather than guessing.
- Do not use a concrete mechanic (for example a station, collectible, or companion) as a pipeline default. A GDD may select a capability explicitly.
- Preserve the Unity house-style roots and framework detection workflow, but materialize feature names/asset IDs from the active GDD.
- Do not commit, push, delete broad files, or modify the read-only reference projects.
- Use small, phase-scoped skill sets; do not bulk-load skills or reference source.

## Reference authority

- Knife Tower and Monkey Escape: primary code house-style evidence.
- Break-and-Steal: only SketchEngine v2 API semantics and Roblox-style environment/map visual evidence (material/shader, vertex-color baking, mesh combining, map composition). Never derive code architecture, naming, UI, pooling, lifecycle, or gameplay from it.
- Exact framework APIs must always be verified from the target manifest/package before generation.

## Current pipeline safeguards

- `clone-pipeline/SKILL.md` has the content-neutral contract.
- `game-orchestrator/scripts/gen_task_graph.py` uses `<System>` claim placeholders materialized from each GDD system ID, rather than fixed feature paths/registries.
- Phase-2+ clone tasks receive `docs/reference-foundation.md` through `context_refs` without reloading the whole foundation skill.
- World-zone tasks wait for validated `visual-mapspec`; visual/bake skills remain scoped to visual work.
- `gdd_lint.py` and task-graph generation allowlist IDs before they become paths/claims/titles (`^[A-Za-z][A-Za-z0-9_-]{0,63}$`).
- Focused regression checks were added in `tools/tests/test_orchestrator.py`; Python is unavailable on the previous host, so do not claim the suite passed until the new host runs it.

## Recommended next bounded audits

1. Inspect remaining GDD schema templates/types for generic genre extensibility without adding any game-specific domain by default.
2. Audit `roblox-genre-patterns` and generated task selection so GDD-declared capabilities route to leaf skills without a fixed catalog becoming mandatory.
3. Run the focused Python tests and strict skill lint on a host that has Python; repair only real failures.
4. Continue scanning dispatchable `SKILL.md` files for concrete defaults. Keep reference facts in profile/evidence files, not generic route text.

## Heartbeat continuation

The prior account had a 30-minute heartbeat named `continuous-instruction-audit`. Automations may be account-local. If it is not present after sign-in, recreate an active thread heartbeat with this prompt:

> Continue bounded audits of `D:\GitProject\Unity-AI-Instructions` only. Improve reusable, content-neutral Unity/Roblox GDD skills and pipeline guards. Read `docs/CONTINUATION-HANDOFF.md`, `docs/feedback-notes.md`, and the tail of `docs/agent-handoff.md` first. Reference Unity projects are read-only. Do not create/modify Unity projects, commit, push, or make broad deletions. Keep Thunder visual/v2 API scoped and Knife/Monkey as code-style sources. Stay silent when there is no meaningful improvement; report only meaningful changes, failures, or needed user decisions. Stop when the user says “dừng”.

## Before every change

1. Read `docs/feedback-notes.md` and the tail of `docs/agent-handoff.md`.
2. Read the target file immediately before editing and use a focused patch.
3. Add/adjust a targeted regression or static check when behavior changes.
4. Append a concise factual entry to `docs/agent-handoff.md`.
