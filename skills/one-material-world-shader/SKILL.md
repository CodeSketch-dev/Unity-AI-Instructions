---
name: one-material-world-shader
description: Render the whole world with one opaque material (plus one alpha) by moving per-part variation into vertex data, with the Game/RobloxWorld shader contract. Use when setting up world art, writing the world shader, or fixing material counts and draw calls.
---

# One material, data in vertices

Goal (user decision): world = 1 opaque material + 1 alpha material; per-family materials are the fallback only when one material cannot render correctly (reports 11, 18).

## Why
The Roblox clones' per-part look (`TextureTypeComponent`, `[ExecuteAlways]`) clones a material per instance: thunder-break-egg had 3767 renderers / 149 materials. Moving the data to vertices gave 1 material per segment (decor 1290/97 -> 146/1; 93 batches in Play Mode, Editor, not measured on a device) (report 11, VERIFIED). A combiner can only merge one material, and MaterialPropertyBlock removes a renderer from the SRP Batcher, so colour must live in vertices.

## Rules
- No per-instance material builders, no MPB on static renderers; a tiny MPB only on a handful of dynamic objects.
- Exceptions that stay separate: alpha (Glass/Ice/ForceField), character skins (OmniShade), hull outline, FX/trails, sky.
- The shader declares everything in one `CBUFFER_START(UnityPerMaterial)`, `multi_compile_instancing`, `multi_compile_fog`. Passes: Forward + ShadowCaster + DepthOnly (+ GBuffer only if a Deferred renderer is active, as on BSE's PC renderer). Fade/alpha variants are a SEPARATE shader (property-driven blend loses the SRP Batcher).
- Validate: `Shader.IsSRPBatcherCompatible`, material census of world renderers, no MPB on static.

## `Game/RobloxWorld` channel contract (design, INFERRED; unproven in the Editor)
| Channel | Content |
|---|---|
| COLOR | base colour LINEAR (`vertex-color-baking`), a = emission mask or opacity |
| uv0 | stud-space UV, 1.0 = one stud, box-mapped per dominant normal axis, baked |
| uv1 (x,y,z,w) | flags, surface id/atlas slot, param (checker tiling), emission strength |
| uv2 | scroll velocity (conveyor, lava) |
| uv3 | smoothed normals for hull outline meshes only |
Flag bits (superset of the working Problox 1/2/4/8/16): 1 texture, 2 stud top, 4 checker, 8 scroll, 16 emission, 32 inlet, 64 neon, 128 runtime triplanar for unbaked scaled primitives.

Cost targets: plain surfaces need no texture fetch; studs are procedural (`frac` + `fwidth` AA, fake bevel from the light direction) with a texture fallback; patterns come from ONE atlas sampled once; lighting is main light Lambert/half-lambert + flat ambient + fog, no additional lights, no env reflection. A `_ROBLOX_LOWEND` keyword drops stud AA, atlas lookup and wrap light. The ALU budget (<= 40 on a Mali-G52 class GPU) and `fwidth` shimmer on Mali are UNVERIFIED: profile with the GPU vendor compiler/device before relying on it.

Related: `roblox-world-kit` (surfaces, palette, parts), `mesh-merge-baker`, `world-batching-culling`.

## Gotchas (tint)
- A custom batched shader may ignore `_BaseColor` entirely: read the shader source before relying on material tint.
- In Linear colour space `Material.SetColor` linearises the value, so store tint ratios through a linear-to-gamma step to get the intended result.
- Compute tint ratios from the real mesh vertex colours, not a constant reference colour.
