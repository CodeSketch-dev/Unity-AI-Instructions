---
name: mobile-perf-audit
description: Audit a Unity mobile game for CPU, GC, physics, rendering, UI and memory issues with measurable fixes by impact. Use on FPS/lag/heat/draw-call questions or before a milestone build.
---

# Mobile performance audit

Principle: measure first, remove work first, then batch, then cache, then micro-optimize. Never claim an improvement without evidence, and say plainly when something was not measured on a real low-end device.

## Procedure
1. **Baseline.** Profile a representative scene in a development build when possible (Profiler, Frame Debugger, Memory profiler; editor numbers are only indicative). Record frame time, GC alloc/frame, batches/SetPass, triangles, physics ms.
2. **Static scan** of the code for the usual offenders:
   - `Update`/`FixedUpdate` on large populations; `Find*`, `GetComponent`, `Camera.main`, LINQ, string building, closures/lambdas, `new WaitForSeconds` in hot paths.
   - Per-object `OnTriggerEnter` that calls `GetComponent` on the other collider (route through a collision registry/dictionary lookup instead).
   - `Instantiate`/`Destroy` in gameplay loops (pool instead).
   - Physics queries without `NonAlloc`, layer mask or trigger interaction flag; loose collision matrix; mesh colliders where primitives suffice.
3. **Rendering**: SRP Batcher compatibility, shared materials, GPU instancing for large identical sets, MaterialPropertyBlock only for a few instances, static mesh combining by material (never for things that move/toggle), overdraw from transparency/particles, shadow settings (one cascade, small map, short distance), MSAA/HDR off unless needed, texture compression (ASTC) and mipmaps.
4. **Visibility**: event-driven culling (CullingGroup) for many small objects instead of per-frame distance loops; per-zone camera far clip.
5. **UI**: split static/dynamic canvases, disable Raycast Target on decorative graphics, set text only on change, disable layout groups after layout, batch world-space text.
6. **Memory/loading**: pool spawned things, avoid loading heavy content mid-gameplay, keep one-time costs behind the loading screen.
7. **Rank findings** by (frame-time saved x ease), fix the top few, **re-measure**, and report before/after numbers with the test conditions.

## Output
A short table: finding, evidence (profiler/numbers or "static scan only"), fix, risk. Mark each as measured or unmeasured.
