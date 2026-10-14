---
name: gdd-intake
description: "Turn a Roblox game's videos, screenshots and play notes into a lint-clean GDD package: scaffold, evidence ingest, draft with unknowns, batched questions, UI layout contracts, reference match, lint loop and sign-off. Use when a human wants a clone and only has footage and notes."
---

# GDD intake

Goal: a human finishes a P0-complete GDD in 2-4 hours of play and notes while you do the transcription and structuring. Format: `gdd-schema`; gate: `gdd_lint.py` (`game-orchestrator/scripts`). Never invent a number: unseen = `?`.

## Workflow
1. **Scaffold**: copy `gdd-schema/assets/gdd-template/` to `gdd/`; fill `00-index.md` (game, genre from `roblox-genre-patterns`, orientation, references table, loop in one sentence).
2. **Evidence ingest** (human supplies, you process; extends `gameplay-video-analysis`, `spec-pdf-extract`): videos -> with approval download to a NEW empty directory, extract frames (every ~3 s plus scene changes) and contact sheets, assign `CAP-nnn` ids and write `captures/index.md` rows (what it proves, mm:ss). Screens named `<screen>-<state>.png`: open EVERY image and transcribe all text and numbers. Play notes map into the schemas.
3. **Draft**: one file per detected system and screen with `?` for unknowns, every field tagged with evidence. Which systems exist and what they need: `roblox-genre-patterns`, genre playbooks, `roblox-to-unity-map`.
4. **Interview**: lint, then write `_generated/questions.md`: at most 4 questions per batch, each with a recommended default, taken from the checklist below. The human answers in chat or edits files.
5. **Numbers**: tabulate prices, timers and curves from the captures (3+ points per curve); mark `observed` / `estimated` / `derived`.
6. **UI measure**: for each screen capture, extract the layout contract (positions and sizes in capture pixels) in the `ui-builder` format starting from the closest `ui-pattern-library` pattern; mark `measure: approx` and drop fidelity to `faithful` where precision is impossible. Exact UI needs one full-screen capture per state.
7. **Reference match**: `reference-index` queries per system, screen and asset; fill `recipe` and `source` with real paths; reuse = port, adapt or new (`reference-port`, `rule-port-not-invent`).
8. **Lint loop** until 0 BLOCK; it freezes `_generated/gdd.json` and the hash.
9. **Sign-off**: one summary for the human (systems, P0/P1/P2 counts, open assumptions, estimated hours). This is the only mandatory intake checkpoint.

## Question checklist (ask only what is still `?` after drafting)
Core loop and what ends a run; character speed/jump/size and ragdoll/health; camera orbit/zoom/FOV; input joystick region, buttons, contextual swaps; world zone count, unlock gates, size, hazards, checkpoints, safe zones; economy currencies, sources, sinks, first-purchase time, price curve, caps; shops tabs, item counts, rarities, preview; inventory/tools slots and equip rules; pets/skins acquisition and income; progression level/xp/rebirth; quests and tutorial steps; monetization ad placements, IAP list, passes, consent; retention daily/streak/offline/rating; audio and VFX per event; localization languages; platform orientation and device tier; legal (assets to replace, `clone-ip-safety`). Local-only game: no multiplayer or server, bots substitute.

Copying rules: do not copy Roblox place geometry or protected assets (`clone-ip-safety`); record provenance in `assets.csv`.
