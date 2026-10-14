---
name: vfx-budget-rules
description: "Particle and FX budgets for low-end mobile: caps per prefab, pooling, shared one-shot emitters, vendor pack hygiene. Use when adding or auditing particle effects."
---

# VFX budget rules

From report 09 (reference counts VERIFIED, targets are soft defaults):
- Cap `maxNumParticles` per prefab: 10-50 typical, 100 max in the reference. Never ship a vendor default of 1000.
- Pool every spawned FX through `pool-everything`; expose via the FX factory (`PoolPrefabConfig` list). One-shot bursts can share a global emitter.
- Release on stop; sort order 0 except UI overlays. World particles cheap on overdraw: small count, small screen area, no full-screen transparent layers.
- Per tier (report 18, INFERRED): Low <= 200 live, Mid <= 500, High <= 1000. Transparent overdraw: Glass <= 5/15/40 visible quads.
- Delete unused vendor packs before build; do not edit vendor files, add a project-side adapter.
- Audit: count particle systems with `maxNumParticles` > 100, transparent quads, and unpooled `Instantiate` of FX; report as measured or unmeasured (`profiling-evidence`).
