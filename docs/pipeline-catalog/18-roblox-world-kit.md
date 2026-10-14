# 18 - Roblox-look world kit (single material, studs, palette, bake, lighting, budgets)

Scope: read-only design from mining. Nothing was compiled or run in Unity (ai-game-developer MCP offline). Goal: one material for the whole world when it renders right, Roblox "studs" look, low-end Android.
Tags: **V** = verified (file read, cited), **I** = inferred / proposed design, must be proven in Editor + on device.
Paths: TBE = `C:\Unity\GitProject\thunder-break-egg\break-and-steal-unity\Assets`, KT = `...\knife-tower\knife-tower-troll-unity\Assets`, SAE = `...\steal-an-egg\Assets`, RAP = `...\ride-a-pet\Assets`, PRB = `...\problox\Assets`, TRW = `...\Tiny Relax World\tiny-relaxing-world-unity\Assets`.
Builds on catalogs 09, 11, 13 (not repeated: combine runtime, units table, chunk culling recipe).

## 0. Headline findings

| # | Finding | Tag |
|---|---|---|
| 1 | The Roblox look in all sister projects comes from ONE engine, "vanhuy_probloxengine" (ShaderGraphs `SurfaceProboxShader`, `VertexColorShader`, `SurfaceCharacterShader`, `MetalMatCapShader`, `Block_Checkpoint`, `SkyboxBlending`), present identically in PRB, SAE, RAP, TBE. Per-part look = `TextureTypeComponent` (solid colour + texture slot + lego detail + checker + albedo scroll + emission) which clones a material variant per instance in `OnEnable` (`[ExecuteAlways]`). That is the origin of 149 materials / 3767 renderers in the TBE map. | V `PRB/vanhuy_probloxengine/0_Asset Library/Scripts/TextureType/TextureTypeComponent.cs`, `.../Shader Library/*.shadergraph`, catalog 11 sec 2 |
| 2 | TBE already solved single-material for the map: `Bounce/Problox/SurfaceProboxBatched` (clone of URP Lit + Problox surface function), per-vertex data instead of per-material data. Result 3767 renderers/149 mats -> 1 mat per segment, decor 1290/97 -> 146/1, 93 batches in Editor Mobile Forward. | V `TBE/_Game/Shaders/Problox/Problox_Batched.shader`, `Problox_Batched_Surface.hlsl`, catalog 11 sec 4 |
| 3 | Its flag contract is the best existing spec: `uv1 = (flags, slot, checkerTiling, emissionStrength)`, `uv2.xy = albedo scroll`, `uv0 = box-mapped UV * legoTiling`, colour = linear vertex colour. Flags: 1 texture, 2 lego(stud) detail, 4 checker, 8 scroll, 16 emission. But it is a full URP Lit clone (410 + 275 + 251 + 63 lines, 4-7 texture slots, branches on `slot`), too heavy for the stated low-end target. | V `Problox_Batched_Surface.hlsl:1-63`, `Map_BatchBaker.cs:82-117` |
| 4 | Studs today are a TEXTURE (`tex_Stud_Out.png` 128x128 + `tex_Stud_N_Out.png` normal, mip on, sRGB, in KT `_Game/Materials`) tiled by world-space triplanar `URP/BumpedDiffuse_AutoTiling` (`_TexelsPerUnit`, `_AutoTileScale 0.5`, 3 bump samples; global keyword `_AUTOTILING_NO_BUMP` already exists as the low-end switch). This shader is NOT SRP-Batcher compatible (no CBUFFER, catalog 09). | V `KT/_Game/Materials/Lego Platform/mat_Lego_1.mat`, `KT/_Art/Shader/URP_BumpedDiffuse_AutoTiling.shader:1-200` |
| 5 | RAP/ME use a ShaderGraph `DotTilingWorldSpace` (keywords `_ISGLOW`, `_IS_DOT`, checker, normal map, emission) with material variants (`m_Parent`) for colour. Colour swaps via variants = many materials, so it fails the "one material" goal. | V `RAP/_Game/Materials/TextureAndShader/DotTilingWorldSpace.shadergraph`, catalog 09 sec 2.1 |
| 6 | No shared palette asset exists in any project. Colours are scattered: `Hex()` tables in `Pickaxe_Generator`, `Boss_Rescale.TINTS`, `CageFence_Themed`, `C(0x3FA83D)` in `Map_DecorLibrary`, per-material `_Color`. KT lego mats store arbitrary `_Color` floats (e.g. 0.66,0.92,0.93). | V catalog 11 sec 3; `TBE/_Game/Scripts/Editor/Map_DecorLibrary.cs:89`; `mat_Lego_1.mat` |
| 7 | TBE world scale is metric: tree 1.4 x 7 m boxes, decor chunk 45 m, pickaxe ~1.1 m; character feel (KT) 4.5 m/s, capsule 1.7 m = 16 studs/s and ~6 studs tall at 0.28 m/stud. So reference clones effectively run at stud ~ 0.28 m with hand-tuned bigger props. | V `Map_DecorLibrary.cs:207`, catalog 11 sec 1, catalog pipeline "Feel table"; stud mapping I |
| 8 | TRW (Tiny Relax World) is 2D tilemap (Tiny Swords, `Sprite_Lit_Wetness.shader`), NOT a Roblox-look source. Nothing reusable for this kit except its URP 2D lighting is irrelevant. | V `TRW/_Art/Shader/Sprite_Lit_Wetness.shader`, `Assets/Tiny Swords`, `Voxel Labs` folders |
| 9 | TBE Mobile URP is below KT/ME in cost but not at baseline: HDR on, MSAA off, 512 shadow map, 1 cascade, shadow distance 50, soft shadows OFF (differs from KT/ME where soft is ON), SRP Batcher on, dynamic batching on. Scene: linear fog mode 1 colour (0,0.76,1.0), ambient mode 3 (Flat? value 3 = Custom/Flat), colour (0.67,0.69,0.72), intensity 1, one realtime sun (1.0 after user removed 1.5 override). Linear colour space. | V `TBE/Settings/Mobile_RPAsset.asset`, `_Game/Scenes/SAB_Gameplay.unity`, `ProjectSettings.asset:50`, catalog 11 N:256 |
| 10 | Vertex colours must be baked `.linear` in a Linear project or everything looks washed out (shipped bug, fixed 3 times in 3 bakers). | V catalog 11 sec 3 |

