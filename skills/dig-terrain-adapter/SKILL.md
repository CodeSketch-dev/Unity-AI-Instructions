---
name: dig-terrain-adapter
description: "Thin adapter between tools/bombs and a terrain deformation plugin (Digger): sphere brush, size and cooldown multipliers per world, ground-layer probe. Use when a clone needs real digging or crater terrain, not just node damage."
---

# Dig terrain adapter

From climb-tower `DigController`, `DigCooldownSystem`, `BombCooldownSystem` (report 15 sec 3.2, VERIFIED). Note: thunder-break-egg's "pickaxe" damages nodes and does NOT deform terrain (`tool-weapon-pipeline` Mine behavior); use this adapter only when the GDD shows real holes.

## Interface (template: `assets/IDigTerrain.cs.txt`, UNCOMPILED)
`IDigTerrain { void Dig(Vector3 position, Vector3 direction, float radius); float GroundLayerAt(Vector3 pos) }` implemented by one `DiggerTerrainAdapter` that wraps the plugin (`DiggerMasterRuntime`, `BrushType.Sphere`, `ActionType.Dig`, async edit). Everything else (tools, bombs, bots) talks to the interface so the plugin can be swapped or stubbed in tests. Do not edit the plugin's code (`rule-editor-tool-safety`); keep the adapter in `Assets/_Game`.

## Numbers
- Effective size = `digSize * MapDigSizeMultiplier`; bomb blast radius = `explosionRadius(3) x PowerMultiplier x MapDigSizeMultiplier`.
- Dig duration = `baseDigDuration (3 s) / digSpeedMultiplier * MapCooldownMultiplier` with a progress bar; bomb throw duration = `2.5 s / throwSpeedMultiplier * MapCooldownMultiplier`.
- Harder worlds: smaller hole and longer cooldown (`digSizeMultiplier`, `cooldownMultiplier`, `coinMultiplier` in the world config).
- Ground-layer probe: SphereCast radius 0.3 downward to choose the texture/layer and the sfx.
- Reward: `Base(10) x (petCoin + 1) x (toolCoin + 1) x MapCoinMultiplier`.

## Performance and safety
Terrain edits are expensive: edit async, cap edits per second, never on the first frame of a scene, test on the low-end tier (`device-tier-policy`), and keep a depth tracker event-driven rather than per-frame. Auto-dig/auto-bomb controllers poll at a fixed interval (0.12 s in the reference), not every frame.

Verify in Play Mode: hole size per tier, cooldown per world, no hitch when many bots dig (cap), terrain saved or reset per design. Not verified here (plugin not available in this repo).
