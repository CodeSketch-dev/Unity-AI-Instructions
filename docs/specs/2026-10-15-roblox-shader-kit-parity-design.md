# Roblox Shader Kit Parity Design

**Date:** 2026-10-15  
**Target project:** Unity-AI-Instructions skill suite  
**Reference projects / evidence:** `docs/pipeline-catalog/11-thunder-break-egg-asset-pipeline.md`, `docs/pipeline-catalog/18-roblox-world-kit.md`, bundled `skills/roblox-shader-kit/assets/roblox-shader-kit/SourceContract/`  
**Fidelity:** exact for the reusable Break & Steal shader/bake contract; faithful for image-inferred map composition until Unity A/B captures prove parity

## Goal

Given a reference map image and a compact per-game map spec, the clone pipeline selects the correct Roblox material path, generates compatible geometry/surface data, bakes and batches the map, and validates the result against the Break & Steal rendering contract without loading the whole reference project into agent context.

## Constraints

- Unity 6 mobile-first; preserve the target project's installed URP/framework and use Unity MCP for Editor truth.
- The bundled `SourceContract` remains the on-disk fidelity source; agents query only the relevant symbols/files through indexes or CodeGraph.
- Shared material plus baked vertex/UV data is the preferred path, not an absolute requirement. If incompatible, use the smallest justified material families and record the constraint.
- Do not hand-author target Unity YAML or `.meta` files; use Editor builders/MCP for materialization.
- Do not overwrite other agents' changes; one writer owns each scene/prefab/builder output.
- Skills are phase-scoped: route only the skills needed for the current task, unload them after the phase, and keep the default model-visible listing compact.

## Decisions and assumptions

| Decision | Chosen | Alternatives considered | Why |
|---|---|---|---|
| Source fidelity | Preserve shader/HLSL/property/channel contract on disk | Rewrite a smaller approximation | Exact rendering behavior matters more than a superficially simpler shader |
| Agent context | Compact spec + indexed targeted reads | Paste full source/reference files | Reduces prompt size and repeated exploration |
| Material strategy | Shared material first; minimal families when required | Force one material everywhere | Water, transparency, tools, characters and lighting may require different states |
| Image input | Image informs composition/surface evidence; `MapSpec` carries explicit geometry/runtime facts | Infer hidden topology blindly | A single image cannot prove unseen geometry or gameplay collision |
| Bake location | Editor-time persisted mesh assets and chunk objects | Runtime mesh combining | Matches the reference pipeline and avoids load-time spikes |

## Architecture

1. `SourceContract/` stores the exact shader/HLSL/material/channel reference.
2. `MapSpec` is a compact, game-local description of palette, part primitives, surface ids, chunk size, dynamic exclusions, camera and image evidence.
3. A validator checks the spec and the baked mesh contract before Unity mutation.
4. An Editor builder materializes/relinks the shared material, builds meshes/chunks, keeps colliders separate, and writes an inspectable report.
5. Unity MCP refreshes/compiles/reads back the actual assets and captures fixed-camera A/B screenshots.
6. The orchestrator loads only the current phase's skills and records the result in the clone plan/handoff.

## Data and assets chain

`reference image + GDD evidence -> MapSpec -> spec validator -> RobloxMaterialFactory -> RobloxSurfaceMesh/map baker -> persisted mesh/chunk assets -> scene wiring -> Unity MCP compile/read-back -> render/batch report`

Material families remain explicit: map/decor batched surface, vertex-color-only assets such as eggs, tool/FX materials, and character materials. Static map variation must not become per-object material clones.

## Behavior details

- Surface flags and texture slots are validated before baking.
- Linear vertex colors are required when the project color space is Linear.
- UV channel meaning is stable: UV0 box-mapped surface coordinates, UV1 flags/slot/tiling/emission, UV2 movement; exceptions must be declared by material family.
- Water/lava are selected only when image/GDD evidence supports them; the builder writes the required slot/flags/movement and reports unknowns instead of inventing them.
- Transparent, multi-submesh, mixed-normal, dynamic, interactable and independently culled objects are excluded from static batches unless a material-family rule explicitly permits them.
- Chunking, distance culling, shadow policy, collider generation and NavMesh rebake are separate validated stages.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Skill routing loads too much context | High | Phase-scoped load/unload rules and compact hub descriptions |
| Image does not reveal hidden geometry | High | Require MapSpec facts or mark them unknown; never silently invent |
| Baked mesh channels drift from shader expectations | Medium | Contract validator plus Unity smoke mesh and read-back |
| Concurrent agents rebuild stale assets | High | Workspace guard, claims, one writer, re-read before save |
| Shader parity changes across URP versions | Medium | Compile/pass/property gate in the target project, not source-text trust alone |

## Out of scope

- Reproducing unseen map topology from one image with no additional evidence.
- Copying Break & Steal gameplay, scenes, prefabs, balance, or proprietary assets into the generic kit.
- Claiming device performance improvements without profiler/device evidence.

## Acceptance criteria (checkable)

- [ ] Only the current phase's skills are routed; unused skills are not included in the active context/listing.
- [ ] Contract validator rejects missing/invalid UV channels, flags, colors, material references and unjustified material variants.
- [ ] Target Unity project compiles the shader and a one-object smoke mesh with no new Console errors.
- [ ] A representative map bake produces a persisted mesh/chunk report with material families, renderer counts, vertex counts and culling state.
- [ ] Water/lava evidence maps to the correct surface flags/slots and is visible in a Unity capture when present.
- [ ] A/B captures compare the fixed camera at the required aspect ratios; unknown image-derived facts are reported rather than guessed.
- [ ] Concurrent edits are guarded and the handoff records what later agents must reload.
