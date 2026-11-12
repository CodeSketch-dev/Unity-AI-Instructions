---
name: render-parity-debugging
description: "Find why imported or cloned models look worse than in the reference project: shader, textures, MaterialPropertyBlock, vertex colour colour space, lighting parity. Use when a ported asset renders flat, washed out, textured wrong or differently lit."
triggers: render parity, original model, wrong size, mesh rotation, missing teeth, model goc, sai kich thuoc, size khac, bi phang
---

# Render parity debugging

Fix only the divergent path; do not re-author materials blindly.

## Original geometry and custom-shader recovery gates
- Preserve the original mesh and authored scale while investigating. Never replace an existing model with primitives or fit its visual dimensions to prototype collision bounds. Compare the same camera aspect, viewport and pose before changing size; record source units and projected pixel pitch separately.
- A fallback shader may silently ignore custom texture slots, alpha masks and repeat/scroll floats. Inspect serialized material properties and texture alpha before changing geometry. Dump vertex/UV pairs to identify the longitudinal axis; object XYZ does not determine UV direction. Restore the original texture on the original mesh, capture in Play and label unknown shader math as inferred.
- For mesh particles, verify a nonzero rotated fixture through native baked vertices against source vertices transformed by the simulation pose. Explicit 3D rotation flags and axis/sign can differ from scalar assumptions. Require a numeric vertex-error tolerance; a screenshot or zero-angle fixture alone cannot prove correct orientation.

1. **Same inputs?** Compare material asset, shader, keywords and every texture by GUID/hash with the reference (`asset-transfer-closure`). Different import settings (sRGB flag, compression) count.
   Inspect shader source for `DummyShaderTextExporter` across all imported paths, including lowercase `Resources/shaders`. Keep dummy exports outside active Assets/Packages. `Shader.Find` can select a broken duplicate with the same name: bind the verified shader asset path and read back material.shader. Serialized material values cannot reconstruct missing Shader Graph math; glyph quads, a gray palette or flattened depth require shader-path and color-space checks plus a fresh Play capture.
2. **Per-renderer MaterialPropertyBlock**: the reference may always write a block (colour, tint); a renderer with no block, or a cleared one, exposes the raw texture/overlay and looks different. Write the same block on the same path, or compare `GetPropertyBlock` dumps of both.
3. **Vertex colours**: check the colour-space pairing (mesh vertex colours linear vs sRGB; shader converts once). Double conversion looks washed out or too dark: bake once (`vertex-color-baking`).
4. **Lighting parity**: compare ambient mode/colour, fog, directional light, shadow settings, post volume and Color Space between projects before blaming the material.
5. **Scale/transform**: non-uniform parent scale breaks normals and offsets; compare lossy scale and import scale.
6. **Evidence**: render a before/after sheet of the same object on the same background under both setups (`playmode-driver-recipes` for the capture); record which of 1-5 was the cause in the notes.
7. **A/B in the same scene**: drop one real reference-style object next to the combined/baked mesh under identical lighting and sample screenshot pixels (PIL `getpixel`); equal pixels = the material path is fine, so the gap is lighting/atmosphere. Typical cause of 'green instead of yellow-lime': a per-biome atmosphere default (cool ambient, near fog) overriding the scene's RenderSettings, plus saturation/contrast in the shared volume crushing the red/blue channel.
