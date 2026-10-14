---
name: scene-optimizer-bake
description: One-button, idempotent pre-build scene bake (combine groups, culling lists, NavMesh, waypoints) callable from the menu and from Unity MCP. Use when a scene needs several bake steps run in the right order.
---

# Scene optimizer bake

knife-tower `Scene_Optimizer` menu `Tools/Scene Optimizer/Bake (Ctrl+Shift+B)` runs, in order (report 02, VERIFIED): mesh combiner bake -> distance cull list fetch -> NavMeshSurface bake -> AI waypoints -> feature bakes (e.g. keyboard prebake) -> mark scene dirty.

## Build one in a new project
1. A static `Bake()` entry (no UI dependency) so Unity MCP and local batch runner can call it; a menu item and shortcut wrap it.
2. Order: geometry combine groups -> culling lists -> NavMesh -> waypoints/feature bakes. Each step logs name, counts and ms; show a progress bar in the Editor only.
3. Idempotent: running twice changes nothing; keyed by name/GUID; keep the authoring objects (do not delete sources); overwrite mesh assets by delete + recreate (in-place overwrite left a stale GPU mesh in BSE).
4. Mark the scene dirty and save once at the end (or per chunk for huge scenes, one segment per MCP call).
5. Prefer ONE scene + a bake step over two copies. Reference `*_Optimized` scene copies drifted (one grew 2x) and some are binary (undiffable); if a variant is unavoidable, force text serialization and keep the original as the authoring source.

Claim bake success only from the tool's returned counts and a clean Console, not from file edits (see `done-means-wired`, `editor-tool-authoring`).
