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
2b. **Capture the WHY, not only the what**: a mature system (characters, skins, shop, services) encodes years of the owner's experience. For each system record its design intent and constraints, the trade-offs it solves, and how it evolved (mine the reference's git history: first commit, big rewrites, repeated bug fixes), so later agents inherit the reasoning and can extend it instead of copying blindly.
3. **Rubric**: a numbered pass/fail checklist derived from the reports, each item with how to verify it by script or in the Editor.
4. **Skills**: short, generic, no absolute paths, no names of the owner's other projects; reference material (diagrams, sample code, screenshots, sprite files such as icons) stored in the skill's own `references/` folder. Merge with skills that already exist (read them and `git log` first); never duplicate or overwrite blindly.
5. **Bootstrap**: a skill + Editor tool/checklist that installs every universal service into a new project automatically (persistent root prefab, canvases, connectivity check, rating, settings, loading, ads/IAP/analytics wiring points, device policy...).
6. **Apply and judge**: refactor an existing project against the rubric in staged, verified batches; score every item pass/fail with evidence; be strict, aim at 100%.
7. **Retro**: fold what the refactor taught into the skills, add reference screenshots, publish.

## Never
Reference only what the owner pointed at; do not write into the reference project; do not copy proprietary art/audio into shipped content; do not stop at the examples the owner listed.


## Learning loop (owner standing order 2026-11-10: always learn the essence from references, with superpowers)
Whenever the owner names a project, pack, SDK or minigame to learn from (Break and Steal, Knife Tower, monkey-escape, BounceSdk, an Asset Store pack ...), run this WITHOUT being asked:
1. **Study (parallel, read-only subagents, each told to use superpowers):** one agent per topic writes `docs/reference-<project>/<TOPIC>-STUDY.md` with file:line evidence, numbers, prefab hierarchies, an ASCII diagram, "unverified" list. Reference projects are never modified; their Unity MCP may be down: read YAML / code on disk.
2. **Evaluate harshly:** scorecard 0-10 per axis (architecture, features, code quality, Unity 6 / package fit, privacy / kids fit, licence, value for us). Asset Store packs: licence first; port IDEAS, never copy code or art without a licence.
3. **Distil (writing-plans):** a plan in `docs/superpowers/plans/` with rulings for every open question (the owner pre-approves gates), keep / throw-away lists, interfaces, tests, owned files per task, acceptance numbers, risks. The essence goes into OUR layer (SketchSdk, UI kit, skills), not a vendor copy.
4. **Port:** Codex for file-only code with owned-file briefs (`codex-ui-director-loop`), director for assets, bake, Play, audits. Original art is regenerated in our style; FX / animations may be reused with dependency closure (`asset-transfer-closure`); our own models only.
5. **Prove and generalise:** compile, EditMode, Play captures, measured numbers; then extract what generalises into generic skills + digest and publish (`studio-hook-factory` if it should become automatic).

6. **Copy-exactly:** when the owner says copy / like X, the port reproduces the reference's tables and rules verbatim (see skill `rule-port-not-invent`, Copy-exactly); rulings fill unknowns only, never narrow or cap.

## Recover unreadable serialized assets

For ripped ScriptableObjects with missing scripts, restore only inert Editor-only data schemas first: original MonoScript GUIDs, type/field names, enum integers and serialized private fields. Read dependency metadata without executing ripped SDK assemblies. Compare native loaded values and object-reference GUIDs against raw serialized data and hash source assets before/after. Successful type binding does not recover stripped methods or absent graph payloads; defaults introduced by a schema are not recovered values. Do not bulk-import SDK/runtime code merely to inspect data.

Shared serialized fields do not establish a component subtype. Resolve the original MonoScript identity before rebuilding layout groups; preserve horizontal/vertical direction, padding and child-control flags. Verify the opened menu, since a closed panel can conceal a wrong layout axis. A source-data type audit is required; field-name regexes alone cannot establish the orientation.

## Inventory source roots before claiming something is absent

Before reporting that a source system, asset, or behavior is missing, inventory the distinct code, serialized scenes/prefabs/assets, native metadata/binaries, and media roots available for the reference. State which roots and file types you actually searched. A stripped script/assembly export is not the complete project export; missing code in that subset does not prove that serialized assets, native behavior, or media are absent. Follow serialized references to their helper, callback, or target when safely inspectable before marking behavior unknown. Stop at unsafe execution or bypasses, and label the remaining uncertainty instead of generalizing beyond the searched scope.
