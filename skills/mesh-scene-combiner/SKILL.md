---
name: mesh-scene-combiner
description: Combine static meshes by material - Editor bake stores renderer lists, runtime CombineMeshes runs as a budgeted loading task, dynamic things excluded. Use when a scene has thousands of static MeshRenderers and draw calls are high.
triggers: mesh combiner, combine meshes, draw calls, scene combiner, gop mesh, giam draw call, kt style
---

# Mesh scene combiner

Studio standard (verified in the reference stack). Bake and combine are two separate steps:
- **Editor bake ("Bake Renderer Groups")**: one traversal groups eligible static single-material MeshRenderers BY MATERIAL and serializes only the renderer LISTS on the component. No mesh asset is written, no build-size cost.
- **Runtime combine, as a loading task**: register the combine with the loading screen in `Awake` (check the installed loading API) so progress is reported per group. It loops the baked groups only and calls `Mesh.CombineMeshes` per material, spawns one `[Combined] <material>` object, DISABLES (does not destroy) the source renderers.
- **Frame budget**: stopwatch vs a ms budget, `await UniTask.Yield` when exceeded. Defaults: about 6 ms when playing directly, about 200 ms when the loader is busy. No bake present = runtime scan fallback (slower, same result).
- **Exclusions**: inactive subtrees, a skip tag on prefab roots (step, teleport, treadmill style pieces), explicit exclude roots, unsupported components (SkinnedMeshRenderer, ParticleSystem, Animator, Animation, Rigidbody, TMP text), and dynamic detection by component/type keywords (move, rotate, ladder, fade, animation...) cached per type. Never combine anything that moves, fades, toggles or is destroyed.
- **LODGroup**: collect LOD0 only, then disable the group and force all LOD renderers off. Combined geometry loses LOD (accepted).
- **Readable meshes**: sources need Read/Write; enable it only on combiner sources. UInt32 indices above 65535 verts; `UploadMeshData(true)` when playing drops the CPU copy. Combined objects: shadow casting on only if any source cast, `receiveShadows` off unless needed.

## Where the bake lives
Baked lists are PREFAB-INSTANCE OVERRIDES in the scene; the prefab keeps an empty list. Re-bake after ANY stage edit: destroyed references are silently skipped and those meshes stay uncombined. Put the combiner on a small shared `SceneCombiner` prefab (combiner + culler) and bake with `scene-optimizer-bake`.

## Done check
Renderer count, batches and set-pass before/after, bake ms, combine ms behind the loader, visual parity screenshot (`world-batching-culling`). Say whether measured on a device (`profiling-evidence`).

## Pitfalls
- Different materials never merge: colour must come from vertex data (`one-material-world-shader`, `vertex-color-baking`).
- Static flag on a combined object re-merges stale meshes. For mesh colliders, clone box colliders into a collider child before merging visuals.
- Offline-merged FBX scene variants have zero runtime cost but cost build size and drift; prefer bake + runtime combine.

Details, code sample and a one-mesh-per-scene alternative: [references/combiner-details.md](references/combiner-details.md).
