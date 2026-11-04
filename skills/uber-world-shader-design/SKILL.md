---
name: uber-world-shader-design
description: "Design a light shared world shader for mobile: one material per biome renders lego/checker/neon/lava/ice via per-vertex type and params, bloom via HDR emission, transparent mesh pre-sorted. Use when planning world shader, map combine, or special-surface materials."
triggers: uber shader, one material, combined mesh, vertex data, lava, neon, ice, transparent sort, world shader, sketchshader, shared shader, mot material
---

# Uber world shader (design rules)
- Colour in COLOR.rgb (linear, written once), alpha in COLOR.a, surface type id + params in uv1, box UV in uv0 (already scaled by tiling). The shader picks the look with lerp/step math, no per-type keywords; only quality keywords (SKETCH_LOW, MAIN_SHADOWS).
- Bloom: emissive types output HDR > 1 from vertex params; the post volume does the rest. Scroll: `_Time` offset gated by the type flag.
- Tunables are global shader properties (`_Sketch*`) pushed by one ScriptableObject profile; absent from per-material CBUFFER so materials never mask them; safe defaults when unset.
- Authoring component keeps one shared material asset + MaterialPropertyBlock preview; combine bakes data into vertices (see `scene-bloat-play-crash`).
- Transparent: separate shared material, ZWrite Off, ONE mesh per biome with triangles pre-sorted back-to-front along the view axis; overlapping layers viewed from both sides need alpha-to-coverage/dither or a small per-frame sorted mesh.
- Verify before trusting: pixel diff (`mean < 0.5%`, p99 < 6/255) of combined vs reference objects per surface type; A/B cube test under identical lighting; draw-call count in Frame Debugger. Colour/yellow-vs-green problems: compare ambient, fog and volume first (`render-parity-debugging`).
