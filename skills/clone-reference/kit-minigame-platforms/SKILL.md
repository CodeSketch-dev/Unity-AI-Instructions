---
name: kit-minigame-platforms
description: "Use when adding a game mode/minigame shell or reusable platform/obstacle prefabs: mode registration, mode master with policy functions, HUD loader, collision dispatch, fade tile, conveyor, trampoline, kill zone, teleporter, checkpoint; plus serialization-drift pitfalls."
triggers: minigame shell, game mode registration, mode master, policy functions, platform prefab, fade tile, conveyor, trampoline, kill zone, teleporter pair, obstacle prefab, serialization drift, prefab value ignored, che do choi moi, nen tang, bay kill, knife tower style
---

# Kit: minigame shell, platforms, obstacles

Opt-in kit (see `prefab-kit-catalog`). Existing skills first: `minigame-registration`, `recipe-add-minigame`, `minigame-consistency-contract`, `platform-kit`, `teleporter-pad`, `checkpoint-respawn`, `collision-registry`, `scene-teardown-safety`. This skill adds the catalog-level contracts and pitfalls.

## 1. Mode shell contract
A mode = a scene + one selection asset (type, title, load type, thumbnail, scene, bot spawn config) listed in a Factory; Home card, order, enter counter and load screen are data-driven, no code.
Scene must contain: persistent root prefab, player prefab (shared actor, variant only for camera/UI), `Mode_Master` (`_type`, set in `Awake` so Start-time systems see it), HUD loader (view prefab by Addressable/prefab reference, execution order before BGM starters), BGM starter with an audio config, optimizer prefab (`kit-maps-stages-optimizer`), bot manager (if bots), interstitial pacing object (if used).
Registration steps: enum value (sparse numbers grouped by family, saved as keys: add, never renumber) -> scene + Build Settings -> selection asset -> add to the Factory list -> optional policy cases -> analytics ids derived from the type.

## 2. Policy functions, not scattered ifs
Put every "does this mode allow X" in a static policy class keyed by the current type (weapons allowed, shield revive, reset progress on enter, trail available, skin pool). Never `if (mode == ...)` in feature code; inject outcomes through events. A Start-time inventory restore once re-enabled weapons over the mode setting; one source of truth fixed it. Static mode state must be reset on scene/mode exit.

## 3. Platforms and obstacles (one behaviour per prefab)
Contract: scene-placed prefab, no runtime spawn; the ACTOR forwards contacts, the platform derives from the framework collision register (`collision-registry`), registers ALL its colliders, empty bodies for unused callbacks.
- Fade tile: alpha-fade a cloned material, disable, wait, fade in; hundreds of tiles = hundreds of material instances (use property blocks or a shared fade material, destroy clones).
- Conveyor: add `dir*v*dt` in FixedUpdate for grounded actors; optional move-direction boost (belts felt slow otherwise).
- Trampoline: platform owns only feedback (squash, sfx); bounce physics lives in the actor controller because it depends on fall height.
- Kill zone: `actor.Kill(type)` unless immortal; keep a bypass type for hazards that ignore shields; tag registry for lookups.
- Mover: evaluate the sequence inside the mover controller so riders inherit motion; breakable: precomputed splinters, re-arm on revive; teleporter: in-progress set + wait-for-exit set (no ping-pong), control lock, `finally` restore.
- Shape primitives (cone, cylinder, stair) need only mesh + collider.

## 4. Checkpoint and death branching
Progress marker = `DataValue<int>` per mode type, saved only when the PLAYER enters and the index grows. Death: no progress -> silent respawn; progress > 0 -> revive popup (`revive-result-flow`) chosen by mode through events/policy.

## 5. Pitfalls (verified in the reference)
- A prefab field renamed in the script (`_fadeDuration` -> `_fadeOutDuration`) keeps the old value in the prefab YAML: the new field silently uses its script default. Renaming serialized fields is data loss: use `FormerlySerializedAs` deliberately or re-author the prefab, and diff prefab YAML vs script fields after any rename.
- Prefab value differs from script default (conveyor 100 vs 700): always read the prefab value, not the script.
- Duplicated near-identical classes (two checkpoint types, three HUD loaders): merge before importing.
- Swallowed exceptions (`try/catch {}`) around tween code hide teardown bugs; many upstream fixes were unsubscribe/cancel leaks across repeated scene entry: repeat the mode enter 3 times.
- Legacy namespace dependencies inside a prefab (old movers): replace the actor type or the mover before importing.

## Done-check
Mode enters from the Home card, dies/revives per policy, checkpoint saves per type, wins, returns Home; re-enter 3 times with empty Console; prefab YAML field names equal script fields.

## Genre classification
Neutral: registry, shell, policy, checkpoint, collision dispatch, hazards, mover/bouncer/conveyor/teleporter, switches, win flag. Optional packs: tower climbing, hazard-roamer survival, stage obby, glass bridge, fade-tile arenas, typing/keyboard floors (never import by default; extract the ~80-line concept instead).

References: [recipes](references/recipes.md), [PROVENANCE](references/PROVENANCE.md).
