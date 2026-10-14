# 11 - thunder-break-egg: controlled asset pipeline and lessons

Source: `C:\Unity\GitProject\thunder-break-egg` (Unity root `break-and-steal-unity/`, game "Break & Steal Egg", a Steal-an-Egg clone, SketchEngine, URP, Linear). Read-only reverse engineering.
Notation: `P:` = `break-and-steal-unity/Assets/_Game/`, `N:` = `docs/feedback-notes.md` (line numbers), `H:` = `docs/agent-handoff.md`. Tags: **V** verified (file read), **I** inferred.

## 0. Headline findings (corrections to the brief)

| # | Finding | Tag |
|---|---|---|
| 1 | There is NO single global material. There are several single-material FAMILIES, each fed by its own baker: map + decor + cage + shops = `M_Problox_Batched`; eggs and zone-11 boss = `M_VertexColor` (Problox ShaderGraph); pickaxes = `M_Pickaxe_VertexColor`. Characters/skins stay on ~136 OmniShade materials (user forbade stripping them). | V `P:Materials/`, `P:Shaders/`, N:246 |
| 2 | Meshes are NOT imported through FBX/ModelImporter. They are procedurally generated or merged by Editor scripts and saved as `.asset` Mesh files (148 mesh assets). No `ModelImporter`/`isReadable` code exists in `Scripts/Editor`. The 220 FBX are transferred reference art under `_Art/`, later re-baked. | V grep + find |
| 3 | Combining is an EDITOR bake persisted as assets + scene objects, NOT the house-style runtime `MeshSceneCombiner`. The user asked about the runtime combiner (N:69); what shipped is the persisted bake (N:80-81). No loader-screen bake step exists. | V `Map_BatchedStatic.cs`, N:69,80 |
| 4 | Vertex colours are stored LINEAR (`color.linear`) in every baker; this fixed "washed out" visuals. | V `Egg_MeshBaker.cs:71`, `Map_BatchBaker.cs:91,232`, `Pickaxe_Generator.cs:249`, N:177 |
| 5 | Per-object variation without extra materials = (a) extra vertex channels (uv0/uv1/uv2/tangent) for baked static data, (b) `MaterialPropertyBlock` on a few dynamic objects only (Egg_Node, Pet_View, Boss_Guardian, Character_Trail). | V grep, 4 files |
| 6 | The discipline is real but was applied per feature AFTER user complaints (pickaxes, eggs, map, fences, boss hull), not as a project-wide gate from day 1. | V N:172-178,431 |

## 1. Mesh generation / import

