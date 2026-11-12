---
name: lod-automation-workflow
description: "Decide LOD vs cull vs combine and automate LOD generation on low-end Android: import-time LODs, screen-height thresholds, hierarchical LOD, LOD bias per tier. Use when vertex cost is high, or on 'add LODs'."
triggers: lod, lodgroup, level of detail, auto lod, mesh simplify, mesh simplification, decimate, hlod, hierarchical lod, lod bias, screen height, giam poly, giam triangle, toi uu mesh, cap do chi tiet
---

# LOD automation workflow

Labels: `Source: third-party example (Unity-Technologies/AutoLOD, idea-only)` = idea only, no code copied (Unity Companion License). `Source: our practice` = our own rule.

## 1. Pick the tool first
Source: our practice. On low-end Android, draw calls and materials usually cost more than triangles (`mobile-perf-audit`, `world-batching-culling`). Choose:
| Situation | Tool |
|---|---|
| Many small static props, same material | Combine (`mesh-scene-combiner`, `mesh-merge-baker`) |
| Many tiny objects far away | Cull (`culling-group-distance`) |
| Few big meshes (>= ~2k tris) seen near and far: landmarks, trees, buildings | LODGroup |
| Distant clusters of static meshes | Hierarchical LOD (one merged proxy per chunk) |
| Skinned characters | Tri/bone budget (`character-perf-budgets`), crowd LOD by distance, no auto-simplify |
Measure first: if vertices drawn is not the bottleneck, LODs add memory and no speed.

## 2. Import-time generation
Source: third-party example (AutoLOD, idea-only).
- A model post-processor runs on import, simplifies the mesh in steps, writes LOD meshes as sub-assets next to the model and builds the LODGroup.
- Keep the simplifier pluggable per model; project-wide settings with per-model override.
- Skip meshes already under a small tri budget.
- Each level halves quality (0.5^i); on mobile cap at 2-3 extra levels.
- Generated assets are deterministic and re-generatable; never hand-edit them.
- Source: our practice. The FBX importer's own LOD generation or a Blender decimate pass (`art-direction-asset-pipeline`) is an acceptable swap for the same idea.

## 3. Thresholds (screen-relative height)
Source: third-party example (AutoLOD defaults as a starting point).
- Halving ladder: LOD0 0.5, LOD1 0.25, LOD2 0.125; last level swaps to culled at about 0.01.
Source: our practice.
- Low-end: shift up (LOD1 about 0.35, cull about 0.03), at most 3 levels.
- Pick thresholds from the real gameplay camera distance; if LOD1 looks the same as LOD0 up close, raise the threshold.
- Per tier at runtime (`device-tier-policy`): `QualitySettings.lodBias` Low 0.5-0.7, Medium 1.0, High 1.5; `maximumLODLevel` 1 on Low skips LOD0. No asset change needed.

## 4. Hierarchical LOD (distant combine)
Source: third-party example (AutoLOD scene LOD, idea-only).
- Split the scene into grid chunks; per chunk build a merged, simplified proxy of its static meshes, either material-preserving (one submesh per material) or atlased to one material.
- Show the proxy beyond a distance and swap to the real objects when near, with hysteresis.
- Only static, never toggled/destroyed objects go in.
Source: our practice. Build offline as an idempotent, chunked Editor tool with Undo groups, keep source objects, re-runnable (`editor-tool-authoring`).

## 5. Pitfalls
Source: our practice.
- LODGroup on tiny props: each group costs CPU; under ~500 tris or a few pixels, cull or combine instead.
- LODGroups inside meshes already combined: combining defeats LOD; combine near-only, LOD the rest, disable the LODGroup after combining.
- Skinned meshes: auto-simplification breaks weights and shapes; use hand-made low skins or budget cuts.
- Vertex-colour world materials (`vertex-color-baking`, `one-material-world-shader`): the simplifier must keep colour and UV channels, else LOD1 shifts colour; A/B screenshot.
- Hard-edged lego/voxel meshes: decimation rounds silhouettes and pops; keep LOD0 or use a flat box proxy.
- Cross-fade doubles draw cost; use a plain swap on low-end.
- Shadow casters: use the lowest LOD or no shadows, else shadow pops.
- LOD meshes add RAM; count them before shipping.

## 6. Verify with Unity MCP
Source: our practice. Same camera before and after: rendering stats (triangles, vertices, batches, set-pass), script stats, mesh memory. Screenshot A/B at the switch distances on the Low tier to catch pops. Report numbers and say if measured on a device (`profiling-evidence`).

Notes: `references/autolod-notes.md`.