## 1. Design decision: ONE material, ONE shader, data in vertices

Name: material `M_RobloxWorld`, shader `Game/RobloxWorld` (I). Replace per-part material variants (Problox `TextureTypeComponent`, `DotTilingWorldSpace`, `AutoTiling`) with a vertex channel contract. Exceptions that stay separate materials (I, sorted by reason):

| Exception | Reason | Count target |
|---|---|---|
| `M_RobloxWorld_Alpha` (Glass/Ice/ForceField) | transparent blending cannot share the opaque queue; same shader keyword `_SURFACE_ALPHA` | 1 |
| Character skins | OmniShade, user forbids stripping (V catalog 11 N:246) | existing |
| Hull outline `Game/HullOutline`, FX, trails | separate passes/queues | per feature |
| Sky | skybox material | 1 |

Goal wording for the GDD: "world = 1 opaque material + 1 alpha material" (resolves contradiction 10 in `pipeline-catalog.md` stricter than "one per family").

## 2. Shader spec `Game/RobloxWorld` (proposal; basis TBE Pickaxe_VertexColor + Problox batched + KT AutoTiling)

### 2.1 Structure
- HLSL URP, `Tags RenderPipeline=UniversalPipeline Queue=Geometry`. Passes: `UniversalForward`, `ShadowCaster`, `DepthOnly` (and `DepthNormals` only if SSAO/depth needed; `GBuffer` only if a Deferred renderer is used. TBE PC renderer is Deferred so GBuffer was mandatory there, V catalog 11 sec 2). Mobile = Forward, so ship Forward + ShadowCaster + DepthOnly. DepthOnly in Pickaxe shader is the minimal template (V `Pickaxe_VertexColor.shader`).
- All per-material values inside ONE `CBUFFER_START(UnityPerMaterial) ... CBUFFER_END` (V pattern in `Pickaxe_VertexColor.shader`); `#pragma multi_compile_instancing` and `multi_compile_fog` (V same file). Keywords: `_SURFACE_ALPHA`, shader_feature local `_STUD_NORMAL`, global multi_compile `_ROBLOX_LOWEND` (mirrors existing `_AUTOTILING_NO_BUMP` switch, V). No `[ExecuteAlways]` per-instance material builders, no per-renderer MaterialPropertyBlock on static map (MPB breaks SRP Batcher, V house style).
- Dynamic props that move still use the same material (batched by SRP Batcher). Colour tweens use per-object vertex colour variants or a tiny MPB only on a handful of objects (V rule, catalog 11).