| Generator (Editor) | Input | Output | Conventions | Tag |
|---|---|---|---|---|
| `Scripts/Editor/Pickaxe_Generator.cs` (1510 lines) | spec tables `LOOKS`, `FX_*`, `TRAILS`; 15 tiers now (37 originally) | `Meshes/Pickaxe/*.asset` (15), `Prefabs/Pickaxe`, `Textures/PickaxeIcons`, `Materials/Pickaxe/M_Pickaxe_VertexColor.mat`, `Pickaxe_Asset` rewiring | voxel evaluator per 0.05 m voxel (design unit 0.04), only exposed faces meshed, 8 archetypes x 15 themes, hand-sized ~1.1 m, `UInt16` index, explicit normals, no tangents, uv0.x emission mask, uv0.y shine | V, N:173-177 |
| `Egg/Egg_MeshBaker.cs` (`Game/Egg/Bake Egg Meshes`) | each `Egg_Asset._visualPrefab` (dozens of cube/shell renderers) | 88 meshes `Meshes/EggBaked`, 88 prefabs `Prefabs/Egg/Baked`, asset re-pointed | 1 mesh + `M_VertexColor`; colour from renderer material -> vertex colour (linear); smoothed normals into UV3 for hull outline; skips ParticleSystem children; UInt32; idempotent (skips prefabs already in `Baked/`) | V |
| `Map_BatchBaker.cs` | static `TextureTypeComponent` MeshRenderers of a segment of `_Maps` | `Meshes/MapBatched/MapBatched_<seg>.asset` (13) + scene object `MapBatched/Batched_<seg>` | section 3; skips transparent, multi-submesh, custom-lego, mixed-normal, non-TextureType shaders | V |
| `Map_Expander.cs`, `Map_DecorLibrary.cs`, `Map_Narrower.cs` | map segments | decor chunks, `Meshes/MapDecor/MapDecor_Meshes.asset` (one asset, many sub-meshes) | chunk = 45 m; corridor half-width ~46; menus Expand/Narrow Corridors, Build Plateau Decor | V menus, N:62-66 |
| `Egg/CageFence_Builder.cs`, `CageFence_Themed.cs` | `_Art/3D/Cage/StealEggReference` Base_* prefabs | `Meshes/Cage/<Base>_Fence[Themed].asset` (20), vertex colour per rarity tier | 1 mesh + batched material per cage level; fence object must NOT be Static | V, N:89 |
| `Shop_Builder.cs` | reference `Shop.prefab` proportions | `Prefabs/World/Shops/WorldShop_{Trail,Axe}.prefab`, 2 meshes in `Meshes/Shop` | 40 SM_Cube parts -> 1 mesh per stall | V, N:85 |
| `Egg/Boss_Rescale.cs` | 9 boss prefabs | `Meshes/BossHull/*.asset` (9), `Materials/Boss/M_Boss_Zxx`, `M_Boss_Hull` | per-zone TINTS table; hull = smoothed-normal copy for inverted-hull outline; zone 11 keeps original material | V |
| `Pet_Highlight.cs` (runtime) | pet mesh | hull shell with smoothed normals in UV3, cached per source mesh | built at runtime, not baked | V |

Conventions observed (V): assets under `_Game/Meshes/<Feature>/`, one folder per generator; names `<Feature>_<Name>` (`EggBaked_*`, `MapBatched_M1`, `BossHull_01_Chicken`); pivot = object local origin (egg bake uses root `worldToLocalMatrix`, so root pivot is preserved); scale baked into vertices; winding flipped when `determinant < 0`; index format by vertex count (`> 65000 ? UInt32 : UInt16`; Pickaxe forces UInt16). Read/write: procedural `.asset` meshes are readable by default and no code calls `UploadMeshData(true)` (I: wasted RAM on device, not audited). LOD: none for meshes; chunk GameObject toggling replaces it (section 4). UV usage: uv0 is a real UV only for Problox batched meshes; Egg/Pickaxe use uv0 as data; UV3 is reserved for hull normals.

Hang/duplicate safeguards actually learned (V N:67,71,87,153,199): never `PrefabUtility.InstantiatePrefab` on a nested-prefab child (instantiated the whole `_Maps` -> 30 GB hang); save the scene after each stage (a Unity restart lost work); guard loops (invalid segment length ran to ~31 GB); delete + recreate a mesh asset rather than `CopySerialized` (stale GPU mesh even in Play); force-reimport prefabs after `BuildTiers` (null mesh ref otherwise); bake one segment per MCP call; `Egg_MeshBaker` idempotent by folder check; `Narrow Safe Zone` documented as idempotent.

## 2. Single-material setup

