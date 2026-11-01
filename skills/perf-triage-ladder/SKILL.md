---
name: perf-triage-ladder
description: "Order of operations for a slow Unity mobile scene: set target, find CPU vs GPU side, fix the single biggest cost, re-measure, set budgets. Use when FPS is low or uneven, before choosing any optimization; pairs with mobile-perf-audit."
triggers: low fps, frame drops, stutter, hitch, gc spike, slow scene, triage, bottleneck, cpu bound, gpu bound, frame budget, giat, lag, cham, toi uu truoc
---

# Perf triage ladder

Source: third-party example (method), rewritten for Unity mobile. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/performance-optimization. This skill owns the ORDER; `mobile-perf-audit` owns the offender list; `profiling-evidence` owns the claim format.

## Ladder
1. **Target + repro.** State the budget (60 fps = 16.7 ms, 30 = 33.3 ms) and a repeatable worst-case scene or action. "Sometimes slow" is not actionable.
2. **Measure, do not guess.** Profiler plus Frame Debugger (dev build when possible; Editor numbers are indicative only). Record frame ms, CPU main, render thread, GPU ms, GC alloc per frame, batches/SetPass.
3. **Pick the side.** Compare CPU frame vs GPU frame; the slower one sets fps. Fixing the other side changes nothing.
   - GPU bound: overdraw, transparent layers, resolution, shader cost, shadows, post, particle fill.
   - CPU render-thread bound: batches/SetPass, material variety, no atlas, SRP Batcher breakers.
   - CPU main bound: scripts, physics callbacks, UI rebuilds, GC.
4. **Fix the single biggest cost** with an algorithmic win first: do less (event instead of poll), do it less often (throttle/stagger), cache, then batch, then micro-optimize.
5. **Re-measure** on the same scene and hardware. Keep the change only if the number moved.
6. **Budget it:** per-subsystem ms and asset ceilings (draw calls, particles, texture memory), checked in QA.
7. **Report** before/after numbers, the bottleneck found and what was not measured on a low-end device.

## Symptom -> look here first
| Symptom | First check |
|---|---|
| Periodic hitch | GC alloc in Update, Instantiate/Destroy, LINQ, string building |
| Smooth in Editor, slow on device | GPU fill, thermal throttling, shader variants, texture size |
| Worse with many pickups/NPCs | per-entity Update, GetComponent, physics callbacks |
| UI stutters on open | Canvas rebuild, layout groups, unpooled item prefabs |
| Draw calls high | unique materials, missing atlas, MaterialPropertyBlock on hundreds of renderers |

## Pitfalls
- Optimizing before profiling; profiling the Editor and calling it final.
- Fixing CPU code while GPU bound.
- GPU Instancing toggled with no effect under SRP Batcher: check the Frame Debugger.
- No budget, so it regresses silently.
- Contorting a prototype for speed before it is fun (see `prototype-keep-kill`).

Related: `mobile-perf-audit`, `profiling-evidence`, `device-tier-policy`, `pool-everything`, `culling-group-distance`.
