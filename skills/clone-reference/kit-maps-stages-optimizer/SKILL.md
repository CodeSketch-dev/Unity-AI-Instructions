---
name: kit-maps-stages-optimizer
description: "Use when authoring stage/floor chunk prefabs in a scene container, ordering stages, adding checkpoints/zones, or setting up the per-scene optimizer (combine, cull, navmesh, waypoints). Chunk anatomy, stage order = hierarchy order, three optimizer generations."
triggers: stage chunk, chunk anatomy, stage container, stage order, hierarchy order, scene optimizer, optimizer bake, mesh combine bake, bake prefab, lane map, tower floors, obby chain, nesting depth, chunk map, thiet ke stage, toi uu scene, knife tower style map
---

# Kit: maps, stages, per-scene optimizer

Opt-in kit (see `prefab-kit-catalog`). Rules live in `map-chunk-prefabs` (placed prefabs, never runtime-spawned), `scene-authored-prefabs`, `scene-optimizer-bake`, `mesh-scene-combiner`, `culling-group-distance`, `zone-level-design`; this skill adds measured anatomy and the optimizer decision.

## 1. Chunk anatomy (genre-neutral)
```
Scene > Stage (plain container + manager scripts) > Stage_N (root: trigger BoxCollider + far-clip zone)
   > { Floor, Wall, Decor, Waypoints, Info(world label), Links } > art prefab > mesh
```
- Containers are plain GameObjects; the chunk root carries the ONLY component (zone). Walls carry NavMeshModifier; decor is what low-end kills (`DestroyIfLowEnd`).
- Reference sizes (48 chunks): median 26 GameObjects, ~150 nested instances, 0.9 MB, worst 16 MB (5000 repeated ladder models: the warning sign, not the model). Budget per `map-chunk-prefabs`.
- NESTING DEPTH: plain geometry chunks measured 2-3; 7 once a safe zone/shop stand is embedded; 8-9 when a boss or character is nested. The old "<= 8" target was exceeded by real chunks, so the target is <= 9 and characters/bosses are placed in the scene, not nested in chunks.
- Far-clip zones: 200-250 enclosed, 500+ open; zones overlap on purpose (deepest wins).

## 2. Order = hierarchy order
Stage/checkpoint order is the sibling order under the container; an editor `Load` button sorts checkpoints by sibling-index path (parent before child) and assigns indexes. Ids in tuning/teleport assets are positional: after reordering, re-run `Load` and recheck those ids. Progress = per-mode `DataValue<int>` of the highest checkpoint; a world/zone list asset (unlock level, tuning, scene name, teleports) unlocks with a latch that never relocks.

## 3. Add a stage (10 steps, short)
Duplicate the previous chunk prefab -> rebuild Floor from boxes with the shared material -> Walls -> Decor props -> waypoints in walking order (+ traversal links) -> label -> nest the safe-zone/checkpoint -> set root trigger + far distance -> save, drag under the container -> `Load` checkpoints, add teleport asset -> run the optimizer bake, Play from checkpoint 0 and from the new teleport.

## 4. Optimizer: three generations, pick the third
1. Per-object combine at load (runtime cost, ANR on low-end).
2. Pre-merged FBX copies + a binary `_Optimized` scene twin per world (91 MB FBX, two scenes to keep in sync).
3. RECOMMENDED: one optimizer prefab per scene with a one-key editor bake (mesh combiner groups, distance-cull list, NavMesh, waypoints, scene-specific managers); baked lists are scene overrides, re-bake after ANY chunk edit. Write the bake step so it is idempotent and reports counts. Pair with a mesh bake to prefab ("bake-prefab") so the combined result is an authored asset, not a runtime product (`mesh-merge-baker`, `editor-bake-safety`).
Low-end kill switches on decor; one directional light; no lightmaps/occlusion data unless measured.

## 5. Optional genre packs
Neutral: container, chunk anatomy, zone root, checkpoint order, world list asset, optimizer prefab, prop kit with one shared material and kill/safe volumes. Packs: tower (floors stacked on Y by an editor Generate, per-floor fall detector, turns), obby chain (stage + checkpoint pad + left/right turns), boss set piece inside a chunk.

## Done-check
Chunks placed in the scene (no runtime spawn); checkpoint indexes follow hierarchy; bake run reports counts and a second run changes nothing; depth stat script <= 9; Play from first and last checkpoint; Console clean.

## Pitfalls
Baked renderer lists go stale after chunk edits; duplicate checkpoint classes; a generator that logs an error on success; debug/test hotkeys left in `Update` run in BUILDS (wrap in `#if UNITY_EDITOR || DEVELOPMENT_BUILD` and flag them in review); static zone fields (`s_active`) must reset on subsystem registration; a 23 MB floor prefab; two tween libraries in one feature.

References: [recipes](references/recipes.md), [PROVENANCE](references/PROVENANCE.md).