| Material | Shader | Used by | Per-object variation | Tag |
|---|---|---|---|---|
| `M_Problox_Batched.mat` | `Bounce/Problox/SurfaceProboxBatched` = clone of URP Lit with SurfaceProboxShader math; passes Forward, GBuffer, ShadowCaster, DepthOnly, DepthNormals (PC renderer is Deferred so GBuffer is mandatory); `Shaders/Problox/Problox_Batched*.hlsl` | all baked map segments, decor chunks, plateaus, shops, fences | all in vertex data (section 3); texture slots from `TextureDataAsset` | V |
| `M_VertexColor.mat` (under `Assets/ProbloxEngine/.../Shader Library/Materials`) | Problox ShaderGraph | baked eggs, zone-11 boss | vertex colour; hatch flash swaps to `Mat_HatchWhite`; MPB on `Egg_Node` for dynamic tint | V |
| `M_Pickaxe_VertexColor.mat` | `Game/PickaxeVertexColor` (HLSL URP, `CBUFFER UnityPerMaterial` so SRP Batcher compatible, `multi_compile_instancing`, fog) | 15 pickaxes | vertex colour albedo; uv0.x HDR emission (capped ~1.5, feeds bloom), uv0.y shine; wrap light + fresnel rim; no textures | V |
| FX / outline | `Game/HullOutline` (Cull Front, Queue Geometry+1, `_Color`, `_Width`), `Game/Trail`, `Game/WingFx`, `Game/CageWall`, `Game/ToolFxParticle`, `Game/ToolFxTrail` (procedural shapes, no textures) | outlines, trails, particles | colour via material or MPB | V |
| Characters | OmniShade URP (136 mats); variant-strip flags forced to `All` on 74 after black-on-device bug | skins | n/a | V N:240-246 |

User rules about shaders/lighting: do not strip/optimise OmniShade (N:246); `_LightColor0` fix is a hypothesis not device-verified (N:240); baked sources never cast shadows so baked renderers must stay `ShadowCastingMode.Off`; environment reflections/specular must stay ON or the A/B diff rises (N:84); no runtime lighting override, the scene Lighting settings are the only source (N:256-257).
Root cause of 149 map materials: Problox `TextureTypeComponent` is `[ExecuteAlways]` and builds a shared-variant material per instance in `OnEnable`; never mass-instantiate it (N:67-69).

## 3. Vertex data baked (`Map_BatchBaker.cs:82-117`, V)

| Channel | Content |
|---|---|
| position / normal / tangent | world space via object matrix `L`; tangent.w sign flipped on mirrored transforms |
| color | `srgbColor.linear`, alpha 1 (the TextureType colour) |
| uv0 | box-mapped UV (`Branch(normal)` picks 1 of 6 axis branches) x legoTiling; exact only for hard-edged meshes, so meshes whose triangle verts straddle branches are `safe=false` and skipped |
| uv1 (Vector4) | `flags` (1 texture, 2 lego, 4 checker, 8 albedo-movement, 16 emission), texture `slot`, `checkerTiling`, `emissionStrength` |
| uv2 (Vector4) | albedo movement xy |

Eggs: colour + UV3 smooth normals. Pickaxes: colour + uv0 (emission, shine). Fences: colour per rarity tier (`CageFence_Builder.cs:134,196`). No AO and no gradient baking exists (V grep). Palette = per-feature C# tables (`Pickaxe_Generator` `Hex()` specs, `Boss_Rescale.TINTS`, `CageFence_Themed` rarity colours, `Character_SkinTools` constants), NOT a shared palette asset or palette index (V). Plateau colour = biome wall colour +20% brightness written to vertex colours inside `MapDecor_Meshes.asset`; re-running `Build Plateau Decor` overwrites it (N:429-430).

Colour-space pitfalls: GPU does not sRGB-convert vertex colours, so a Linear project must bake `.linear` (Pickaxe guards with `PlayerSettings.colorSpace == Linear`; Egg and Map bake unconditionally). Washed-out pickaxes before the fix (N:177). Skin brightness was re-tuned (0.46/0.38 -> 0.60/0.50) when the sun changed 1.5 -> 1.0 (N:256,339).

## 4. Combining, culling, numbers

