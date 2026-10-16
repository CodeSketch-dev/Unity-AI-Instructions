---
name: render-parity-debugging
description: "Find why imported or cloned models look worse than in the reference project: shader, textures, MaterialPropertyBlock, vertex colour colour space, lighting parity. Use when a ported asset renders flat, washed out, textured wrong or differently lit."
---

# Render parity debugging

Fix only the divergent path; do not re-author materials blindly.

1. **Same inputs?** Compare material asset, shader, keywords and every texture by GUID/hash with the reference (`asset-transfer-closure`). Different import settings (sRGB flag, compression) count.
2. **Per-renderer MaterialPropertyBlock**: the reference may always write a block (colour, tint); a renderer with no block, or a cleared one, exposes the raw texture/overlay and looks different. Write the same block on the same path, or compare `GetPropertyBlock` dumps of both.
3. **Vertex colours**: check the colour-space pairing (mesh vertex colours linear vs sRGB; shader converts once). Double conversion looks washed out or too dark: bake once (`vertex-color-baking`).
4. **Lighting parity**: compare ambient mode/colour, fog, directional light, shadow settings, post volume and Color Space between projects before blaming the material.
5. **Scale/transform**: non-uniform parent scale breaks normals and offsets; compare lossy scale and import scale.
6. **Evidence**: render a before/after sheet of the same object on the same background under both setups (`playmode-driver-recipes` for the capture); record which of 1-5 was the cause in the notes.
