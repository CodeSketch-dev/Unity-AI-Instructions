---
name: mesh-scene-combiner
description: Combine static meshes by material with an Editor bake and a budgeted runtime combine, excluding anything dynamic. Use when a scene has thousands of static MeshRenderers and draw calls are high.
---

# Mesh scene combiner

Pattern (knife-tower `MeshSceneCombiner`, report 02, VERIFIED):
- **Editor "Bake Renderer Groups"**: one traversal groups eligible static MeshRenderers BY MATERIAL and stores the renderer lists in the component (no mesh assets written, no build-size cost).
- **Runtime**: build one combined mesh per material group, async with a per-frame millisecond budget (default 6 ms in play, ~200 ms behind a loading screen, 0 = single frame), yielding with UniTask at `LastUpdate`. If unbaked, fall back to a runtime scan (slower, same result).
- **Exclusions**: explicit exclude roots, a skip tag (`Tag_SkipMeshSceneCombiner`), dynamic detection by component/name keywords (animated, moving, rotating, ladder, treadmill). Never combine anything that moves, fades, toggles or is destroyed.
- **LODGroup**: combine LOD0 of non-dynamic groups, then disable the LODGroup and force LOD1/2 renderers off. Combined static geometry loses LOD (accepted).
- **Readable meshes**: `CombineMeshes` needs `isReadable` on the SOURCE meshes in builds; enable it only on combiner sources.
- Pay the cost behind the loading flow, not mid-gameplay. Keep `ShadowCastingMode.Off` on baked meshes that never cast shadows.

Why one material matters: a combiner can merge only identical materials, so colour must come from vertex data, not per-object materials or MaterialPropertyBlock (`world-batching-culling`, `shared-material-vertexcolor` rules in AGENTS.md).

Orchestrate with `scene-optimizer-bake`. Measure before and after (renderers, batches, set-pass, bake ms) and say whether it was a device (`profiling-evidence`).