| Item | Value | Tag |
|---|---|---|
| Map before | 3767 renderers / 149 distinct materials | V N:69 |
| MapDecor before | 1290 renderers / 97 materials | V N:69 |
| Decor after | 146 renderers / 1 material, 136 chunks (1 mesh + 1 material each) | V N:81 |
| Play, Mobile Forward, decor view | 38/136 chunks active, ~52k decor verts, 93 batches / 62 set-pass | V N:83 |
| Earlier cut | 28/136 chunks, ~42k verts (show <230, hide >270) | V N:81 |
| Parity | A/B vs source mean diff < 0.2% at 8 camera positions | V N:84 |
| Eggs | 88 prefabs: dozens of renderers each -> 1 mesh, 1 material | V |
| Project size | `_Game`: 342 .cs, 238 prefabs, 55 materials, 148 meshes, 67 `MenuItem`s | V find/grep |
| Device measurements | none recorded; mobile tier verified in Editor with Mobile Forward quality only | V N:84 |

Runtime parts: `Map_BatchedStatic` (`[DefaultExecutionOrder(-10000)]`) disables authoring MeshRenderers + TextureTypeComponents in `Awake` BEFORE their OnEnable, so no per-object variant material is ever created; authoring objects stay in the scene so the bake can be re-run (`Map_BatchBaker.Bake("M3")`, `Preview(bool)`), groups serialized per segment. `Map_DecorCulling`: per-chunk sphere centre/radius, show/hide distances with hysteresis (rim 460/420, floor chunks x0.65), coroutine `_interval 0.4 s`, `Camera.main` cached lazily (V). Deviation: coroutine + `WaitForSeconds` loop instead of event-driven `CullingGroup`; fine for 136 chunks but not the documented standard.
Gotchas: a SafeZone cube change needs `Map_BatchBaker.Bake("SafeZone")` + NavMesh rebake (H); an open scene shows `mesh=NULL` after meshes were replaced on disk, reload the scene (H); `Game/Map/Bake Decor Bounds` must be re-run after map changes (N:408).

## 5. Editor tool catalog (V `Scripts/Editor`, 67 menu items)

| Group | Tools (menu) | Inputs -> outputs | Safeguards observed |
|---|---|---|---|
| Asset bake | Bake Egg Meshes; `Map_BatchBaker.Bake(seg)`; Build Plateau Decor; Bake Decor Bounds; Rebuild Cage Fences (Themed); Shop_Builder; `Pickaxe_Generator.BuildTiers/BakeIcons`; Rescale Bosses + Red Outline | prefabs/scene -> mesh assets + prefabs | idempotent-by-folder; delete + recreate mesh; force reimport; `MarkSceneDirty` + `SaveAssets`; one segment per call |
| Config gen | `1. Generate All Configs`, `1b Trails + Menu Icons`, Sync Zones With Steal An Egg, Remap Rarities, Fill Factory_Character With All Skins, Create Steal Egg Upgrade Assets | reference data -> `Configs/*` assets + Factory lists | re-runnable, name-matched |
| UI build | numbered pipeline `0..8`, `EggUi_Builder` + 6 partials (Iap, Monet, PetIndex, Settings, ShopAll, SkinShop), "Build Pets Popup Only", Wire Carry UI | code spec -> `SAB_GUI_View.prefab`, popups | rebuild in place; partial per popup; "Only" menus avoid rebuilding the whole HUD |
| Wiring | `7. Wire Scene (all)`, Wire Bonk / Boss Agents / Pet Carry / Pet Interact / Home Safe Zone / Clock + Luck icon, `Tools/Bot/Wire Everything` | scene/prefab refs | AGENTS.md: runtime fallback is not a substitute for authored wiring |
| Sprites/icons | `4. Generate UI Sprites`, `UiSprites_Generator`, `EggIcons_Generator`, `IconRenderer`, `Draw2D` | code -> PNG + sprite import | first render after camera creation can be blank, run twice |
| Balance | Bake Treadmill + Pickaxe Values; Full Game Audit / Progression / Route / Upgrade Loop simulations; `Gameplay_Rebalance` | `EggBalanceFormula` -> asset values + audits | QA-only; one deterministic formula file is the source |
| Diagnostics | `Dev_SceneCapture`, `Dev_UiCapture`, Scan Missing Scripts, `Build_DataBlockRegistryGuard` (build gate) | screenshots, reports | read-only |
| Import | `docs/monet-demo`, `import-gameplay-fx.ps1`, `import-trail-assets.ps1`, `trail-import-map.json`, `MonsterImport_Tools` | reference project -> project, GUID-preserving | closure rule in AGENTS.md |
| Migration | `TmpMigration` (capture then apply), `UniText_Setup`, `UniText_WorldConvert` | TMP -> UniText | 2-step, capture first |

