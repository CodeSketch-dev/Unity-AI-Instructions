---
name: hot-loop-data-batching
description: "IDEA-ONLY from DOTS samples: batch large populations in plain arrays and structs with one manager tick, optional Jobs and Burst, instead of per-object Update. Use when hundreds of entities cost CPU and DOTS is not adopted."
triggers: hot loop, batching, manager tick, struct array, jobs, burst, update many, crowd, population, nhieu doi tuong, vong lap nong
---

# Hot-loop data batching (idea-only)

Source: third-party example (Unity EntityComponentSystemSamples, Unity Companion License) as inspiration; nothing copied. Our games stay MonoBehaviour + SketchEngine, NOT DOTS. DOTS-specific parts (Entities, baking, subscenes, Netcode) are SKIPPED.

## Steps
1. Measure first (`perf-triage-ladder`, `profiling-evidence`).
2. Replace N `Update` calls with one manager owning `struct` arrays (position, timer, state) and ticking them in one loop, staggered by index or interval.
3. Keep Unity object access (Transform writes) in one tail loop; use `TransformAccessArray` with a parallel-for-transform job only when the profiler shows the tail dominating.
4. Add Burst/Jobs only for pure math on blittable arrays; allocate persistent native containers and dispose them in `OnDestroy`.
5. Disable idle components instead of early-return; combine with `culling-group-distance`.

## Pitfalls
- Jobs add overhead for under ~1000 items; plain loops often win.
- Native containers leak if not disposed; safety checks catch races in Editor only.

## Verify
`profiler-get-script-stats` before/after on a representative scene; state plainly if not measured on device.
