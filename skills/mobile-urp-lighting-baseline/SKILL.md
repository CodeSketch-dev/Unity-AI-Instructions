---
name: mobile-urp-lighting-baseline
description: URP mobile lighting, fog and post preset for a Roblox-look scene plus per-tier world budgets and a budget checker. Use when setting up scene lighting or checking a render-stats report against a device tier.
---

# Mobile URP lighting baseline

Seeded from thunder-break-egg (VERIFIED values) and the house baseline; unmeasured on devices (report 18). Compare with `projectsettings-baseline` for the URP asset values.

## Preset `RobloxLook_Default` (soft defaults)
- Linear colour space. One realtime directional sun, warm white (1.0, 0.96, 0.88), intensity 1.0, shadows on (strength 0.6-0.8). No lightmaps or probes (knife-tower: 0 probes).
- Ambient: flat colour (BSE (0.67, 0.69, 0.72)). Fog: linear, colour = sky horizon colour (BSE (0, 0.76, 1.0)), start ~40% of far, end = far.
- Camera far 100-150 m, FOV 70 (Roblox default); per-zone far clip (`culling-group-distance`).
- URP asset: SRP Batcher on, shadow map 512 (low) / 1024, 1 cascade, shadow distance 25-35, soft shadows off, additional lights off, depth/opaque off, MSAA off or 2x, HDR only if Bloom is used.
- Post: Global Volume with Bloom (threshold ~1.0, intensity 0.2-0.4, only Neon blooms) and Color Adjustments (+10..20 saturation, +5 contrast). No vignette, SSAO, DoF, motion blur or heavy tonemapping on low tiers.
- Skybox: single gradient or cubemap. Tiers: `_ROBLOX_LOWEND` keyword, post off, shadows off, fog on (`device-tier-policy`).
- Do not override scene lighting at runtime; the scene is the source of truth. Skin brightness may need retuning when the sun changes. Match the palette from the reference frame.

## Budgets per tier (DATA, `assets/world-budgets.json`)
Batches 60/100/150, verts 80k/150k/300k, tris 120k/250k/500k, active chunks 20/40/70 for Low/Mid/High; plus materials, shadow casters, particles, bots. Anchors: BSE 93 batches, ~52k verts in the Editor. Treat as defaults.

## Check a report
`py -I <skills>/mobile-urp-lighting-baseline/scripts/world_budget_check.py <Low|Mid|High> stats.json` with `stats.json` like `{"batches": 80, "verts": 90000, "materials": 1, "measured_on": "editor"}`. Exit 1 on any breach. `measured_on` is echoed so an Editor number is never mistaken for a device measurement (`profiling-evidence`).
