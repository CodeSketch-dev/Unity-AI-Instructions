---
name: blender-procedural-assets
description: "Generate game meshes procedurally with headless Blender Python: archetype libraries, vertex-colour palettes, emission whitelist, export checks. Use when building props, pets or eggs from scripts instead of hand-modelling."
triggers: blender, procedural, mesh, fbx, vertex color, emission, glow, headless, python, lowpoly, voxel, prop, tao model
---

# Blender procedural assets
Headless run: `blender.exe -b --python script.py` (detect the installed version first).
- Build parts from a small shared archetype library (box, bevel box, plate); one script per family, deterministic seed, one material, colours as vertex colours.
- Emission discipline: whitelist ONE emissive colour, sweep the face list once before export instead of chasing glow primitive by primitive.
- Saturation is hue distance, not value: a near-black close to the ambient hue washes to grey; shift the hue, do not darken. Measure the low-saturation pixel share before/after.
- Check before import: tri budget (`character-perf-budgets`), scale/axes, applied transforms, no stray root renderers.
- Import and wire in the Editor with `art-direction-asset-pipeline`; record provenance.
