---
name: mesh-merge-baker
description: Bake a static map or prefab set into merged chunk meshes with generated colliders, navmesh and render-stats. Use when turning many authored parts into the shipped world or merging many renderers into one mesh with vertex colours.
---

# Mesh merge baker

Based on thunder-break-egg `Map_BatchBaker` and `Egg_MeshBaker` (report 11, VERIFIED) with the colliders/navmesh design from report 18 (INFERRED).

## Pipeline
`MapSpec -> parts per segment -> merge per chunk (one mesh, <= 65k verts, UInt16 preferred) -> save Meshes/.../Chunk_XX.asset (delete+recreate) -> chunk objects (MeshFilter+MeshRenderer, shared material, ShadowCasting Off) -> colliders -> NavMesh -> bounds bake -> render-stats -> save scene`.

## Rules
- `Bake(segment)` per call; keep authoring objects; skip transparent, multi-submesh and mixed-normal sources; moving parts (platforms, spinners, doors) stay separate prefabs with the same material.
- No runtime combine when the bake is persisted as `.asset` (zero load cost). Mark final meshes no-longer-readable unless runtime access is needed (RAM doubles otherwise; INFERRED). For the runtime-combine variant see `mesh-scene-combiner`.
- **Colliders**: no MeshCollider on merged visual chunks. Generate from the same PartSpec: BoxCollider per block, Capsule per pillar/cylinder, a few convex wedges only where needed; a `Colliders` child per chunk; <= 400 per chunk; merge coplanar floor boxes. Register triggers via `collision-registry`.
- **NavMesh**: `NavMeshSurface` collecting physics colliders, `NavMeshAssetManager.instance.StartBakingSurfaces(...)`, then SAVE THE SCENE (failure seen twice) and verify the asset is referenced; rebake after moving shops/zones/cages. Agent radius 0.3, height 1.7, step 0.4, slope 45 (match the capsule).
- Chunk 32-48 m (BSE 45 m). Culling: `culling-group-distance` or `world-batching-culling`.
- Gotchas: reload the scene after disk mesh swaps; re-run bounds bake after map changes; set shadows Off on baked renderers; keep reflection/specular when A/B-matching a reference.
- Report renderers, materials, batches, set-pass, active chunks, verts from a fixed camera set; state whether measured on a device (`profiling-evidence`). Re-running twice must diff to zero.
