---
name: vertex-color-baking
description: Bake colours into mesh vertex colours correctly (linear space, one helper, palette-driven) and merge renderers into one mesh. Use whenever a baker or generator writes vertex colours or a world looks washed out.
---

# Vertex colour baking

## Rule: LINEAR (report 11, VERIFIED shipped bug, fixed three times in three bakers)
In a Linear-colour-space project write `color.linear` into vertex colours; gamma colours look washed out. Use ONE shared helper (`RobloxColor.ToVertex(Color srgb)`) in every baker and put a comment at the top of each generator. Never store gamma colours in palette assets. A/B screenshot against the source after baking (mean diff target < 0.5%, 0.2% was achieved on BSE).

## Palette ownership
No project has a shared palette; colours are scattered `Hex()` tables (report 18). Use one palette asset (see `roblox-world-kit`): sRGB hex for authoring plus cached linear; themes, rarity and biome tints reference palette ids, bakers read `.linear`. Replace scattered tables when you touch them.

## Bake mechanics
- Spec tables in code; explicit normals; index format by vertex count (UInt32 above 65,000).
- Idempotent by output folder; DELETE and recreate the mesh asset (in-place overwrite left a stale GPU mesh); force reimport prefabs; reload the scene after meshes change on disk (shows `mesh=NULL` otherwise).
- Keep the pivot via the root `worldToLocal`; skip particle children; keep authoring objects; re-run safety: generators must not overwrite hand recolouring.
- Baked renderers get `ShadowCastingMode.Off` unless they must cast.
- Skip transparent, multi-submesh and mixed-normal sources.
- Report counts on every run (parts/verts/tris/renderers/materials).

Merge existing prefabs with `mesh-merge-baker`; the shader side is `one-material-world-shader`.
- Colour space: bake sRGB or linear once; a double conversion makes everything dark. Compare mean luminance with the reference.
- A shared vertex-colour shader may need a per-renderer MaterialPropertyBlock (e.g. base colour) to match the reference look; renderers without it look different.
- Tint ratios for a vertex-colour material come from the baked vertex colours of that mesh, not a fixed reference colour; check the shader actually reads the tint property (see `one-material-world-shader` gotchas).
