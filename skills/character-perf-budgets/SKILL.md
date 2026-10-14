---
name: character-perf-budgets
description: "Numeric budgets for player and bot characters on low-end Android: triangles, bones, materials, textures, animators, ragdolls, shadows, nametags, crowd LOD. Use when approving skins, sizing bot counts, or reviewing character performance."
---

# Character performance budgets

ALL numbers are INFERRED starting targets (report 19 sec 4); none was measured on a device. Measure on a mid device with the Profiler before claiming gains or tightening (`profiling-evidence`). The validator enforces them per catalog (`character-catalog.json` `budgets`, `skin_validator.py`).

| Item | Player | Bot / crowd |
|---|---|---|
| Triangles | <= 3,000 | <= 1,500 |
| Bones | <= 25 | <= 20 |
| Materials | <= 2 | 1, shared across bots |
| Texture | 512 px (ASTC) | 256 px |
| Shadows | real shadow on the player only | none or blob |
| Per-skin memory | mesh + texture <= 1.5 MB, one pooled instance per skin id | same |

## Crowd and runtime
- Visible animated characters: <= 12 full-rate Animators; the rest CullCompletely or updated every 2nd-3rd frame (manual `Update` / stepped `animator.speed`).
- Skinned draw calls from characters <= 25 in total (shared material across bots).
- Crowd LOD bands via `CullingGroup` (`culling-group-distance`): 0-15 m full, 15-40 m 20 fps animator, > 40 m renderer off.
- Bot count: scale by device tier (`device-tier-policy`; reference base 5 scaled by tier); spawn one per frame behind a loader task (`bots-as-players`).
- Ragdoll: player + nearest 3 only, from a shared pooled ragdoll prefab per rig (<= 14 rigidbodies, auto-sleep 3 s), spawned at death with the pose; the reference bakes 12 rigidbodies + 11 joints into EVERY skin prefab (verified on `Character_Skin_1.prefab`): do not copy.
- Nametags: max 8 visible, CullingGroup band ~25 m, text set only on change, one shared font atlas.
- Instantiate never in the gameplay loop; skins come from a pool keyed by skin id; unload unused addressable skins on shop close.
- Shop preview: one 512x512 RenderTexture (256 low tier), camera enabled only while visible (`shop-skin-preview`).

Skins that exceed a budget fail the importer unless the catalog documents an exception with a reason.