### 2.2 Vertex channel contract (extends TBE's contract; keep flag bits compatible)

| Channel | Content | Notes |
|---|---|---|
| position / normal | world or object space, explicit normals | hard edges for blocks; no tangents (V pickaxe: "no tangents") |
| COLOR (Color32 ok) | base colour, LINEAR (`srgb.linear`), a = emission mask or opacity | helper `RobloxColor.ToVertex(Color srgb)` single place (rule from catalog 11) |
| uv0 (Vector2) | stud-space UV: world units / stud size, box-mapped per dominant axis (Problox `BoxUv(Branch(n))`, V) | 1.0 = one stud; baked, so no in-shader triplanar for static meshes |
| uv1 (Vector4) | x = surface flags (int), y = surface id / atlas slot, z = param (checker tiling or tile scale), w = emission strength | same layout as Problox `pb1` (V) |
| uv2 (Vector2, optional) | scroll velocity (conveyor, lava) | Problox `pb2` (V) |
| uv3 | smoothed normals for hull outline only, on hull meshes | V pattern (Egg bake) |

Flag bits (superset of Problox 1/2/4/8/16, V): 1 TEXTURE (atlas), 2 STUD_TOP, 4 CHECKER, 8 SCROLL, 16 EMISSION, 32 INLET (stud negative, for bottom face), 64 NEON, 128 TRIPLANAR_RUNTIME (for objects NOT baked, e.g. scaled primitives at runtime: shader computes uv0 from object-space position * object scale, equal to KT triplanar but with 1 sample, I).

### 2.3 Fragment cost target (I)
- Opaque, no texture fetch for plain Plastic/SmoothPlastic/Neon (colour only). Studs are PROCEDURAL: `d = length(frac(uv0) - 0.5)`; stud mask = `smoothstep(r, r - fw, d)` using `fwidth` (or `ddx`) for AA; fake bevel by brightening on the light-facing half and darkening on the other (`dot(normalize(uv0 - cell), L.xz)`), no normal-map sample. Texture studs (KT `tex_Stud_Out.png` 128x128) remain an option under keyword for fidelity checks (I).
- Surface patterns (checker, wood grain, brick, grass noise): ONE atlas texture `T_RobloxSurfaces` (512x512 or 1024x512, ASTC 6x6, mips ON, sRGB, per catalog 09 texture rule) sampled once with `slot` selecting a cell; replaces Problox `_Albedo1..4` + `_LegoDetail` + `_LegoNormal` + `_CheckerDetail` (7 textures, V).
- Lighting: URP simple per-pixel main light (Lambert + half-lambert wrap 0.45 from Pickaxe shader, V), ambient flat (`SampleSH` or `_Ambient` const), no additional lights, no specular on SmoothPlastic beyond tiny blinn (`_Shine`), fog via `MixFog` (V). Hard-to-see Roblox specular on Plastic = a small constant highlight scaled by flag, not env reflection.
- Receive shadows: `_MAIN_LIGHT_SHADOWS` with `_SHADOWS_SOFT` off on Mobile (V TBE Mobile asset: soft off). Keep ShadowCaster on only for characters/movers; static baked map meshes have `ShadowCastingMode.Off` (V catalog 11 sec 2 rule).
- Instruction/ALU budget: a plain opaque fragment should compile to <= 40 ALU on Mali-G52 class (I; measure with Mali Offline Compiler or Xcode-equivalent; no data yet).

## 3. Roblox surface set (map Roblox material -> vertex data, I; Roblox list is engineer knowledge, not fetched)

| Roblox material | Flags / slot | Look | Cost |
|---|---|---|---|
| Plastic | STUD_TOP | studs on +Y and side faces facing up only | procedural |
| SmoothPlastic | none | flat colour, tiny spec | none |
| Studs / Inlet (Roblox surface types, not materials) | STUD_TOP / INLET | per-face; bake as `stud mask` bit per triangle by normal | procedural |
| Neon | NEON + EMISSION (w = 1..1.5, capped like pickaxe `min(1,1.5/max)` , V) | flat bright, feeds bloom | none |
| Glass / ForceField | goes to `M_RobloxWorld_Alpha` | alpha 0.3-0.5, no refraction | transparent (budget separately) |
| Grass / Sand / Slate / Concrete / Brick / Wood / WoodPlanks / Metal / DiamondPlate / Cobblestone / Ice / Marble | TEXTURE + slot (atlas cell) | low-contrast tile modulates colour (x0.85..1.15), 1 cell each | 1 sample |
| Checker (obby floors) | CHECKER, z = tiling | `frac` math, no texture (replace `_CheckerDetail`) | ALU |
| Lava / conveyor | SCROLL, uv2 = velocity, EMISSION | `uv0 - _Time * uv2` (Problox does this, V) | ALU |
| Terrain | do NOT use Unity Terrain; bake meshes with colour per biome | | none (V rule 13) |

