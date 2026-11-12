---
name: house-style-foundation
description: "Use when starting a new Roblox-to-Unity clone or game: build the compact foundation profile (framework API map, persistent root and canvas contract, boot, collision registry, data/factory/state/pool) from the reference projects before gameplay work, SketchEngine first."
triggers: foundation, house style, reference profile, framework map, new game foundation, persistent root, boot order, global canvas, knife tower style, kt style, nen tang du an, phong cach nha, du an moi
---

# House-style foundation

Use once at the start of a new game or Roblox-to-Unity clone. Read the reference projects read-only and emit a compact `docs/reference-foundation.md`; do not copy production files. Always prefer SketchEngine (the upgraded framework): teach and write the SketchEngine form, and check the installed package API before writing code. Reference projects may run an older version of the same framework; `references/reference-profile-v1.md` lists each of their facts with the SketchEngine form to write. Roles of the reference projects: `references/reference-project-matrix.md`.

## Required profile

Record only verified facts:

- Unity version, render pipeline, target platform, package/framework version and namespace.
- Persistent root (`GameSingleton`-class prefab) and global Canvas contract: ownership, render mode, sorting, scaler, safe-area/root/popup containers, EventSystem.
- Boot order and initialization owner (`RuntimeInitializeOnLoadMethod`, splash/home/game entry).
- Collision dispatch contract: installed `OptCollisionRegister`/sensor API, actor callback owner, interface family and registration lifecycle.
- Data persistence (`DataBlock<T>`), factory singleton (`Factory_*`), state machine, event bus, caching base, pooling.
- Supporting services that affect every game: audio factory/config + BGM crossfade/cancellation, localization event lifetime, scene loading/fade/loading-progress, settings binding, camera manager/input boundary, low-end device policy and pool initialization.
- Folder, namespace, naming and performance rules that are actually present in the target (`project-structure-layout`).
- Comparison: shared contract vs project-specific delta; never infer an API of one framework version from a project on another.

## Generation hard-gates

Before gameplay/UI tasks may start, the target must have:

1. The detected framework API map; never invent or mass-replace namespaces.
2. A boot/foundation task that creates or wires the persistent root prefab and global Canvas contract (`persistent-root-prefab`).
3. A collision task using the installed registry/sensor API; no parallel callback/lookup path.
4. Data/factory/state/pool scaffolding using installed framework types, not replacements (`house-code-patterns`).
5. A compact profile and a verification checklist. If a fact is unknown, mark it `UNKNOWN` and stop the dependent task instead of guessing.

## Next skills (the real foundation is a prefab and a folder layout, not only a document)
`persistent-root-prefab` (root, canvases, boot), `project-structure-layout` (folders, naming, audit), `house-code-patterns` (decision table for Data/Factory/Event/State/Pool/collision), `new-game-bootstrap` (template and installer).

## Existing leaf-skill routing

Do not load all of these at foundation time. Pass the profile path to the orchestrator, then load only the leaf skill when the GDD needs it:

| Contract | Leaf skill |
|---|---|
| Global Canvas, popup/view roots, TMP containment | `unity-ui`, `ui-text-tmp`, `ui-popup-anatomy`, `ui-validator` |
| AudioConfig/AudioManager, volume binding, BGM crossfade | `game-audio-system`, `sfx-variation-ducking` |
| Locale event lifecycle and font/text localization | `localization-pipeline`, `ui-localization`, `ui-text-tmp` |
| Scene fade, loading progress, cancellation | `scene-flow-loading`, `async-cancellation` |
| Camera and low-end camera policy | `freelook-third-person-camera`, `device-tier-policy` |
| Touch/joystick input | `mobile-input-controls` |
| Pool config/prewarm/return lifecycle | `pool-everything` |
| Runtime device/physics/render policy | `device-tier-policy`, `mobile-urp-lighting-baseline`, `mobile-perf-audit` |

Mesh combine and vertex-color baking are intentionally not duplicated here; use the existing mesh/baking skills only when the GDD or target requires them.

## Token policy

Load this skill plus the compact profile only for the foundation gate. Later tasks receive the profile path and the relevant leaf skill names, not this full file or the reference project's source.

## Verification

- `docs/reference-foundation.md` exists and contains no unverified claims.
- Framework map matches `Packages/manifest.json` and at least one installed API example.
- Persistent root, Canvas, boot, collision and framework scaffolding are inspected in Unity when MCP is available; otherwise report file-only verification.
- The task graph blocks phase 2+ until this foundation task is complete.
