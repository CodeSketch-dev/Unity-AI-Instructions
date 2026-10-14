---
name: world-batching-culling
description: Make big static worlds cheap on low-end mobile: bake meshes/materials, chunked distance culling, parity and render-stat checks. Use when a map has thousands of renderers, high draw calls, or on "optimize the map".
---

# World batching and culling

Most mobile frame time in a Roblox-style world is renderer/material count, not triangles. The measured win from this approach: map decor went from 1290 renderers / 97 materials to 146 renderers / 1 material, with 28-38 of 136 decor chunks active at a time. Use the same pipeline and measure your own numbers.

## Method
1. **Measure first.** Count renderers, distinct materials, batches and set-pass calls in Play Mode (profiler / frame debugger / MCP stats) for a representative camera. Record in the spec.
2. **Classify objects**: static opaque (bake), decor (bake into chunks + cull), dynamic/animated/toggled/destroyed (leave alone), transparent / custom shaders / mixed-normal meshes (leave unbatched unless proven safe).
3. **Bake in the Editor** (an idempotent, chunked tool: `editor-tool-authoring`): group by material-compatible keys, write per-vertex data for properties that differed per material (colour, texture index, emission, lego/checker flags, movement), evaluate procedural UV mapping per vertex when exact, produce **one mesh + one material per chunk**. Keep the authoring objects in the scene as the source; a runtime component hides them at Awake (early execution order) and shows the baked meshes, so re-baking after edits is possible.
4. **Material/shader for the batch**: clone the project's lit shader with the same math as the source material shader; include every pass the active renderer needs (Forward, GBuffer for deferred PC renderers, ShadowCaster, DepthOnly, DepthNormals). A missing pass renders correctly in one tier and wrongly in another.
5. **Shadows and reflections**: baked sources that never cast shadows must keep ShadowCastingMode Off after baking; keep environment reflections/specular enabled when the source had them, otherwise the look shifts.
6. **Chunking and culling**: split decor by spatial chunk (e.g. 45 m); a lightweight culling component shows chunks inside a show distance and hides beyond a larger hide distance (hysteresis avoids flicker). Choose distances so that decor visible from the **actual gameplay camera** is never culled early (users notice pop-in at the rim of the world); use shorter distances for ground-level clutter than for tall landmarks. Store per-chunk distances at bake time. For many tiny objects with no chunk structure use `CullingGroup` (event-driven) instead of per-frame loops.
7. **Components that build materials per instance** (ExecuteAlways material builders): never mass-instantiate them; bake instead and keep one instance per combined mesh if the shader still needs it.
8. **Verify parity**: render A/B screenshots from several camera positions (e.g. 8) with the source vs baked; the mean pixel difference should be tiny (target < 0.5%, measured 0.2% before); check on both the mobile (forward) and PC quality tiers.
9. **Re-measure** and report before/after: renderers, materials, batches, set-pass, active chunks, vertices drawn, memory of baked meshes, and load/bake time. Say whether it was measured on a device.
10. **Stability**: save the scene after each chunk; bake one segment per MCP call.

## Pitfalls
- Static flag on a combined object re-merges stale meshes.
- Overwriting a mesh asset in place can leave a stale GPU mesh (delete + recreate).
- Segment joints must align (no steps between modular segments); verify after widening or changing segments.
- Decor placed behind walls is invisible and wasted; place it where the gameplay camera can see it.
- Keep gameplay paths clear: decor must not sit on routes, spawn points or interaction areas (`zone-level-design`).
