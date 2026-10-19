# Roblox Shader Kit Parity Implementation Plan

**Goal:** Build an exact, token-efficient Break & Steal shader/bake contract and a routed image-to-map foundation for future Unity clones.

**Architecture:** Keep the full reference contract on disk, route only phase-required skills, and use compact MapSpec/validator outputs to drive Editor builders. Unity MCP remains authoritative for materialization, compilation, serialized references, screenshots and runtime state.

**Tech stack:** Unity 6 URP, existing project framework, Unity MCP/Editor builders, Python validation scripts, CodeGraph/index when available.

**Spec:** `docs/specs/2026-10-15-roblox-shader-kit-parity-design.md`

## Global constraints

- Preserve the existing dirty worktree and never overwrite another agent's changes.
- Use the bundled `SourceContract` as fidelity evidence; do not paste or duplicate large reference files into instructions.
- Prefer shared material plus baked mesh data; allow minimal justified material families when required by shader/runtime state.
- Use Unity MCP for Editor truth and one writer/claim per shared Unity asset.
- Load only the current phase's skills; remove unused skills from active context after the phase.
- No commits, pushes or destructive cleanup unless explicitly requested.

## Review focus

- Vertex/UV channel meanings must match shader reads, including Linear color and water/lava flags.
- Runtime material creation must not reintroduce per-object static variants.
- Image-derived unknowns must be surfaced instead of silently inventing hidden geometry or gameplay.
- Validators must remain cheap and useful without loading Unity scenes or large source files.
- Unity-only claims require MCP/Editor evidence; static script checks are not enough.

### Task 1: Context-scoped skill routing

**Files:**
- Modify: `skills/clone-pipeline/SKILL.md`
- Modify: `skills/roblox-shader-kit/SKILL.md`
- Modify: `AGENTS.md` only if a concise global rule is required after the skill-level change

**Interfaces:**
- Consumes: phase table and existing `token-efficient-workflow` rules.
- Produces: explicit load/use/unload protocol for feature skills and reference contract.

- [x] Add a phase lifecycle: load only the current phase's skills, record the active set in the clone plan, unload when the phase gate closes, and never treat the full skill directory as prompt context.
- [x] Mark `roblox-shader-kit` as routed for visual/material/bake phases only; keep its SourceContract queryable on disk.
- [x] Verify descriptions and the 200K skill-budget listing remain within the repository budget: hub-visible listing 6,287/8,000 chars (78%).

### Task 2: Contract validator

**Files:**
- Create: `skills/roblox-shader-kit/scripts/validate_contract.py`
- Create: `tools/tests/test_roblox_shader_contract.py`

**Interfaces:**
- Consumes: JSON mesh/material report with `channels`, `materials`, `flags`, `color_space`, and `families`.
- Produces: deterministic JSON/text diagnostics with errors for invalid contract and warnings for justified alternate paths.

- [x] Write tests for valid shared material, invalid channel lengths, illegal flags/slots, gamma colors in Linear mode, per-object static variants and justified material families.
- [x] Implement a dependency-free validator with compact output and non-zero exit on errors.
- [x] Run the focused test file and then the repository test/lint gates.

### Task 3: Compact MapSpec contract

**Files:**
- Create: `skills/roblox-shader-kit/assets/map-spec.schema.json`
- Modify: `skills/roblox-shader-kit/SKILL.md`
- Create: `skills/roblox-shader-kit/references/map-spec.md`

**Interfaces:**
- Consumes: image evidence and GDD facts.
- Produces: deterministic part/surface/chunk/camera data consumed by the Editor builder.

- [x] Define the smallest schema that preserves geometry, surface ids, material family, dynamic exclusions, chunking, camera and unknown evidence.
- [x] Document water/lava/sand and shared-material fallback rules without hard-coded per-game balance.
- [x] Validate the schema examples with the contract validator.

### Task 4: Unity bake/builder parity foundation

**Files:**
- Modify: `skills/roblox-shader-kit/assets/roblox-shader-kit/Editor/RobloxMaterialFactory.cs`
- Modify: `skills/roblox-shader-kit/assets/roblox-shader-kit/Editor/RobloxSurfaceMesh.cs`
- Create: `skills/roblox-shader-kit/assets/roblox-shader-kit/Editor/RobloxMapBuilder.cs`

**Interfaces:**
- Consumes: validated MapSpec and material-family contract.
- Produces: persisted mesh/chunk objects, separate collider inputs, and bake report.

- [ ] Preserve exact shader inputs while fixing box/world UV and linear color behavior.
- [ ] Build static geometry by compatible family/chunk, excluding dynamic and unsupported renderers.
- [ ] Add idempotent Editor menu/builder entry points with stop-Play-Mode/idle guards and one-segment-at-a-time output.
- [ ] Compile and inspect through Unity MCP in a target project.

### Task 5: Image-to-map routing and validation

**Files:**
- Modify: `skills/clone-pipeline/SKILL.md`
- Modify: `skills/roblox-shader-kit/SKILL.md`
- Create: `skills/roblox-shader-kit/references/image-to-mapspec.md`

**Interfaces:**
- Consumes: supplied reference image(s), MapSpec, shader contract.
- Produces: explicit inferred facts, unknowns, surface assignments and A/B capture checklist.

- [ ] Route image analysis only when the current GDD/reference supplies map visuals.
- [ ] Require a compact inference report before generation; no hidden topology guesses.
- [ ] Verify fixed-camera screenshot comparisons at the target aspect ratios and report unknown/unverified items.

### Task 6: Integration and wiring

- [ ] Run the active skill-budget/index gates and focused validator tests.
- [ ] Use the actual Unity MCP project to install/materialize the kit, compile, inspect Console and run a smoke bake.
- [ ] Verify shared material/family counts, UV/color contract, chunk/culling state and water/lava sample surfaces.
- [ ] Capture A/B screenshots and record verified vs unverified results.
- [ ] Update feedback notes and handoff; unload phase-only skills before the next task.

## Self-review checklist

- Every spec acceptance criterion maps to a task.
- The shader/source contract stays on disk rather than in prompts.
- The plan permits alternate material paths only with explicit constraints and measurements.
- Image-only unknowns remain visible.
- Unity claims are gated on MCP evidence.