Useful suffix convention (V file names): `_Builder` creates, `_Wiring` assigns refs, `_Generator` writes assets. Menu paths are inconsistent (`Game/Egg/7b.`, `Tools/Bot/...`).

## 6. Docs: format and recurring corrections

Format that worked (V): `docs/superpowers/specs/<date>-<topic>-design.md` (header Date / Target project / Reference read-only path / Fidelity / Supersedes; "Decisions taken with the user" table with a Why column; "Reference facts" tables with anchor/pos/size per node) + `plans/<date>-<topic>.md` (9 specs, 11 plans, 2026-10-11..14) + `docs/balance/*.csv|md` (baseline vs proposed + sim notes) + append-only `agent-handoff.md` (`date | agent | files | what changed | what to reload`) + 463-line `feedback-notes.md` grouped by topic with DONE/OPEN/QUEUE tags. Weaknesses (I): mixed Vietnamese/English and unaccented Vietnamese; superseded entries left in place (Run speed v1/v2/v3, TEMPORARY 203 m/s cap with revert note); the whole file is re-read each session (token cost).

Recurring corrections as rules (reason in brackets):
1. Port reference UI/prefab/atlas 100%; generate new art only after proving the reference has none [user rejected "close enough" HUD, wrong Attack/Jump tiles, improvised icons; N:HUD 2026-10-12].
2. Never invent a visual a sister project already has (arrow, focus pointer): transfer the real closure (M_Quest_Arrow + Animated Shader + T_Arrow) with a SketchEngine adapter [N:373].
3. Procedural art must match the reference silhouette language: smooth chamfered pickaxes rejected -> voxel; square tips never cones; every tier unique and "not ugly"; old art deleted, not kept [N:172-178].
4. Repeated art = one mesh + vertex colour + shared material, baked in the Editor, authoring objects kept for re-bake [N:172,431].
5. Performance first: no continuous Instantiate/Destroy; pool labels/FX/icons; one manager does label billboard/scale/cull instead of per-object LateUpdate [N: STANDING RULE 2026-10-12; H: EggLabelManager].
6. Do not override scene lighting/ambient at runtime; the scene is the source of truth (agent forced sun 1.5, user removed it) [N:256-257].
7. Do not strip/optimise a shader that produced black characters on device [N:246].
8. Reference priority for AI/gameplay: Steal-an-Egg canon, then knife-tower/monkey-escape, only then tune "fun" [N: Bots].
9. Finish the active task before queued ones; acknowledge and queue new requests (promoted into AGENTS.md).
10. Wire everything (scene, prefab, SO, serialized refs), run the bake, compile, Console, Play. Scripts alone are not done; build gate: do not tell the user to build for device until audit, wiring, tests and a timeScale=1 Play pass are done [AGENTS.md; N: BUILD GATE].
11. Balance is ONE loop (speed, boss, pickaxe, egg HP, pet income, cage, ads, IAP); copy relationships not absolute numbers; fast-forward is QA only; verify from a clean save [N:2026-10-12/13].
12. Ads/IAP are optional value, never a paywall; some rewards session-only; this game has no daily [N:339,429].
13. Use installed SketchEngine frameworks (Audio, Popup, Taptic), transfer only needed clips, record provenance in `docs/asset-provenance.md` [N: Audio].
14. UI text = UniText (not TMP); fix baseline globally in shared setup, not per-label nudges [N: UniText 2026-10-12].
15. Physics feel: character glued to ground at high speed, no launch, max slope 20 deg [N: Ground hugging].
16. Save the scene after each stage; rebake NavMesh with `NavMeshAssetManager.instance.StartBakingSurfaces` then SAVE THE SCENE (BuildNavMesh + SaveAssets did not persist) [N:149,153-155].
17. Back up the dev save before mock purchases and restore after [H: IAP].

