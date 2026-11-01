---
name: procedural-stud-shader-recipes
description: "Shader recipes for procedural brick/stud and bevel surface layers, vertex-colour glow and saturation boosts, SRP Batcher safe. Use when giving models a Lego or toy-brick look with a shader instead of geometry."
triggers: stud, lego, brick, bevel, shader, vertex color glow, saturation, srp batcher, voxel look
---

# Procedural stud shader recipes
- Studs and bevel lines come from a world- or object-space grid in the fragment shader, not geometry.
- Glow from vertex alpha (document the convention per shader and convert at import, never mix silently).
- Saturation/vibrance as material properties; keep SRP Batcher compatible (all properties in CBUFFER).
- Shaders loaded via Shader.Find must be in Always Included Shaders.
- One material per family; see `one-material-world-shader`, `roblox-shader-kit`.