Surface table lives in `Factory_RobloxSurface` (SO registry) with `id, flags, slot, defaultTint, physicsMaterial, sfxFootstep`, so baker, gameplay (footstep, friction) and validator read one source (I, house style factory).

## 4. Palette registry (BrickColor-like) - DATA

Design (I): `Palette_Roblox.asset` (ScriptableObject, Game namespace) holds named entries `{ id (int), name, srgbHex, linear (cached), category }`. Roblox BrickColor has ~128 named colours; clones need ~40-64 (decision: ship 64 slots, 2 columns of 32; keep ids stable like BrickColor numbers so GDD can say "Bright red"). Starter set (names are Roblox's public BrickColor names; hex values must be sampled from the reference video frames or are placeholders, I): White, Institutional white, Medium stone grey, Dark stone grey, Black, Really black, Bright red, Really red, Br. yellowish orange, Bright orange, Bright yellow, New Yeller, Lime green, Bright green, Dark green, Forest green, Teal, Cyan (Toothpaste), Bright blue, Navy blue, Royal blue, Bright violet, Magenta, Hot pink, Pastel brown, Brown, Dark orange, Sand, Tan, Pastel yellow, Pastel green, Pastel blue, Electric blue, Lapis, Medium blue, Sand green, Olive, Burlap, Cool yellow, Neon orange.
Rules:
1. Palette stores sRGB hex (authoring) AND baked linear floats; bakers read `.linear` only (rule-vertex-color-linear, V catalog 11).
2. Vertex stores colour directly (not palette index) for the main contract; an optional index mode (`uv1.y` = palette id, shader looks up 64-entry `float4` array in CBUFFER, global `_PaletteTable`) is a runtime-recolour option for plots/skins without remesh (I; array in global shader property, not per-material). Use index mode only for objects that recolour at runtime.
3. Biome/rarity/theme tints reference palette ids, not hex (replaces scattered `Hex()` tables, V catalog 11 gap).
4. Re-run safety: generators must not overwrite hand-recolour (documented hazard V N:429).
5. Extraction tool (TOOL): sample dominant colours from reference frames/screenshots, snap to nearest palette entry (deltaE in Lab) and output usage histogram, so GDD "art" section lists palette ids (I).

## 5. Primitive part generator with stud-scale UVs - TOOL

`Roblox_PartGenerator` (Editor, `_Generator` suffix, V naming convention catalog 11 sec 5). Inputs: `PartSpec{ shape(Block|Wedge|Cylinder|Sphere|Ball|CornerWedge|Truss-lite), sizeStuds(Vector3), colorId, surfaceId, studTop(bool), rotation, pos, name }` list (data = JSON/SO "GDD map spec"). Output: mesh pieces merged per chunk (section 8) or saved `.asset` for prefabs (V: TBE saves procedural meshes as `.asset`, no FBX).
Rules (I unless marked):
- Geometry: block = 24 verts (hard normals, 4 per face) so box-map is exact; wedge/cylinder bevel-free; cylinder 12 segments (low-end), sphere 8x6; no mesh >65535 verts per chunk or force UInt32 (V rule in `Egg_MeshBaker`: `>65000 ? UInt32 : UInt16`).
- UV: `uv0 = (worldPos on the two axes perpendicular to normal) / 1 stud`, origin at part min corner snapped to integer so studs align between neighbours; sign flips per face so studs tile continuously; mirrors handled by winding flip when `determinant<0` (V, catalog 11 sec 1). Scale NOT baked into the transform; baked into verts (V).
- Stud bits: STUD_TOP only on faces with normal.y > 0.7 when `studTop`; INLET on bottom faces when part sits under another (skip, never needed visually).
- Snap sizes to 1 stud multiples and positions to 0.5 stud (validator rule, I).
- Output pivot at part origin; export report line `parts/verts/tris/bounds` (V "report counts on every run").
- Idempotent by output folder `Assets/_Game/Meshes/RobloxWorld/<Segment>/` (V pattern); delete+recreate mesh asset rather than `CopySerialized` (V stale GPU mesh hazard); one segment per MCP call (V).
- Guard loops with iteration caps (V 31 GB runaway); never `PrefabUtility.InstantiatePrefab` on nested-prefab child (V 30 GB hang).

## 6. Modular kit pieces (prefab kit, I)

Kit prefabs under `Assets/_Game/Prefabs/RobloxKit/`, each = one mesh + `M_RobloxWorld`, pivot at bottom centre, size in whole studs:

| Group | Pieces |
|---|---|
| Floor | Plate 8x1x8 / 16x1x16 / 32x1x32 (stud top), Road strip, Lava/Neon strip, Checker floor |
| Wall/Frame | Wall 8x8x1, Pillar 2x8x2, Fence 8x3x0.5, Arch, Door frame (door opening 4x7 studs to calibrate scale: avatar ~5-6 studs) |
| Ramp/Stairs | Wedge 8x4x8, Stair 8 steps (rise 1, run 2 studs), Spiral-lite |
| Obby | Truss ladder, Spinner bar, Moving plate, Disappearing plate, Jump pad, Checkpoint, Kill brick |
| Decor (TBE `Map_DecorLibrary` style, V) | Tree (box trunk + sphere-ish cluster), Bush, Rock, Cloud, Sign, Torch, Crate, Barrel |
| Shell | Cage, Shop stall (40 parts -> 1 mesh, V `Shop_Builder`), Spawn plate |

Kit pieces are authored by `Roblox_PartGenerator` (not hand-modelled); variants differ by palette id only.

## 7. Stud -> metre scale and assembly rules

- Single constants class `RobloxUnits`: `STUD_M = 0.28f` default (I, unverified), `WORLD_SCALE` (GDD `scale.world_scale`), conversion in one place (consistent with `rule-roblox-units`, catalog 13). Stud pattern pitch in shader/UV = 1 stud in uv0 irrespective of metres, so changing `STUD_M` rescales geometry but studs stay square: bake with a `studSizeMeters` field in the bake config (I).
- Calibration test (I): door 4x7 studs vs avatar capsule; reference video frame: measure avatar height vs door and set `STUD_M` so avatar = 5-6 studs (KT capsule 1.7 m / 0.28 = 6.1 studs, V arithmetic on V numbers).
- Assembly rules (I): X/Z on integer-stud grid; Y on 0.5/1 stud; platforms 8x1x8 min; gaps for jumps from `jump height 2.0 m` = 7.1 studs and max horizontal `v*t` (use movement table in catalog 13): obby gap max = 0.8 x computed (safety), stair rise <= 1 stud, step slope <= `MaxStableSlope` 50 deg.
- Segment size = bake chunk. TBE chunk is 45 m (V); at 0.28 m/stud that is ~160 studs. Use 32-48 m chunks.
- Corridor/lane widths from reference: TBE half-width ~46 m (V); store in map spec, not code.
- Kill plane `y = -500 studs * STUD_M` default (catalog 13 I) or per-level trigger.
- Placement via spec JSON so the map can be regenerated; hand-edits go into overlay JSON (avoid TBE hazard where re-run overwrote hand recolour, V).

## 8. Bake pipeline

```
MapSpec (JSON/SO) -> Roblox_PartGenerator (per segment)
  -> Parts (mesh, matrix, colorId, surfaceId) -> merge per chunk, one mesh/chunk (<= 65k verts, UInt16 preferred)
  -> save Meshes/RobloxWorld/<Segment>/Chunk_XX.asset  (delete+recreate, force reimport)
  -> create scene objects Batched/<Segment>/Chunk_XX  (MeshFilter+MeshRenderer, M_RobloxWorld, ShadowCasting Off, Static flags: Batching/Occluder as chosen)
  -> collider build -> navmesh bake -> render-stats report -> save scene
```
Based on `Map_BatchBaker` (V: `Bake(segment)`, authoring objects kept, runtime disable at order -10000, skip transparent/multi-submesh/mixed-normal) and `Egg_MeshBaker` (V). Differences proposed (I): the kit is generated from specs, so no authoring-GameObject-per-part exists; the spec is the authoring source and no `TextureTypeComponent` is ever instantiated (removes the 30 GB / ExecuteAlways trap, V).
- **Chunk merge:** group by chunk cell; static solid geometry only; moving parts (platforms, spinners, doors) stay separate prefabs with the same material. Exclude by tag/keyword like `MeshSceneCombiner` (V: `_dynamicKeywords`, `Tag_SkipMeshSceneCombiner`). Persisted `.asset` bake, no runtime combine (V TBE choice: zero load cost). `UploadMeshData(markNoLongerReadable:true)` is NOT applied in TBE (V N/A: not used); do it for the final meshes when no runtime mesh access is needed, else RAM doubles (I).
- **Colliders (I):** do NOT put MeshColliders on merged visual chunks. Generate colliders from the SAME PartSpec: one BoxCollider per Block, CapsuleCollider per Cylinder/Pillar, a few MeshColliders only for wedges/ramps (convex wedge -> BoxCollider rotated for slopes where possible). Put them on a `Colliders` child per chunk (no renderer). Cap per chunk <= 400 colliders; merge adjacent coplanar floor boxes when contiguous (greedy meshing of boxes). Static, layers set by surface (e.g. `Ground`). Register trigger parts through `OptCollisionRegister` (V house rule), never `OnTrigger+GetComponent`.
- **NavMesh:** bake from the collider/render geometry of floor chunks via `NavMeshSurface` collecting `Physics Colliders` (cheaper than render meshes); `NavMeshAssetManager.instance.StartBakingSurfaces(...)` then SAVE THE SCENE; verify the asset is referenced (V catalog 11 recipe `navmesh-rebake-persist`, failure seen twice). Rebake after moving shops/zones/cages/SafeZone (V). Agent radius 0.3 m, height 1.7 m, step 0.4, slope 45 (matches capsule r0.3/h1.7, V feel table).
- **Occlusion / culling:** chunk GameObject toggling by distance with hysteresis (V `Map_DecorCulling`: show<230/hide>270 m, interval 0.4 s) or `CullingGroup` per house style (V deviation noted); bake chunk bounds once (`Decor_BoundsBaker` V).
- **Gotchas to carry (V):** reload scene after meshes replaced on disk (shows `mesh=NULL`); save scene after each stage; re-run `Bake Decor Bounds` after map changes; set `ShadowCastingMode.Off` on baked renderers; keep reflection/specular ON when A/B comparing.
- **Report (TOOL `render-stats-report`, V catalog 11):** renderers, materials, batches, set-pass, active chunks, verts from fixed camera set, state "not measured on device".

## 9. Roblox-look lighting / fog / post presets (URP mobile)

Preset `RobloxLook_Default` (I, values seeded from V TBE where noted; confirm against the reference video palette, catalog 13 "match palette from video frame"):

| Item | Value | Basis |
|---|---|---|
| Colour space | Linear | V all projects |
| URP asset | SRP Batcher on; HDR on only if Bloom is used (else off, saves bandwidth); MSAA off or 2x (4x only high tier); render scale 1 (0.8 low tier); main shadow map 512 (low) / 1024 (mid+); 1 cascade; shadow distance 25-35 (TBE/KT use 50 = above baseline, V); soft shadows OFF (TBE V); additional lights off; depth/opaque texture off; dynamic batching off (irrelevant with SRP Batcher) | V TBE asset, house baseline |
| Sun | 1 directional, warm white `(1.0,0.96,0.88)`, intensity 1.0 (TBE final 1.0 after user removed 1.5, V), euler (50,-30,0); shadows ON, `Shadow Strength` 0.6-0.8; baked-map renderers Off | V TBE sun intensity; rest I |
| Ambient | Flat/colour mode, sky `(0.67,0.69,0.72)` intensity 1 | V TBE `m_AmbientSkyColor` |
| Fog | Linear, colour = horizon colour of sky (TBE `(0,0.76,1.0)`, V), start ~40% of camera far, end = camera far (e.g. 40..120 m); fog doubles as distance cull blend | V TBE mode 1; numbers I |
| Camera | Far clip 100-150 m, FOV 70 (Roblox default V catalog 13), per-zone far-clip zones (V house style) | |
| Skybox | single gradient or cubemap (`SkyboxBlending`/`SkyboxBlendCubemap` exist, V RAP `_Arts/Skybox`) ; Roblox default blue gradient | V names |
| Post | Global Volume: Bloom (threshold ~1.0, intensity 0.2-0.4, only on Neon), Color Adjustments (saturation +10..+20, contrast +5); NO vignette/SSAO/DoF/motion blur/tonemap ACES on low tier; LUT 16, grading mode LDR (V KT/ME) | V KT/ME volume = Bloom + ColorAdjustments |
| Reflection | Default reflection probe off; env reflections off in `M_RobloxWorld` (cheap) but see V N:84 A/B note when matching a reference | |
| Light probes / lightmaps | none (V KT: 0 probes, realtime) | V |
| Tiers | `_ROBLOX_LOWEND` global keyword (disable stud AA fwidth, texture atlas -> flat tint, skip wrap light), post off, shadows off, fog on | I (mirrors `Device.cs` tiering V) |

Do not override scene lighting at runtime; the scene is the source of truth (V N:256-257). Skin brightness may need retuning when the sun changes (V N:256,339).

## 10. Validation tools - TOOL `roblox-world-validate` (I; checks mapped to V lessons)

| Check | Pass rule |
|---|---|
| Material census | world renderers use only `M_RobloxWorld` / `M_RobloxWorld_Alpha`; list offenders (V catalog 11 census approach) |
| SRP Batcher | shader declares `UnityPerMaterial` CBUFFER and `Shader.IsSRPBatcherCompatible`; no MPB on static renderers |
| Vertex data | every chunk mesh has COLOR (linear check: compare to source sRGB), uv0 within [0, studs extents], uv1 flags valid bits; no NaN |
| Mesh budget | verts/tris per chunk and total (section 11); UInt32 only when needed; `isReadable` false on final meshes (unless required) |
| Scale | avatar capsule height / door height ratio; platform sizes are integer studs; jump gaps <= computed jump distance x 0.8 |
| Colliders | no MeshCollider on chunk visuals except listed wedges; collider count per chunk; layers set |
| Navmesh | NavMesh asset referenced by scene, bots can path from spawn to each zone (V catalog 11) |
| Palette | every vertex colour within delta E 2 of a palette entry (flag stray colours) |
| Lighting | scene has exactly 1 realtime directional, 0 probes, fog on, ambient not Skybox-heavy; URP asset values equal preset for the tier |
| Render stats | fixed camera set: batches, set-pass, verts, active chunks; screenshot 3 positions; compare to reference frame (mean diff) as in TBE A/B (<0.2%, V); "not measured on device" stated |
| Idempotence | re-run bake twice, diff zero (V rule) |

## 11. Numeric budgets per device tier (I: nothing measured on device; V anchors in brackets)

Device tier comes from `Device.Tier` (GPU name + RAM, V `KT/_Game/Scripts/Logic/Settings/Device.cs`); no Unity Quality tiers (V).

| Budget | Low | Mid | High |
|---|---|---|---|
| Frame target | 30-45 fps floor, cap 60 (V cap vSync 0) | 60 | 60 |
| World batches visible (set-pass) | <= 60 | <= 100 [V TBE 93 batches decor view] | <= 150 |
| Visible tris (world) | <= 120k | <= 250k | <= 500k |
| Visible verts [V TBE decor ~52k] | <= 80k | <= 150k | <= 300k |
| Total baked mesh in RAM | <= 25 MB | <= 50 MB | <= 100 MB |
| Chunk | 45 m, <= 65k verts, <= 400 colliders [V 45 m chunk] | same | same |
| Active chunks [V TBE 38 of 136] | <= 20 | <= 40 | <= 70 |
| Distance culling (show/hide) | 120/150 m | 200/240 m [V 230/270] | 280/330 m |
| Camera far | 100 | 150 | 200 |
| Shadow map / distance | 512 / 25 m (or off) | 1024 / 35 m [V 512/50 TBE] | 2048 / 50 m |
| MSAA / render scale | off / 0.75-0.85 | off or 2x / 1.0 | 2x-4x / 1.0 |
| Post | none | Bloom only | Bloom + Color Adj |
| Opaque material count (world) | 1 | 1 | 1 (+1 alpha) |
| Textures in world material | 1 atlas 512 ASTC 6x6 (or 0) | 1 atlas 1024 | 1 atlas 1024 + stud normal |
| Transparent overdraw (Glass) | <= 5 quads visible | <= 15 | <= 40 |
| Particles (world FX) | <= 200 live | <= 500 | <= 1000 [V KT `maxNumParticles` 10-50 typical] |
| Dynamic shadow casters | player + <= 4 | <= 12 | <= 24 |
| Pooled bots/props | <= 8 bots | 12-16 | 24 [V catalog 13 bot cap 8-24] |
| Cold map bake time | n/a (Editor) | | |
| GC alloc per frame in world code | 0 B steady-state | | |

Fail rule: any tier exceeding batches or verts blocks the "device build" gate (V "BUILD GATE", catalog 11).

## 12. Gaps / not verified
- No Unity Editor session: shader not written/compiled; ALU/fragment cost and visual parity with the Problox shader are unproven. Procedural stud AA via `fwidth` may shimmer on Mali; a texture fallback is kept (I).
- Roblox stud = 0.28 m, BrickColor ids/hex, exact material list: engineer knowledge, not fetched (catalog 13 verification backlog).
- Problox ShaderGraph internals only skimmed (names and the batched HLSL port); exact lego-detail math not reproduced.
- TBE Mobile asset values (HDR 1, soft 0) read from asset text; scene values read from `SAB_Gameplay.unity` only; no Profiler/device data anywhere.
- steal-an-egg / ride-a-pet `_Game` scene lighting not decoded; only their shared Problox shader set and Lego shader were located.
- Greedy box merging for colliders, palette-index mode, and `_ROBLOX_LOWEND` keyword are new designs with no reference implementation.

## Proposed classification

| Class | Proposed name | Must-haves (3-6) |
|---|---|---|
| RULE | `rule-roblox-single-material` | World = `M_RobloxWorld` (+1 alpha); all per-part variation in vertex data (no per-instance materials, no `TextureTypeComponent`/ExecuteAlways builders, no MPB on static); exceptions list (alpha, skins, outline, sky); CBUFFER + instancing; validator gate |
| RULE | `rule-vertex-color-linear` (reuse catalog 11) | `.linear` in Linear projects via one helper `RobloxColor`; palette stores sRGB hex + linear; A/B screenshot vs source; never store gamma colours in assets |
| SKILL | `roblox-world-shader` | `Game/RobloxWorld` spec: channel contract (COLOR, uv0 stud UV, uv1 flags/slot/param/emission, uv2 scroll, uv3 hull); flag bits compatible with Problox 1/2/4/8/16 (+32/64/128); procedural studs; Forward+ShadowCaster+DepthOnly (+GBuffer only if Deferred); `_ROBLOX_LOWEND` keyword; SRP Batcher check |
| DATA | `palette-roblox` (`Palette_Roblox.asset`) | 64 named BrickColor-like entries, stable ids; sRGB hex + cached linear; categories; optional runtime index mode with global table; GDD references ids; extraction output from reference frames |
| DATA | `roblox-surface-registry` (`Factory_RobloxSurface`) | surface id -> flags, atlas slot, default tint, physics material, footstep sfx; read by baker, gameplay, validator; one atlas texture `T_RobloxSurfaces` |
| TOOL | `roblox-part-generator` | PartSpec (shape, studs size, color id, surface) -> stud-UV meshes; hard-normal 24-vert blocks; integer-stud snapping; UInt32 when >65k; idempotent by folder, delete+recreate assets, iteration caps; count report |
| RECIPE | `kit-pieces-roblox` | Floor/wall/ramp/stair/obby/decor kit sized in whole studs; door 4x7 and avatar 5-6 studs calibration; variants by palette id only; no hand-modelled FBX |
| RULE | `rule-roblox-units` (extend catalog 13) | `STUD_M` single constant (default 0.28, verify against door); integer-stud grid; jump gap <= 0.8 x computed; chunk 32-48 m; kill plane; bake config stores stud size |
| TOOL | `roblox-map-bake` | MapSpec -> merged chunk meshes (<=65k verts) -> chunk objects (shadows Off) -> collider set from specs (boxes/capsules, few convex wedges) -> NavMesh bake and SAVE SCENE -> bounds bake -> render-stats; one segment per MCP call; reload scene after disk mesh swap |
| RECIPE | `roblox-look-lighting-urp` | Preset values section 9: 1 sun, flat ambient, linear fog, Bloom+ColorAdjust only, soft shadows off, shadow 512-1024/1 cascade; tier table; no runtime lighting override; palette match from reference frame |
| TOOL | `roblox-world-validate` | Checks in section 10: material census, SRP Batcher, vertex data/linear, scale ratios, collider and navmesh checks, palette delta-E, lighting preset, render-stats vs tier budget, idempotent re-bake |
| DATA | `world-budgets-by-tier` | Section 11 numbers per Low/Mid/High (batches, verts, chunks, culling distances, shadow, post, particles, bots); marked "unmeasured on device" until Profiler data; wired to device-tier-quality-gating |
