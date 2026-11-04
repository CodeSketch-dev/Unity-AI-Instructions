---
name: reference-project-dissection
description: "Use when the owner points to a reference project/game as the standard: dissect it exhaustively (structure, scenes, prefabs, singleton, services, cameras, UI, code patterns), build a pass/fail rubric, then write skills and a bootstrap so later agents reproduce it."
triggers: reference project, knife tower, giong, chuan, kien truc, mo xe, phan tich, rubric, bootstrap, game studio, self game studio
---

# Reference project dissection (self-directed, exhaustive)

Owner rule: when a reference project is named, the examples the owner gives are NOT the scope. Find, analyse and document everything yourself; the owner will not hint again. Goal: every later agent builds a new game in the same style without being told. We are building a self-running game studio: each task makes the agents smarter.

## Method (superpowers: brainstorming -> writing-plans -> subagent-driven-development)
1. **Plan first** (`docs/superpowers/plans/`): scope = the whole reference, deliverables, phases, gates.
2. **Parallel read-only research agents**, one report each, disjoint files, evidence on every claim (relative path + counts, VERIFIED/INFERRED): structure (folders, asmdefs, naming counts), scene and prefab authoring (roots, prefab instances, persistent root contents, canvases, EventSystem, boot flow, how maps/levels are authored), code patterns (data, factory, events, state, pools, collision, async, tween, audio, localization, UI page/item), cameras, tutorial/quest focus, cross-cutting services (connectivity, rating, ads gates, IAP, analytics, remote config, update/consent, notifications, loading, settings, offline, retention, haptics, device policy, save, lifecycle...), plus a systematic index of EVERY system (universal / optional / game-specific) so nothing is missed. If a service is absent, write "not present".
3. **Rubric**: a numbered pass/fail checklist derived from the reports, each item with how to verify it by script or in the Editor.
4. **Skills**: short, generic, no absolute paths, no names of the owner's other projects; reference material (diagrams, sample code, screenshots, sprite files such as icons) stored in the skill's own `references/` folder. Merge with skills that already exist (read them and `git log` first); never duplicate or overwrite blindly.
5. **Bootstrap**: a skill + Editor tool/checklist that installs every universal service into a new project automatically (persistent root prefab, canvases, connectivity check, rating, settings, loading, ads/IAP/analytics wiring points, device policy...).
6. **Apply and judge**: refactor an existing project against the rubric in staged, verified batches; score every item pass/fail with evidence; be strict, aim at 100%.
7. **Retro**: fold what the refactor taught into the skills, add reference screenshots, publish.

## Never
Reference only what the owner pointed at; do not write into the reference project; do not copy proprietary art/audio into shipped content; do not stop at the examples the owner listed.
