---
name: scene-optimizer-bake
description: One-button, idempotent pre-build scene bake (combine groups, culling lists, NavMesh, waypoints, feature bakes) callable from menu and Unity MCP. Use when a scene needs several bake steps run in the right order.
triggers: scene optimizer, bake scene, optimizer bake, ctrl shift b, bake all, kt style
---

# Scene optimizer bake

A static `Scene_Optimizer.Bake()` behind a menu (`Tools/Scene Optimizer/Bake`, Ctrl+Shift+B) runs, in order: mesh combiner bake -> distance-cull list fetch from target prefabs -> NavMeshSurface bake -> AI waypoints -> feature bakes (chunk prebake, treadmill/collector lists) -> mark scene dirty. One keystroke bakes the whole scene.

## Build one in a new project
1. A static `Bake()` entry with no UI dependency so Unity MCP and batch runners can call it; a menu item and shortcut wrap it.
2. Order: geometry combine groups -> culling lists -> NavMesh -> waypoints/feature bakes. Each step logs name, counts and ms; progress bar in the Editor only.
3. Idempotent: running twice changes nothing; keyed by name/GUID; keep authoring objects (never delete sources); overwrite mesh assets by delete + recreate (in-place overwrite left a stale GPU mesh).
4. Mark dirty and save once at the end (or per chunk for huge scenes, one segment per MCP call).
5. Prefer ONE scene + a bake step over two copies. `*_Optimized` scene copies drift (one grew 2x) and may be binary (undiffable); if unavoidable force text serialization and keep the original as authoring source.

## Where results are stored
Baked renderer lists and culling lists are scene-level overrides on a prefab instance (the optimizer prefab keeps empty lists). After any stage edit run the bake again; stale lists are skipped silently. Add the bake to the pre-build checklist and to refactor batches (`staged-refactor-playbook`).

## Done check
Claim success only from the tool's returned counts (groups, renderers, cull targets, navmesh status) and a clean Console (`done-means-wired`, `editor-tool-authoring`). A second run reports zero changes.

Related: `mesh-scene-combiner`, `culling-group-distance`, `world-batching-culling`, `map-chunk-prefabs` (optimizer stack layout).
