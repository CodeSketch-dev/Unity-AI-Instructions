---
name: roblox-shader-kit
description: "Routed Roblox/Lego environment foundation for visual recon, materialization, mesh baking, chunk/culling and render validation; load only when the current task needs those phases."
---

# Roblox environment kit

Use the bundled payload `assets/roblox-shader-kit/` as the visual foundation for Roblox/Lego-style clones. Copy it into the target project at `Assets/_Game/RobloxShaderKit/` with all `.meta` files preserved. Do not require a UPM package or reference/inspect an old game project during generation.

The payload is a rendering workflow, not only a shader file. It must include the batched shader/HLSL, `VertexTypeCompoment`, `VertexColorMetalMode`, `TextureTypeComponent` (runtime and editor partial), texture data model, surface textures, and their metadata. Preserve the implementation of the authoring scripts; do not replace them with a simplified vertex-color script.

`assets/roblox-shader-kit/SourceContract/` is the fidelity source of truth captured from the proven reference implementation. It contains the original shader/HLSL behavior, shared material property layout, texture set, texture data asset and authoring scripts. Use it to build a generic target-side installer/material factory; do not copy reference gameplay, scenes, prefabs or balance data.

## Pipeline

1. Detect the GDD visual contract: block/stud geometry, vertex-color look, surface families, transparency, water/lava, lighting and mobile target.
2. Copy the bundled payload to `Assets/_Game/RobloxShaderKit/`. Stop Play Mode before import/refresh. If the target lacks Odin Inspector, adapt the authoring attributes before compile; do not add a second serialization framework.
2a. Materialize the source contract before map generation: prefer one shared material with the source shader's exact albedo slots, checker detail, LEGO detail, LEGO normal and texture-data mapping. If the GDD or shader state requires separation, define the smallest material families that preserve the look and document why; do not create per-color replacement materials merely for convenience. Never treat copied source `.mat` YAML as final: source GUIDs are not portable. Relink every texture through target `AssetDatabase` paths and verify all required slots are non-null.
3. Resolve Roblox/Environment/BatchedSurface and compile a one-object smoke test before map generation. If the shader is missing, unsupported, or fails to compile, stop and report the exact error; never silently fall back to URP/Lit/Standard.
4. Start with one shared opaque batched material and add only the smallest transparent/metal/VFX or surface-family variants required by the GDD, shader state, lighting, culling or runtime behavior.
5. Prefer baking static color and surface variation into mesh channels so compatible environment meshes share a material; use the proven layout when that path fits: box-mapped UV0, flags/slot/tiling in UV1, movement in UV2, and vertex color. When baking cannot preserve a required feature, use the minimum justified material families and optimize their variants, texture usage and batching instead. Attach and initialize `VertexTypeCompoment`/`TextureTypeComponent` only on authoring roots, then bake static output; do not leave unnecessary per-object material instances. Do not paint flat colors directly onto primitives as a substitute for the selected contract.
6. Bake static geometry by compatible material/shader variant. Combine only static renderers with matching material/lightmap/visibility constraints; keep gameplay colliders and dynamic objects separate.
7. Generate decor LODs or distance-cull groups from authored bounds. Preserve landmarks, interactables, VFX and readable silhouettes.
8. Validate shader compilation, vertex colors, material count, missing references, batch groups, LOD/culling, lightmap compatibility and mobile draw/overdraw budgets. For component authoring, verify component execution. For direct procedural baking, run `RobloxSurfaceMesh.Validate` and inspect rendered surfaces; components are not required on baked output.
9. Run a reference-composition gate: compare a fresh Unity capture against the supplied image for silhouette, biome order, palette, landmark density, depth, camera framing and detail density. A primitive-only terrace blockout fails this gate.
10. Save and verify through Unity MCP. Refresh/import only after Play Mode is stopped and the Editor is idle.

## MapSpec routing

Load `references/map-spec.md` and `assets/map-spec.schema.json` only when the current task has reference images/GDD map evidence or is building the map. Keep MapSpec compact: source evidence, surface ids, material families, static/dynamic parts, chunks, camera and explicit unknowns. Do not load the full SourceContract into the prompt; query it on disk and emit a compact bake report instead.

When the input is an image, require the upstream `visual-evidence` gate and use `references/image-to-mapspec.md` first; emit the MapSpec before creating Unity objects. The image can establish visible composition and surface cues, but it cannot prove hidden topology, collision or gameplay; keep those facts explicitly unknown.

Before handing work to the Unity map builder, validate `gdd/_generated/map-spec.json` with the compact artifact preflight and include the exact validation result in the MCP dispatch evidence. Unity scene creation is not allowed to substitute for a missing or invalid MapSpec.

## Transfer contract

Use `scripts/copy_payload.py <unity-project-root>` or an equivalent MCP/editor transfer. Copy shader/HLSL, textures, authoring scripts and their `.meta` files as one unit; never copy only the shader. Re-read the target paths after transfer, refresh through MCP, compile, inspect the Console, and run one sample bake before generating the full map. The agent may create the target material profiles and `TextureDataAsset` through an idempotent Editor builder; do not hand-write Unity YAML.

## Non-negotiable output

- GDD-driven environment only; never invent a dig, treadmill, weapon or other feature.
- Minimize material state: try the shared-material + baked-mesh-data path first, then use the smallest justified material families when sharing is incompatible or measurably worse.
- Prefer vertex colors and UV metadata for compatible static variation; never create duplicated per-object materials merely to represent a color.
- Any alternate material path must state the constraint that prevented sharing and validate material count, batches, memory and visual fidelity.
- Shader fallback is forbidden when the GDD selects this kit.
- A material-only or flat-`Mesh.colors` approximation is not equivalent to the reference shared-material path. Use the full vertex contract when compatible; otherwise preserve the required visual behavior through the smallest validated alternative.
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
