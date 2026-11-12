---
name: profiling-evidence
description: Rules and report format for claiming a performance change with evidence (what was measured, where, before and after). Use before reporting any FPS, draw-call, GC or memory improvement.
---

# Profiling evidence

No profiler numbers exist in the reference repos for the registry or culling gains; only one reference project's batch counts (map 3767 renderers / 149 materials -> 1 / 1; 93 batches, 62 set-pass in Play Mode, not on a device). Do not quote speedups you did not measure.

## Report every perf claim as
| Change | Metric | Before | After | Where measured | Conditions |
Metrics: frame ms (CPU/GPU), GC alloc per frame, batches/set-pass, vertices, physics ms, memory. Where: Editor, development build, or named device. Conditions: scene, camera position, tier.

## Rules
1. Measure before changing; same scene/camera after.
2. Label each row `device`, `build`, `editor` or `static scan only`; Editor numbers are indicative.
3. Prefer a simple change that removes work over a clever one: remove, batch, cache, then micro-optimize.
4. Unity MCP stats (rendering/script stats) count as Editor evidence; say so. If MCP is unavailable, say nothing was measured.
5. A structural count (renderers, materials, batches) is acceptable proof of a structural change; it is not proof of an FPS gain.
6. Never present an estimate as a measurement. Use `mobile-perf-audit` for the audit procedure.
7. Population benchmarks must assert the intended live population and relationships remain throughout the measured window; objects falling out, expiring or being collected can turn a full-pool test into an empty-loop result. Report active counts, warmup, step count and conditions. Allocate timing/report helpers before the GC baseline, and label calling-thread allocations separately from job-worker or whole-frame allocations.
