---
name: staged-refactor-playbook
description: "Use when refactoring a live Unity project toward a reference architecture in verified stages: baseline snapshot, stage order, per-stage gates (compile, EditMode counts, missing scripts, Play), rubric scoring, lean before/after numbers, rollback rules, batch reports."
triggers: refactor, restructure project, staged refactor, conformity, rubric, score, stage gate, gate, baseline, lean, lighter project, before after, rollback, tai cau truc, don dep du an, cham diem, giai doan, knife tower style, kt style
---

# Staged refactor playbook

Why: a big refactor done in one sweep hides regressions and costs more rework than it saves. Work in small stages that each end green, measured against a baseline and a rubric. Never report "done" without numbers. Tools: `unity-script-migration` (GUID-safe renames/moves/splits), `lean-asset-audit` (size and dead-asset proof), `tech-debt` (deletion rules), `project-structure-layout` (the target), `regression-suite`, `editor-lane-single-writer` (one Editor writer).

## 1. Baseline (before the first change)
Record in the plan file and keep it:
- git clean on the folders you will touch; branch/commit hash as the rollback point.
- Compile state and Console (empty or the known list).
- Full EditMode run: PASS and SKIP counts (reflection tests skip silently, so SKIP matters). PlayMode smoke if it exists.
- Missing scripts and missing references on every Build Settings scene and every prefab (Editor script, count per asset).
- Play 5 s on each main scene with an empty Console.
- Lean numbers: `lean-asset-audit/scripts/size_report.py` + `import_audit.py` output; draw calls/SetPass/batches on the main scenes (`profiling-evidence`), scene load time, script/prefab/scene counts.
- Rubric score: fill `references/conformity-rubric.md` for the project (P/F/U per item, evidence per P and F; run the verify command for every U you can). Get the pessimistic and verified scores and the list of failing blockers.
Without the baseline you cannot prove "not worse".

## 2. Stage order (cheapest and safest first; adapt to the rubric's failing blockers)
1. Zero-risk lean: untrack derived/generated folders, ignore rules, delete DEAD-PROVEN orphans in separate batches (`lean-asset-audit`).
2. World and maps as prefabs placed in the scene (no runtime spawn of the world); keep combiner/culling; draw-call and load-time gates.
3. Scene roots: managers, player stack, HUD as prefab instances; persistent root prefab in every scene (`scene-authored-prefabs`).
4. Scripts, folders, naming, one type per file, events to StaticBus, dead code (`unity-script-migration`, `project-structure-layout`).
5. Other modes/minigames and Home, one at a time with the same recipe; merge forked copies into a base + config (merge, do not delete: both are live).
6. Foundation: asmdef policy, test asmdefs, `.gitignore` audit, build/version method, hooks (`house-editor-tools`, `git-hygiene-conventions`).
7. Human layer: per-feature README, onboarding doc, walkthrough by a fresh agent who adds a popup and an item with no help, timed.
Each stage = one plan item with files, acceptance numbers, rework risks.

## 3. Per-stage loop and gate (`references/stage-gates.md`)
Loop: claim the Editor lane -> small batch (one feature or a handful of files) -> compile -> gate -> release the lane -> commit only if the project rule allows (otherwise leave a clean named diff) -> next batch.
Gate for every batch, all must hold:
- compile clean, Console no new errors;
- EditMode PASS count not lower, SKIP count not higher than baseline;
- 0 missing scripts and 0 missing references on every touched scene and prefab (reopen the scene from disk, not the cached one);
- Play 5 s on the affected scenes, empty Console; owner-visible screenshot where UI/scene changed (`render-parity-debugging` baseline comparison when visuals could change);
- no new rubric failure (run the verify commands of the touched groups);
- lean numbers not worse (assets MB, draw calls, load time).
A failed gate stops the stage: fix the cause or roll back that batch (`references/rollback.md`); never move on with a red gate.

## 4. Scoring
Weights blocker 5, major 3, minor 1. Item pass = full weight, fail = 0. Two scores per group and total:
- verified = sum(pass) / sum(pass + fail) (unknown items excluded);
- pessimistic = sum(pass) / sum(all items) (unknown counts as fail). This is the number to improve; every U becomes P or F by running its command.
Gate verdict independent of score: any blocker F or U = NOT DONE for the batch. Pessimistic >= 90% with 0 failing blockers = conformant; 75-89% CONCERNS; below 75% FAIL. Update the Status column and the change log after each stage.

## 5. Report per batch (`references/batch-summary-template.md`)
Score before/after (verified and pessimistic), failed IDs, U IDs checked, files moved/renamed/deleted counts, gate evidence (numbers, not adjectives), lean table deltas, what was NOT verified, next stage. Reports of delegated agents are reviewed like a junior's work: diff, compile, Play capture, re-run the gate.

## 6. Retro (end of every stage and at the end)
Write what cost time, fold reusable lessons into the matching skill (`studio-self-training`), delete one-off tools used for the migration, record the final lean report.

## Pitfalls
- Mixing a mass rename with logic changes: keep renames in their own batch and compare tests before/after.
- Deleting "obviously dead" code or assets without the proof (`tech-debt`, `lean-asset-audit`).
- Trusting a green local run: a fresh clone and a reopened scene catch ignored files and stale caches (`repo-hygiene-gitignore-audit`).
- Two writers on one scene/prefab/builder: single Editor lane; file-only agents get disjoint file lists and no Editor.
- Changing gameplay behaviour during structure work: behaviour stays identical; fixes found on the way go to the backlog.
- Compiling while subagents still edit files shows transient errors; compile after they return.
- A rollback via broad `git checkout`/`clean` destroys other work: use targeted restore or `git stash push -u -- <paths>`.