## 7. House-style conformance and agent-process failures

| Area | This project | Verdict | Tag |
|---|---|---|---|
| Layout | `_Game/{Audios,Configs,Fonts,Materials,Meshes,Prefabs,Resources,Scenes,Scripts{Core,Data,Editor,Event,Factory,Logic},Shaders,Textures,Tests}`; art in `_Art` (220 FBX) + legacy `_ARTs` | follows; adds Meshes/Shaders/Textures/Tests | V |
| Naming | `Data_*` (8), `Factory_*` (10 files), `Event_*`, feature-first `Egg_*`, `Pet_*`, `Cage_*`, `Boss_*`, `Tutorial_*` | follows | V |
| Framework | SketchEngine; `StaticBus<` in 39 files, `StateMachine<` in 3, `DataBlock<` in 8, collision registry in ~7 | follows | V |
| Update loops | 63 `Update/LateUpdate` in Logic; label manager centralised after complaints | partly deviates | V |
| Culling | coroutine distance loop, no `CullingGroup` | deviates | V |
| Combining | Editor-persisted bake, no runtime `MeshSceneCombiner`, no loader step | deviates (zero load cost) | V |
| `Find*` | 3 uses in Logic | good | V |
| Tools size | `Pickaxe_Generator` 1510 lines; `EggUi_Builder` 7 partials; `.disabled` KnifeTower treadmill file kept | acceptable for tools | V |
| Tests | EditMode asmdefs: Audio, BotLogic, CarryPose, GameplayHud, ShopSkin, Treadmill (+Guidance); six unrelated Bot/HUD tests red on 2026-10-13 | partial | V, H |

Agent-process failures (V in N/H): (1) 30 GB hang from `InstantiatePrefab` on a nested prefab, ~31 GB runaway loop, lost unsaved session; (2) NavMesh rebake not persisted, twice; (3) stale mesh after in-place overwrite; (4) another agent kept entering Play Mode and blocked compile (3 times); Codex + Claude edited `EggUi_Builder`/`Egg_Label` concurrently, the handoff log was the coordination tool; one session blocked by another agent's `Skin_Shop` compile errors; (5) invented visuals instead of porting (HUD tiles, arrow, luck icon, pickaxes) -> rework; (6) QA at `timeScale=60` gave false negatives (pet lifetime 0.7 s real), polluted save gave false completion times, first audit used a provisional hit cadence (0.22 s vs 0.378 s measured); (7) exception in `Pet_Carrier.Steal` skipped boss knock because `?.` was used on a destroyed Unity object; (8) re-running a generator overwrites hand recolour in `MapDecor_Meshes.asset` (documented hazard); (9) temporary test constant (`MAX_MOVE_SPEED = 203`) left live with a revert note; (10) MCP `ai-game-developer` ECONNREFUSED forced a queued-work list (N:443); (11) "done" claims without Console/Play evidence were challenged repeatedly, which created the build gate.

## 8. Overlap with existing skills in this repo (V skill list)

`world-batching-culling` already encodes sections 3-4 from this same project; `editor-tool-authoring` and `asset-transfer-closure` cover section 5 and AGENTS.md; `multi-agent-coexistence` covers failure 4. Not yet covered: procedural vertex-colour mesh generation + linear colour rule, single-material family design and channel contract, hull-outline recipe, palette ownership.

## Proposed classification

