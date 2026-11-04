# Tier values and content scaling (reference defaults)

| Setting | Low | Medium | High |
|---|---|---|---|
| URP depth texture | off | off | on |
| URP HDR | off | off | on |
| Render scale | 0.8 | 1 | 1 |
| Shadow distance | 0 (shadows off) | 50 | 50 |
| MSAA | 1x | asset | asset |
| Fixed timestep | 1/30 | 1/50 | 1/50 |
| Maximum allowed timestep | 0.1 | 0.1 | 0.1 |
| Camera post-processing + depth mode | off / none | on | on |
| Bloom | - | off | on |
| Selective outline asset | no | no | yes (cheap shader outline otherwise) |
| Autotiling normal map | off (global keyword) | on | on |
| Chunk cull distance | 45 m | 80 m | 150 m |
| Camera far | 200 | per zone | per zone |
| Detail mesh (paint/special mode) | low-poly | low-poly | high |

Bootstrap: `[RuntimeInitializeOnLoadMethod(AfterSceneLoad)]` sets frame rate and vSync, then `ApplyRenderPolicy()` and `ApplyPhysicsPolicy()`; cameras apply their own policy in `OnEnable`.

## Content scaling by tier
- Bot / fake-player counts: Low 0, Medium about 2, High about 5 (spawn configs hold Low/Mid/High lists).
- Floating text on Low is batched on an interval (about 0.3 s) or shown on High only.
- Per-object helper components: a tracker that self-destroys on Low; `DestroyIfLowEnd` on decor prefabs (destroys in Awake); `DisableRenderersIfLowEnd` for overdraw FX renderers.

## Scene-scoped policy
A mode that tightens Low/Medium settings snapshots the static values on enter and restores them in `OnDestroy`.

## Quality asset notes
Single level, SRP Batcher on, dynamic batching on, 1 shadow cascade 512 px map, soft shadows supported (tightened at runtime), additional lights limit 1, lodBias 1, `enableLODCrossFade` on, one directional light per scene, linear fog + skybox, no baked lightmaps, no static-batching flags (batching comes from combiners and instancing).

## Android player baseline
IL2CPP, managed stripping High, ARMv7+ARM64, GLES3 first with Vulkan, multithreaded rendering, incremental GC, split binary, R8 minify. Physics: 50 Hz fixed, auto sync transforms off, reuse collision callbacks on, solver 6/1, NonAlloc queries.
