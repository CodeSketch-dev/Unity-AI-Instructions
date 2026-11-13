---
name: profiling-evidence
description: Rules and report format for claiming a performance change with evidence (what was measured, where, before and after). Use before reporting any FPS, draw-call, GC or memory improvement, including Editor microbenchmarks.
triggers: profiler, performance evidence, microbenchmark, Editor benchmark, P95, Time.frameCount
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

## Editor microbenchmarks
- Pin the exact workload and source hash for before/after runs. Invoke a case once per Editor update; do not batch many `Temp` allocation samples into one update and call that repeated evidence.
- Cache delegates before timing and keep reflection out of the per-sample path. In EditMode, do not use `Time.frameCount` as the sample clock: it may not advance between editor-driven invocations.
- Report warm-up policy and sample count, plus median, P95, and maximum. Preserve unfavorable outliers and repeat results; explain them instead of deleting them.
- An isolated CPU microbenchmark is not scene performance, GPU timing, or device FPS. Keep those claims separate and measure the scene/device workload directly before drawing them.

## Pooled workloads and derived graph caches
- Record allocated pool capacity separately from live count, per-frame graph rebuild count and fixed-step count for matched windows; a small visible set may still pay full-capacity work.
- Skip rebuilding only for proven unchanged logical inputs: cover every authoritative input the graph reads, not merely unchanged population or topology. Keep dirty rebuilds and publication ordering.
- Require epoch/reset, query reorder and late-carry tests, plus same-count/different-content cases. Late-arriving phase work must invalidate reuse before its consumer runs; cached identity/order must not hide changes.
- Inspect child-job/worker markers and whole-frame median/P95 before/after; relocating a wait is not work removal or an improvement. Keep adverse results and separate Editor evidence from device performance.
- Review dependency changes using the complete branch's Schedule/Complete sequence for steady-state AND resize, not only a diff hunk or allocation helper. An existing unconditional fence may sit outside the quoted hunk; compare actual scheduled work between fences before declaring drift.

## Interleaved live-frame comparisons
- Label each policy with an inline runtime ProfilerMarker and read that marker from the same raw CPU frame. Editor callbacks can observe state adjacent to the last completed profiler frame; never use callback order alone as the mode label.
- Predeclare balanced assignments, warmup, population/progress checks, and acceptance criteria. Compare fixed-tick strata as well as all frames; keep outliers and rejected paused/completed or mismatched-wave windows. Sum repeated same-name PlayerLoop samples instead of taking the last sample.
- When the reference disables multiple caches, prove that unrelated caches would not skip work in every compared frame. Record actual stage counts, live population and gameplay progress, plus the environment and raw artifact hash.
