---
name: soak-test
description: "Long-run Play Mode stability recipe: fixed duration, sampled memory/GC/FPS via Unity MCP profiler, leak signs, scene reload loops. Use before release, after pooling or lifecycle changes, or on slowdown/crash reports."
triggers: soak test, long run, memory leak, gc growth, fps drop over time, scene reload loop, stability, chay lau, ro ri bo nho, tut fps, on dinh
---

# Soak test

Use to find problems that only appear after minutes: leaks, pool exhaustion, listener pile-up, GC spikes.

## Setup
1. Back up the save; claim blocking popups with a real tap (`playmode-driver-recipes`). Clear the Console.
2. Duration: 10 min quick, 30 min standard, 2 h before release. Use an input driver or autoplay so the game keeps doing real loops (spawn, collect, spend, popups).
3. Enable profiler modules via MCP (memory, rendering, scripts).

## Sampling
Every 60 s record: managed memory, GC allocation per frame, GC count, texture/mesh memory, object counts of key types, draw calls, SetPass, average and p95 frame ms, pooled active vs total.

## Scene reload loop
Reload the main scene or switch modes 10-20 times. After each cycle object count and memory should return to within ~5% of the first pass. Growth per cycle = leak (static lists, missing unsubscribes, undisposed tweens or tokens).

## Verdict
- PASS: memory plateaus, p95 frame time stable, no new errors.
- FAIL signs: monotonic memory or object count, rising p95, growing pool total, repeating errors, NullReference after destroy.
Report numbers (first, last, slope) and the suspected owner of any growth; fix the cause, then repeat the same duration.

## Cleanup
Exit Play, restore the save, clear profiler data. State plainly that numbers are Editor-measured, not low-end-device measured.
