---
name: mobile-budget-checklist-for-systems
description: "Per-system mobile budget checklist: CPU ticks, allocations, draw calls, particles, UI rebuilds, memory, pooling. Use when designing or reviewing any new system for low-end Android."
triggers: budget, mobile budget, low-end, ticks, allocation, draw calls, particles, pooling, system review, hieu nang
---

# Mobile budget checklist for a new system
- Ticks: one manager ticks many entities; throttle or stagger; disable idle components.
- No per-frame allocations, LINQ, Find/GetComponent in hot paths; cache Camera.main.
- Spawn through pools; cap particles and objects per action.
- Rendering: shared materials, SRP Batcher safe, few transparent layers, CullingGroup for small renderers.
- UI: split static/dynamic canvases, raycast off, set text only on change.
- Evidence: `profiling-evidence`; say plainly when not measured on device.
