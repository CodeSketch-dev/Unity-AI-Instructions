---
name: gdd-schema
description: "The machine-readable GDD package format: folder layout, ids, evidence tokens, fidelity and priority, per-system-type front-matter, UI layout contracts, templates and a worked example. Use when writing, reviewing or consuming a GDD for the clone pipeline."
---

# GDD package format

The GDD is the ONLY per-game input; skills stay generic. Structured front-matter is for machines, prose below it is for humans: agents read front-matter and skip prose unless a task needs it. Lint it with `game-orchestrator/scripts/gdd_lint.py` before any agent builds from it. A complete example (`Sky Climb`, a tower climb with a skin shop) is in `assets/example-sky-climb/gdd/`; blank templates per system type are in `assets/gdd-template/`.

## Layout (in the target Unity repo root, read-only for agents except `_generated/`)
```
gdd/
  00-index.md        manifest: game, genre, orientation, loop, systems, priorities {P0,P1,P2}, fidelity_default, ui_default, locales, budget
  decisions.md       append-only decisions with a Why
  glossary.md        names as shown in game -> canonical ids
  systems/S-<nn>-<slug>.md   one per system (front-matter per type)
  ui/UI-<nn>-<slug>.md       one per screen/popup/HUD (layout contract)
  economy/prices.csv ...     tables a script can read
  assets/assets.csv, style.md
  captures/index.md          evidence ledger: id | file | video | mm:ss | what it proves | device
  qa/golden-path.md          the 3-minute playthrough as numbered steps (becomes the Play Mode script)
  _generated/                tools only: lint-report.md, questions.md, gdd.json, task-graph.json/.md
```

## Conventions
- Ids: `S-<nn>-<slug>` system, `F-<nn>.<m>` feature, `UI-<nn>-<slug>`, `A-<nnn>` asset, `CAP-<nnn>` capture; immutable once referenced.
- Evidence token `CAP-014@02:31` (capture id + mm:ss). No evidence, no `exact`/`faithful`: write `?` or `fidelity: free`.
- Fidelity: `exact` (layout, silhouette, numbers within tolerance), `faithful` (same behavior/feel, own art), `free` (our design). Priority: `P0` core loop + first purchase, `P1` complete game, `P2` polish (cut first).
- Acceptance criteria are checkable sentences with a verifier tag: `[play]`, `[shot]`, `[edit]`, `[inspect]`, `[sim]`. A feature needs at least one; P0 needs `[play]` or `[edit]`.
- Unknown = `?` (blocks P0, assumption for P1/P2). Never invent a number.
- System envelope: `id, type, title, priority, fidelity, evidence, depends_on, recipe (skill hint), features[{id, name, priority, acceptance[]}]`. Types: character, camera, input, world, interactable, economy, shop, inventory, pets, quests, audio, vfx, monetization, retention, tutorial, localization, bots, minigame. Type-specific keys are shown in the templates.
- UI files use the `ui-builder` format (reference_canvas, numbered elements with anchor/pos/size, `container`, `state`, HUD `zone`, `states`, `captures`, `opened_by`); patterns in `ui-pattern-library` supply the starting contract.

## Lint rules (what stops the costly mistakes)
L001 schema, L002 ids and cycles, L003 evidence, L004 acceptance, L005 unknowns, L006 economy sources/sinks, L007 reachability, L008 UI contract (anchors, zones, overlap), L009 assets, L010 orphans, L011 budget, L012 P0 coverage and golden path, L013 monetization, L014 exact UI needs one capture per state, L015 stale GDD. BLOCK stops the pipeline, WARN becomes an assumption, INFO is a hint.