| Candidate | Class | Proposed name | Must-haves |
|---|---|---|---|
| Vertex colours baked LINEAR in Linear projects | RULE | `rule-vertex-color-linear` | `.linear` when `PlayerSettings.colorSpace==Linear`; one shared helper for every baker; comment at top of each generator; A/B screenshot vs source; never store gamma colours in palette assets |
| One material per feature family, variation in vertex data | SKILL | `vertex-color-single-material` | channel contract per shader (colour, uv0 data, uv1/uv2 flags, UV3 smooth normals); SRP Batcher-safe `CBUFFER`; passes for every active renderer (GBuffer if Deferred); MPB only on a few dynamic objects; no ExecuteAlways per-instance material builders |
| Procedural mesh generator (voxel/primitive) saved as `.asset` | SKILL | `procedural-mesh-generator` | spec tables in code; exposed-face voxel meshing; explicit normals; index format by vertex count; delete + recreate asset; force reimport prefabs; bake icons twice |
| Merge N renderers into 1 mesh + vertex colour for existing prefabs | TOOL | `mesh-merge-baker` (pattern of `Egg_MeshBaker`) | idempotent by output folder; skip particle children; keep pivot via root worldToLocal; smoothed normals in UV3 for outlines; re-point config asset; report counts |
| Static map segment bake with Apply/Preview toggle, authoring kept | RECIPE | `static-map-bake` | `Bake(segment)` per call; disable authoring comps in Awake at order -10000; shadows Off on baked renderers; skip transparent/multi-submesh/mixed-normal; before/after renderer + material table |
| Distance chunk culling with hysteresis | RECIPE | `decor-chunk-culling` | baked centres/radii; show < hide distance; interval or `CullingGroup` (house style) not per frame; per-type distance factor |
| Inverted-hull outline shader + smoothed normals | RECIPE | `hull-outline` | `Cull Front`, `Queue Geometry+1`; width param; smoothed normals in UV3 cached per mesh; separate hull mesh for bosses; do not rely on lit-shader outline passes |
| Editor tool safety (`_Builder/_Wiring/_Generator`, "Only" menus, idempotent) | RULE | `rule-editor-tool-safety` | no `InstantiatePrefab` on nested-prefab child; loop/iteration caps; `MarkSceneDirty` + `SaveAssets`; one unit of work per MCP call; count report on every run |
| NavMesh rebake persistence | RECIPE | `navmesh-rebake-persist` | `NavMeshAssetManager.instance.StartBakingSurfaces`, then save scene; verify asset is referenced; rebake after moving shops/zones/cages; check bots from Splash start |
| Spec / plan / feedback doc formats | RECIPE | `spec-plan-feedback-format` | spec header (date, target, read-only reference, fidelity, supersedes); decisions table with Why; reference-facts tables; prune superseded notes; rules block on top of feedback file, keep it short |
| Recurring user corrections 1-17 (section 6) | DATA | `user-corrections-ledger` | one line each: rule, why, date, source; consumed by `done-means-wired`, `ui-clone`, `reference-port`; prune superseded; tag UI/art/perf/process |
| Port reference visuals 100%, never invent | RULE | `rule-port-not-invent` | check reference first; transfer closure with GUIDs; SketchEngine adapter instead of CodeSketch class; log provenance in `docs/asset-provenance.md` |
| Render stats before/after report | TOOL | `render-stats-report` | count renderers/materials/batches/set-pass/active chunks/verts from fixed camera set; store in spec; state "not measured on device" |
| Palette ownership (absent here) | DATA | `palette-registry` | one SO or C# table of named colours (linear); theme/rarity/biome tints reference it; bakers read it; replaces scattered `Hex()` tables |
| QA false-negative traps | RULE | `rule-qa-validity` | verdicts at timeScale=1; clean save for progression claims; measure constants (clip length) before auditing; log temporary constants with a revert owner |
| Destroyed-object null safety | RULE | `rule-destroyed-object-null` | no `?.`/`??` on `UnityEngine.Object`; wrap cross-feature side effects in try/catch so the next effect still runs |
