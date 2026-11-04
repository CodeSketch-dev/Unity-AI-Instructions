# Performance stack notes (studio reference stack)

## World shader family
- One pass only (forward lit, no fallback): no ShadowCaster and no DepthOnly pass, so these meshes neither cast shadows nor write the depth texture (outline-by-depth and depth effects miss them). Decide on purpose.
- Main light + SH ambient only, triplanar auto-tile UVs, optional triplanar bump, `#pragma target 3.0`, instancing, main-light shadow keywords.
- Per-object values in an instancing buffer batch by GPU instancing but NOT the SRP Batcher; SRP Batcher needs `CBUFFER_START(UnityPerMaterial)`. Pick one on purpose and check both in the Frame Debugger. A vertex-colour variant with a CBUFFER is SRP-Batcher friendly.
- Merging same-shader renderers into one shared material plus a property block for colour is a good recipe but only worth it with measured benefit.

## Imports (no presets in the reference)
Textures: max 2048, mipmaps off on UI, Android ASTC override 4x4 / 6x6 / 8x8 by importance, crunch off, global mip limit 1. Meshes: Read/Write only where combined, weld on, blendshapes and animation import off unless used. Audio: Vorbis, decompress-on-load for short clips, streaming for music, mono where possible. A studio addition is presets (`import-presets`).

## Pooling
Framework pool configs with prewarm, capacity, max, persist-across-scenes, deactivate-on-release. Typical: death FX prewarm 60, hit/spawn FX 25, floating text prewarm 0 capacity 200 max 500. A second static pooler with no callers is dead code; do not keep both.

## Loading
Loading screen loads the scene async with activation held at 0.9, activates, waits a few frames so Awake-registered load tasks join, then drives progress from those tasks; audio muted during load; unload-unused only where needed (iOS). Release shared static build buffers after a build (also mid-build on iOS). No `GC.Collect` calls.

## Tooling
Memory profiler and Android Logcat installed; keep a few memory snapshots; a collider extractor (clone box colliders into a child before merging visuals), material collector and vertex-colour debug views are worth building.

## Dead or untrusted, do not copy
Unused material unifier, outline mesh baker, second static prefab pooler, quality-level apply methods, per-feature Allow* flags, unused outline renderer index, Adaptive Performance flag without the package, stats prefab placed in no scene, instanced diffuse variant with zero materials.

## Open questions
Device-to-tier mapping has no telemetry; whether 30 Hz Low physics with max delta 0.1 shows visible slow-down is unmeasured.
