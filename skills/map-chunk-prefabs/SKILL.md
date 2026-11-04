---
name: map-chunk-prefabs
description: "Use when a map, level, world, stage or tower is spawned, streamed or built from data at runtime and must become authored prefab chunks placed in the scene: container hierarchy, chunk roots, nested art prefabs, object budgets, combine and cull, conversion steps, gates."
triggers: map, level, world, stage, chunk, tower, floor, spawn map, runtime spawn, streaming, place prefab in scene, bake map, map prefab, object budget, merge boxes, dat map vao scene, keo prefab, man choi, tang thap, khong spawn luc chay, kt style, knife tower
---

# Map chunk prefabs

Maps are REAL authored objects: every wall, floor, platform and decor piece exists as a GameObject inside a chunk prefab that is placed under a container in the scene. The owner can see, select and hand-edit them in Edit Mode. Runtime never constructs geometry from records, lists or paths. Rubric: M01-M08.

## 1. Rules
1. One chunk = one prefab (`Stage_N`, `Floor_N`, `Biome_N`). Chunks are dragged into the scene (or nested in a tower/manager prefab) under a plain container GameObject (`Stage`, `Tower`) that carries the one manager script (checkpoints, waypoints). No `Instantiate(chunk)`, no `Resources.Load`, no path strings, no additive scenes, no streaming. Worlds that differ a lot are separate scenes.
2. Geometry is authored objects: boxes/cubes/meshes with the studio's shared surface/material component, grouped by role (`Wall`, `Floor`, `Decor`, `Props`). A data asset may drive an Editor tool that WRITES these objects once into the prefab; the asset is never read to build the world at runtime.
3. Runtime may only optimize what exists: combine static renderers by material (`mesh-scene-combiner`, behind the loading screen), distance-cull (`culling-group-distance`), far-clip zones. Never create meshes or objects from records.
4. Art props are prefabs from the source-art folder, nested in the chunk. Per-chunk variants only when chunks differ by art or numbers, else plain prefabs.
5. Level selection is data: a selection asset (scene name, thumbnail, load type) listed in a factory; Home spawns its item prefabs from it ([level-selection-assets.md](references/level-selection-assets.md)).
6. Anything that moves, fades, toggles or is destroyed at runtime is excluded from combining (skip tag) and stays its own object.

## 2. Chunk anatomy and granularity ([chunk-anatomy.md](references/chunk-anatomy.md))
`Scene > Stage (plain container + manager) > Stage_N (chunk root: zone/cull component) > {Wall, Floor, Decor, Props} > art prefab > mesh`. Nesting depth <= 8. Granularity: a chunk is what a player sees in one stretch of play (one stage, floor or biome tile). Budget per chunk (soft defaults, measure and tune): <= 600 renderers authored, <= 1500 GameObjects total, prefab file <= 2 MB, no generated mesh > 20 MB. The worst reference chunk was a 22 MB prefab: treat that as the warning sign, not the model.

## 3. Keep object counts low at AUTHORING time
- Merge adjacent same-material parts into larger authored boxes with an Editor tool (idempotent, writes into the chunk prefab, keeps colliders and tags; see [chunk-anatomy.md](references/chunk-anatomy.md) section 3). Example: a 40-cube floor strip becomes 1 stretched box; 12 wall segments in a line become 1 box.
- One shared material or one shared material family (`one-material-world-shader`); colour comes from the surface component or vertex data, not per-object materials.
- Replace repeated decor with prefab instances of one art prefab (GPU instancing friendly), not unique copies.
- Remove hidden/never-seen faces and objects out of the camera path.
- Recount after every merge: renderers, GameObjects, SetPass calls (`profiling-evidence`).

## 4. The scene optimizer stack ([optimizer-stack.md](references/optimizer-stack.md))
One `Optimizer` prefab per playable scene (child of the minigame master or placed on its own): mesh combiner, distance-cull manager, waypoint/keyboard managers, NavMeshSurface. Chunk roots carry a far-clip/cull zone (deepest zone wins when zones overlap; [sample/ChunkZone.cs.txt](references/sample/ChunkZone.cs.txt)). Bake or combine during the loading screen; baked scene variants only as a pair with the YAML source and text serialization (`scene-optimizer-bake`).

## 5. Preview in Edit Mode
Because objects exist, review the map without Play: open the scene, frame the container, Scene View screenshot per chunk, walk the path with the editor camera. A chunk that only looks right in Play is a defect.

## 6. Converting a runtime-built world ([conversion-checklist.md](references/conversion-checklist.md))
Inventory what the runtime builder spawns -> extend/run the Editor builder so it writes real objects into chunk prefabs (idempotent: second run = 0 diffs, `editor-bake-safety`) -> place chunks under the container -> verify side by side with the old runtime world (positions, colliders, tags, layers) -> only then delete the runtime path -> enable combiner and cull -> gates.

## 7. Done check (acceptance numbers; fill before/after)
Scene has the chunk instances (count = design), 0 `Instantiate`/`Resources.Load`/path strings in map code, 0 missing scripts, prefab sizes within budget, renderer and GameObject counts per chunk within budget, batches / SetPass before and after the combine, load time and memory measured, Edit Mode screenshots per chunk, Play walk of the whole route with an empty Console, scenes text-serialized.

## Pitfalls
Generated mesh assets saved as text YAML (huge, orphaned after rebuilds); a builder that writes scene-only objects instead of prefabs; one giant chunk prefab; nested depth > 8; combining moving or toggled parts; deleting the runtime path before the placed world passes the gates; per-object materials that defeat the combiner.
