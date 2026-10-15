---
name: roblox-shader-kit
description: "Shared Roblox/Lego-style environment foundation: vertex-color surfaces, batched URP shader, minimal material profiles, water/lava/sand variants, static mesh combine, decor LOD and bake validation. Auto-load when GDD/environment evidence calls for Roblox studs or block-built visuals; no manual invocation required."
---

# Roblox environment kit

Use the bundled payload `assets/roblox-shader-kit/` as the visual foundation for Roblox/Lego-style clones. Copy it into the target project at `Assets/_Game/RobloxShaderKit/` with all `.meta` files preserved. Do not require a UPM package or reference/inspect an old game project during generation.

The payload is a rendering workflow, not only a shader file. It must include the batched shader/HLSL, `VertexTypeCompoment`, `VertexColorMetalMode`, `TextureTypeComponent` (runtime and editor partial), texture data model, surface textures, and their metadata. Preserve the implementation of the authoring scripts; do not replace them with a simplified vertex-color script.

`assets/roblox-shader-kit/SourceContract/` is the fidelity source of truth captured from the proven reference implementation. It contains the original shader/HLSL behavior, shared material property layout, texture set, texture data asset and authoring scripts. Use it to build a generic target-side installer/material factory; do not copy reference gameplay, scenes, prefabs or balance data.

## Pipeline

1. Detect the GDD visual contract: block/stud geometry, vertex-color look, surface families, transparency, water/lava, lighting and mobile target.
2. Copy the bundled payload to `Assets/_Game/RobloxShaderKit/`. Stop Play Mode before import/refresh. If the target lacks Odin Inspector, adapt the authoring attributes before compile; do not add a second serialization framework.
2a. Materialize the source contract before map generation: one shared material with the source shader's exact albedo slots, checker detail, LEGO detail, LEGO normal and texture-data mapping. Do not create per-color replacement materials with empty slots. Never treat copied source `.mat` YAML as final: source GUIDs are not portable. Relink every texture through target `AssetDatabase` paths and verify all required slots are non-null.
3. Resolve Roblox/Environment/BatchedSurface and compile a one-object smoke test before map generation. If the shader is missing, unsupported, or fails to compile, stop and report the exact error; never silently fall back to URP/Lit/Standard.
4. Create one shared opaque batched material and only add transparent/metal/VFX profiles when the GDD requires them.
5. Generate environment meshes with vertex colors and surface flags; never create one material per prop or biome. The delivered bake must write the proven layout: box-mapped UV0, flags/slot/tiling in UV1, movement in UV2, vertex color, and one shared batched material. Attach and initialize `VertexTypeCompoment`/`TextureTypeComponent` only on authoring roots, then bake static output; do not leave hundreds of per-object material instances. Do not paint flat colors directly onto primitives as a substitute.
6. Bake static geometry by compatible material/shader variant. Combine only static renderers with matching material/lightmap/visibility constraints; keep gameplay colliders and dynamic objects separate.
7. Generate decor LODs or distance-cull groups from authored bounds. Preserve landmarks, interactables, VFX and readable silhouettes.
8. Validate shader compilation, vertex colors, material count, missing references, batch groups, LOD/culling, lightmap compatibility and mobile draw/overdraw budgets. For component authoring, verify component execution. For direct procedural baking, run `RobloxSurfaceMesh.Validate` and inspect rendered surfaces; components are not required on baked output.
9. Run a reference-composition gate: compare a fresh Unity capture against the supplied image for silhouette, biome order, palette, landmark density, depth, camera framing and detail density. A primitive-only terrace blockout fails this gate.
10. Save and verify through Unity MCP. Refresh/import only after Play Mode is stopped and the Editor is idle.

## Transfer contract

Use `scripts/copy_payload.py <unity-project-root>` or an equivalent MCP/editor transfer. Copy shader/HLSL, textures, authoring scripts and their `.meta` files as one unit; never copy only the shader. Re-read the target paths after transfer, refresh through MCP, compile, inspect the Console, and run one sample bake before generating the full map. The agent may create the target material profiles and `TextureDataAsset` through an idempotent Editor builder; do not hand-write Unity YAML.

## Non-negotiable output

- GDD-driven environment only; never invent a dig, treadmill, weapon or other feature.
- Minimal material set: shared material first, per-surface variant only when shader state requires it.
- Vertex colors are authored/baked into mesh data, not simulated with duplicated materials.
- Shader fallback is forbidden when the GDD selects this kit.
- A material-only or flat-`Mesh.colors` approximation is not an implementation of this kit. Use the full vertex contract through the bundled builder or proven authoring components.
- Combined meshes never include objects that move, animate, toggle, receive runtime damage, or need independent culling.
- A generated map is not done until the scene opens cleanly, shaders compile, references resolve, and a fresh Play Mode path is visually checked.

## Package boundary

## Executable procedural path

- Call `RobloxShaderKit.Editor.RobloxMaterialFactory.Ensure()`; it relinks the six required textures and rejects unsupported shaders. Inspect `sharedMaterial`, never `renderer.material` (which creates instances).
- Build custom geometry with `RobloxSurfaceMesh` (`Quad`, `Box`, `Beam`, `Build`). It bakes linear COLOR, metric UV0, UV1 flags/slot/checker/emission, UV2 movement, normals and tangents. Do not rescale the finished transform without rebuilding metric UVs.
- Plain colored studs: flags `3` (texture + LEGO), slot `0` (white). Flags `2` alone disable the texture branch. Water/lava/sand slots are `1/2/3`; never assign water to ordinary foliage/walls. These are shader protocol constants, not game balance.
- Write a persistent target-side Editor builder using these APIs. Map dimensions, biome order, prop shapes and camera come from current reference evidence, not kit defaults. Keep generated world coordinates longitudinal on X/Z; do not stack biome floors on Y.
- Generate multi-part silhouettes (branched trunks, stepped/lobed crowns, snow caps, segmented cactus, layered rocks), not single-box stand-ins. Chunk static geometry spatially; retain independent objects for gameplay and LOD/culling ownership.
- A successful compile is not visual acceptance. Capture the actual camera after generation, compare to reference, correct camera/lighting/detail and explicitly report unverified or missing elements.

This package contains reusable rendering/bake infrastructure only. Game-specific scenes, prefabs, balance, quests, economy, gameplay scripts and reference assets stay in the target project.
