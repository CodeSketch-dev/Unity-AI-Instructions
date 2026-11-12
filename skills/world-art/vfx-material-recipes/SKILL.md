---
name: vfx-material-recipes
description: "Shader/material recipes and traps: voxel dissolve for teleports, per-sequence material twins, MaterialPropertyBlock clobber, ported materials silently on another shader. Use for dissolve/teleport FX, material swaps during sequences, or black/flat ported skins."
---

# VFX and material recipes

## Voxel dissolve (teleport out/in)
- Quantise world space: `cell = floor(posWS / cellSize)`; visible when `(H - cellCentreY) * dir + (hash(cell) - 0.5) * jitter > 0`; `clip()`.
- Glow where the distance to the cut < edgeWidth, per-cell flicker + fresnel rim; Cull Off with FRONT_FACE flip; same clip in ShadowCaster.
- One rule serves out and in: animate H down (head to feet) or up. Keep HDR edge ~1.1 under bloom threshold 1.0.

## Material twins for sequences
- Twin per source material, cached, never shared between actors when a per-material float (height, progress) is animated.
- Swap `sharedMaterials` arrays; hide particles/trails/sprites/world canvases; restore in an idempotent `End()` called from OnDisable/OnDestroy.
- Interrupted before a gameplay-critical move: perform the move in the abort path.

## MaterialPropertyBlock clobber
- `SetPropertyBlock(null)` or a fresh block wipes values set by other components (tiling, flags). Always `GetPropertyBlock` first, then `Set`.

## Ported materials on the wrong shader
- Symptom: black faces, flat hair. Cause: same-GUID materials rewritten to another shader during import, losing the alpha/colour contract.
- After any port diff `m_Shader` GUID per material against the reference; a mismatch is a defect. Restore reference content (keep your .meta), clear dangling texture GUIDs, tame bloom with a base-colour tint, not with shader swaps.
- Check with a contact sheet (HDR RT, max channel per skin) before/after.
