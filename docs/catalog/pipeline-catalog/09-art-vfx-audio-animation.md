# 09 - Art pipeline, shaders/materials, VFX, animation, audio

Scope: read-only reverse engineering of `knife-tower-troll-unity` (KT) and `monkey-escape-unity` (ME).
Abbrev: KT = `C:\Unity\GitProject\knife-tower\knife-tower-troll-unity\Assets`, ME = `C:\Unity\GitProject\monkey-escape\monkey-escape-unity\Assets`.
Tags: **V** = VERIFIED (file cited), **I** = INFERRED.
Counts are per-file grep counts; texture/audio `.meta` counts include per-platform blocks, so treat them as proportions, not exact asset counts.

## 0. Headline findings (corrections to the house-style text)

| # | Finding | Tag |
|---|---|---|
| 1 | OmniShade is NOT the world/material standard. It is used only on **character skin materials** (69 `.mat` in KT `_Art/3D/Character/...`, 0 in `_Game`). World materials are URP Lit / SimpleLit plus 17 custom URP shaders in `_Art/Shader/`. | V `KT/_Art/3D/Character/FBX/Brainrot/Ballarian/BC_Cong_chua1.mat`; grep of `_Game` mats |
| 2 | There is **no PC quality tier in use**: `QualitySettings.asset` has a single level `Mobile`, though `PC_RPAsset`/`PC_Renderer` exist in `Assets/Settings`. | V both `ProjectSettings/QualitySettings.asset` |
| 3 | Mobile URP asset is NOT at the "strict low-end" baseline: HDR **on**, soft shadows **on**, shadow distance 50, `m_ColorGradingLutSize 16`. Matches baseline: SRP Batcher on, 1 cascade, 512 shadow map, MSAA off (`m_MSAA: 1`), render scale 1. | V `*/Settings/Mobile_RPAsset.asset` |
| 4 | Lighting is 100% realtime: one directional light per scene, `m_Lightmapping: 4` (Realtime), no LightProbeGroup, no baked lightmaps. | V `KT/_Game/Scenes/*.unity`; I for "no lightmap data" (no lightmap folders next to scenes) |
| 5 | No Animancer, no Spine runtime code, no AnimationEvents. Animation = Unity Animator (hashed params) + tweens (DOTween 48 files + PrimeTween 39 files in KT). Both tween libs coexist. | V grep `_Game/Scripts`; 0 `functionName:` in `.anim`/`.fbx.meta` |
| 6 | Audio framework does **no pitch randomization and no ducking**; pitch only exists for BGM (`BGMHelper.SetPitch`). | V `Library/PackageCache/com.codesketch@.../Runtime/Audio/*.cs`, `KT/_Game/Scripts/Logic/BGM/BGMHelper.cs` |
| 7 | Both projects keep third-party VFX packs fully imported (KT `Packages Fx` = Epic Toon FX 562 MB, Hovl 182 MB, Piloto 285+76+25 MB, Lana 127, Vefects 63, Hun0FX 45). Only ~13-20 particle prefabs live in `_Game`; the rest of the packs are unused ballast in the repo. | V `du -sh` |

## 1. Folder layout (art side)

| Path | Role | Tag |
|---|---|---|
| `Assets/_Art/{2D,3D,Fx,Shader,Skyboxes}` (ME also `Materials`) | Source art: 3D characters (`_Art/3D/Character/FBX/...`), 2D sprites, FBX props, custom shaders | V |
| `Assets/_ARTs/` | Older/second art root (KT: 104 images, 64 FBX; ME: 110/57). Duplicated root, accidental | V counts; I accidental |
| `Assets/_Game/Material` (legacy) + `Materials` | KT `Material/` = 4 loose mats; `Materials/` = subfolders `Lego Platform`, `Lego Wall`, `LegoMapValley`, `LegoSpeed`, `Platform`, `Wall` + 2 Stud textures. ME same split (`Material/Mat_Lego`, `Texture`; `Materials/` 2 mats) | V |
| `Assets/_Game/_Meshes` (KT) / `_Meshs` (ME) | Project-owned FBX (KT 37 FBX in `_Game`; ME 1) | V |
| `Assets/_Game/_Optimized/Speed Keyboard` (KT) | Scene-bake outputs (NavMesh + `FBX_Exporter.unity`) for `*_Optimized` scenes | V |
| `Assets/Packages Fx/*` | Vendor VFX packs (see finding 7). ME also has `Hovl Studio`, `New effects`, `Piloto Studio` at Assets root | V |
| `Assets/Packages Required/` | HighlightPlus, TransitionsPlus, FogShader, KCC, Joystick Pack | V |
| `Assets/_Game/Prefabs/Fx & Trail`, `Prefabs/Currency` | Project-owned FX prefabs | V |

Counts (V): KT `_Art` = 890 png/jpg, 246 FBX, 171 `.anim`, 35 `.controller`, 277 prefabs; ME `_Art` = 655/127/22/5/202. `_Game` KT = 510 prefabs, 8 images.

## 2. Shaders and materials

### 2.1 Shader census (m_Shader guid on all `.mat` under `Assets/_Game`+vendor; guid resolved by `.meta`)

| Project | Shader | Count | Resolved to | Tag |
|---|---|---|---|---|
| KT | `f0632d8b...` | 99 | `Universal Render Pipeline/Lit`-family (guid in URP PackageCache `Lit.shader`; note: also matched by vendor Hovl `Lightning10.mat`) - dominant | V/I |
| KT | `831a199d...` | 23 | `_Art/Shader/URP_BumpedDiffuse_AutoTiling_Transparent.shader` | V |
| KT | `ba3e3898...` | 8 | `URP_BumpedDiffuse_Cylindrical.shader` | V |
| KT | `8d2bb70c...` | 8 | URP `SimpleLit.shader` | V |
| KT | `933532a4...` | 6 | URP `Lit.shader` | V |
| KT | `b1def950...` | 5 | `URP_BumpedDiffuse_Spherical.shader` | V |
| ME | `4f40ae51...` (ShaderGraph) | 56 of 79 | `_Game/Material/Texture/DotTilingWorldSpace.shadergraph` (keywords `_ISGLOW`, `_IS_DOT`); 56 mats are **material variants** (`m_Parent` set) | V `ME/_Game/Material/Mat_Lego/Mat_Caro/M_Color 10.mat` |
| ME | URP Lit/ SimpleLit / AutoTiling_Transparent / TMP Billboard | 1-5 each | - | V |

Material totals: KT 155 in Material(s) / 171 under `_Game`; ME 69 / 79. (V `find -name *.mat`).

### 2.2 House-standard shader families

| Family | Where | Notes | Tag |
|---|---|---|---|
| URP Lit / SimpleLit (stock) | Props, platforms, UI-3D | Default for authored world; `m_Parent` variants for color swaps (ME) | V |
| `URP/BumpedDiffuse_AutoTiling` (+`_Transparent`, `_Cylindrical`, `_Spherical`, `_Conical`, `..._Transparent`) | `_Art/Shader/` (220-493 lines each) | World-space auto tiling: `_TexelsPerUnit`, `_AutoTileScale`, `_BumpMap`, toggles `_EnableShadow`, `_EnableEmission`. Replaces UV unwrap for Lego/obby geometry. Multi-compile `_MAIN_LIGHT_SHADOWS`, `_SHADOWS_SOFT`, instancing | V `KT/_Art/Shader/URP_BumpedDiffuse_AutoTiling.shader` |
| `URP_AutoTiling_VertexColor`, `URP_Mobile_Diffuse_KeyVertexAlphabetPress(_Fade)`, `SKB_MobileDiffuseInstanced` | `_Art/Shader/` | Vertex-color / per-key-press shaders for the Speed Keyboard minigame | V names; I purpose |
| `URP_QuadWireframe_Lite(_Transparent)` | `_Art/Shader/` + `URP_CubeWireFram_Trans.mat` | Cheap wireframe look for platforms | V |
| `TMP_Sprite Billboard`, `Distance Field Billboard` | `_Art/Shader/` | World-space name tags/billboards, instanced variant exists | V |
| `Dissolve.ShaderGraph`, `FlatGraySilhouette` | `_Art/Shader/` | Spawn/die dissolve; locked/silhouette look | V names; I purpose |
| OmniShade `Standard URP` (+Triplanar) | Character skins only | Keywords seen: `ANIME_SOFT`, `MATCAP_PERSPECTIVE`, `AMBIENT`, `DIFFUSE`, `FOG`, `SHADOWS_ENABLED`, `OUTLINE_PASS_DISABLED`; `_OutlineWidth 0.03`, `_OutlineColor` red; outline pass disabled by default in material | V `BC_Cong_chua1.mat` |

SRP Batcher compatibility (V, grep `CBUFFER_START` in `_Art/Shader/*.shader`): 14 of 17 custom shaders declare a CBUFFER; **3 do not**: `URP_BumpedDiffuse_AutoTiling.shader` (the main one), `URP_Mobile_Diffuse_KeyVertexAlphabetPress`, `..._Fade`. These three are not SRP-Batcher compatible (I: accidental; they are the older/simplest shaders).
`SKB_MobileDiffuseInstanced` and `TMP_Sprite_Billboard_Instanced` show an intentional GPU-instancing path for large populations (V names).

### 2.3 Outline strategy (device-tiered)

| Tier | Outline method | Tag |
|---|---|---|
| High-end (`Device.UseHighlightPlusOutline = IsHighEnd && !IsLowEnd`) | HighlightPlus renderer feature (`Mobile_Renderer_Outline.asset` has `HighlightPlusRenderPassFeature`, needs depth texture) | V `KT/_Game/Scripts/Logic/Settings/Device.cs:51`, `Settings/Mobile_Renderer_Outline.asset` |
| Low/Mid | Highlight Plus off, no depth, use OmniShade built-in outline pass | V same |
| Controller | `OutlineController` toggles per-skin OmniShade `_OutlineWidth`/color; skips materials whose shader name does not start with `OmniShade` | V `.../Logic/Optimize/OutlineController.cs:22,177` |

`Device.cs` classifies GPU by name/Snapdragon number (>=700 High, 690 Medium for safety, >=650 High, ...), reads `SystemInfo.systemMemorySize`, supports a forced tier cheat (V `Device.cs:32,160-162`). This is the project's ONLY quality-tier mechanism (no Unity Quality levels).

### 2.4 Unique materials per scene (V, grep of scene YAML)

| Scene | MeshRenderers | SkinnedMR | ParticleSystems | Lights | AudioSources | Size |
|---|---|---|---|---|---|---|
| KT `Minigame_SpeedKeyboard_W1` | 4985 | 0 | 0 | 1 | 0 | 3 MB |
| KT `MiniGame_ClimbCamoTower` | 2101 | 1 | 101 | 1 | 1 | 11 MB |
| ME `Minigame_WukongEscape` | 761 | 0 | 0 | 1 | 0 | 1 MB |

Pattern: thousands of renderers share a few dozen materials; the combine pipeline (section 4) collapses them per material into combined meshes. A python-free count of unique materials per scene was not obtained (INFERRED: tens, not hundreds, because mats are grouped per set: `Lego Platform`, `Lego Wall`, `LegoSpeed`).

## 3. Textures

| Setting | KT | ME | Tag |
|---|---|---|---|
| `maxTextureSize` (import blocks) | 2048: 3330; 512: 476; 1024: 372; 256: 343; 64: 216; 128: 22 | 2048: 2773; 1024: 240; 64: 217; 512: 190; 256: 169 | V `*.png.meta` |
| Android override format | `textureFormat 50` (ASTC 6x6) 256; `48` (ASTC 4x4) 132; `51` (ASTC 8x8) 121; `-1` (auto) 478 | 50: 205; 48: 107; -1: 404 | V (ASTC enum ids: I) |
| Android max size override | 2048: 477; 512: 160; 256: 146; 1024: 128 | 2048: 404; 1024: 125; 256: 81 | V |
| `textureCompression` | 1 (normal) ~3738/3775 | 1 ~2818/2848 | V |
| `crunchedCompression` | 0 everywhere | 0 | V |
| Mipmaps | OFF 935, ON 67 (sprites/UI default off; ON only for a few 3D textures) | OFF 660, ON 113 | V |
| `isReadable` | 0: 973, 1: 29 | 0: 760, 1: 13 | V |
| Sprite mode | Single (1): 646; None (0): 347; Multiple (2): 9 | 519 / 231 / 23 | V |
| Atlas | No SpriteAtlas verification done | - | I (Addressables used for groups) |

Reading: textures are mostly left at default 2048 max with ASTC chosen per platform override; low sizes (64/128/256) are deliberate UI icons. 2048 default on thousands of imports is probably accidental bloat (I). `globalTextureMipmapLimit`: KT = 1 (half-res mip drop globally), ME = 0 (V `QualitySettings.asset`).

## 4. Meshes, combine pipeline, Blender bridge, LODs

### 4.1 Mesh import (V `*.fbx.meta`)

| Setting | KT | ME |
|---|---|---|
| `globalScale` | 1: 501, 0.3: 85, 0.6: 12, 0.003: 23 | 1: 215, 0.3: 71, 4: 40, 100: 16 |
| `useFileScale` | 1 (344) | 1 (185) |
| `meshCompression` | 0: 269, 2: 43, 1: 27 | 0: 145, 2: 40 |
| `isReadable` | 0: 218, 1: 129 | 1: 94, 0: 91 (readable is mandatory for combine, see below) |
| `importBlendShapes` | 0: 266, 1: 81 | 0: 122, 1: 63 |
| `importCameras/Lights` | 0 for ~85% | same |
| `generateSecondaryUV` | 0 | 0 |
| `materialImportMode` | 2 (from material description) | 2 |
| Animation | `animationType` 2 (Generic) 199, 0 (None) 138, **no Humanoid** | Generic 107, None 49, Humanoid 29 |
| `animationCompression` | 1 (Keyframe reduction) | same |

Mixed `globalScale` (0.3/0.6/4/100/0.003) = scale is fixed per-FBX at import (accidental, vendor-driven; I). Rule of thumb implied: authoring unit = 1 m, props get 0.3 when exported huge (I).

### 4.2 Combine pipeline (V `KT/_Game/Scripts/Core/Mesh/`)

| Piece | Behavior |
|---|---|
| `MeshSceneCombiner` (446 lines) | `[SerializeField] _excludeRoots`, `_dynamicKeywords = {"AnimationSequence","Move","Rotate","Tsunami","Ladder","Treadmill"}`; `BakeRendererGroups()` in Editor stores `BakedRendererGroup{material, renderers[]}`; `CombineAsync(progress, budgetMs)` at runtime |
| Budgets | `_budgetMs = 6` ms/frame when playing directly; `_budgetMsViaLoader = 200` ms behind LoadingScreen; `0` = all in one frame; `_yieldTiming = LastUpdate` |
| `MeshCombineHelper` | Requires `Mesh.isReadable` (warns otherwise); `indexFormat = totalVerts > 65535 ? UInt32 : UInt16`; `UploadMeshData(true)` (frees CPU copy); optional 1-level `LODGroup` on the combined GO |
| LOD handling | After combining, source `LODGroup` and all LOD renderers are disabled (`_combinedLods`), Lego authoring renderers skipped (`IsLegoAuthoringRenderer`) |
| Opt-out | `Tag_SkipMeshSceneCombiner`, `Sketch_Lego_ExcludeFromCombine` |
| `_Optimized` scenes | KT has `Minigame_SpeedKeyboard_W{1,2,3}_Optimized.unity` plus a navmesh per scene (V) - tooling output; I: baked combined scenes for low-end |

LOD usage otherwise: `LODGroup` appears only as source art and is disabled at runtime after combine; no authored multi-LOD pipeline for characters (I).

### 4.3 Blender bridge `UnityToBlender_Format` (V `KT/_Game/Scripts/Editor/UnityToBlender_Format.cs`, 273 lines)

| Item | Detail |
|---|---|
| Menu | `Tools/Unity To Blender/Format` (EditorWindow, selects a root `GameObject`) |
| Step 1 | Delete all deactivated children; rename siblings so names are unique |
| Step 2 | Export CSV (default folder `D:\Blender Project`) with columns: name, position, hierarchy **Path** (exact match key in Blender), material `_Color` as `ColorUtility.ToHtmlStringRGBA` ("true colors") |
| Use | Round trip a level to Blender, restore transforms/colors by path (I). Strings are Vietnamese; hardcoded drive path is machine-specific (accidental) |

## 5. Lighting, fog, post-processing

| Item | KT | ME | Tag |
|---|---|---|---|
| Color space | Linear (`m_ActiveColorSpace: 1`) | Linear | V `ProjectSettings.asset` |
| Pipeline | URP, `Mobile_RPAsset` + `Mobile_Renderer`; `PC_RPAsset` unused by Quality | same | V |
| URP: SRP Batcher / dynamic batching | on / on | on / on | V |
| URP: HDR / MSAA / render scale | on / off(1) / 1 | on / off / 1 | V |
| URP: main light shadow map / cascades / distance | 512 / 1 / 50 | 512 / 1 / 50 | V |
| URP: soft shadows / additional lights | on / per-vertex mode 1 | same | V |
| URP: LUT / grading mode | 16 / LDR(0) | 16 / 0 | V |
| Quality (`Mobile` level only) | shadowRes 1, cascades 2, shadowDistance 40, AA 0, vSync 0, lodBias 1, `skinWeights 255` (KT) vs 4 (ME), `particleRaycastBudget 256`, `asyncUploadTimeSlice 2` | `skinWeights 4` | V `QualitySettings.asset` (quality cascades 2 is overridden by URP asset) |
| Renderer | Forward (`m_RenderingMode 0`), no depth priming, `m_IntermediateTextureMode 0` | same | V |
| Scene lights | exactly 1 directional per scene, intensity 0.9 (W1), soft shadows (`m_Shadows.m_Type 2`), realtime | 1 per scene | V |
| Light probes / lightmaps | none (0 LightProbeGroup) | none | V (probes) / I (lightmaps) |
| Skybox | per-scene skybox material (`_Art/Skyboxes`; Home uses built-in default) | - | V |
| Fog | Speed Keyboard scenes ON: linear (`m_FogMode 1`), color `(0.13,0,0.32)`; Home/Climb towers OFF. Extra `FogShader` package | - | V `Minigame_SpeedKeyboard_W1.unity:18-20` |
| Post-processing | Global Volume `VolumeURP` = **Bloom + ColorAdjustments** only; ME also has `PP Profile.asset` + `Scenes/Volume` | same | V `Settings/VolumeURP.asset` |
| Scene transitions | `TransitionsPlus` | same | V |

Intentional vs accidental: single realtime light + fog-as-skybox-blend + bloom/color-adjust is the intentional "toy/Roblox" look. HDR+soft shadows+distance 50 exceed the stated low-end baseline and look inherited from the URP template (I).

## 6. VFX

### 6.1 Sources and conventions

| Item | Detail | Tag |
|---|---|---|
| Vendor packs | Epic Toon FX (ETFX v1.8), Hovl Studio, Piloto Studio (+MeshFx, Tornado), Lana Studio, Vefects, Hun0FX; ME also `New effects` | V dirs |
| Project FX prefabs | KT: 20 prefabs in `_Game` contain `ParticleSystem`; ME: 13 | V |
| `maxNumParticles` in `_Game` prefabs (KT) | 1000 (150 systems, vendor default), 50 (53), 25 (34), 10 (30), 20 (21), 15 (13) | V |
| ME | 100 (6), 10 (5), 1 (3), 20 (1) | V |
| Culling mode | Automatic(0) 226, Always Simulate(3) 65, Pause(1) 33 (KT); ME all 0 | V |
| Sorting | 4849/4955 renderers at order 0; a few at 1/2/4; ME has outliers 2506 and 20000 (UI/overlay FX) | V |
| Particle count per scene | ClimbCamoTower 101 ParticleSystem components (the only particle-heavy scene) | V |

### 6.2 Delivery APIs (KT)

| Layer | Class | Behavior | Tag |
|---|---|---|---|
| Pool config | `PoolPrefabConfig` SO (CodeSketch) in `Configs/Pool/Pool_Fx_*.asset` | Fields `_prefab`, `_persistAcrossScenes`, `_deactiveOnRelease`, `_poolPrewarm`, `_poolCapacity`, `_poolCapacityMax`. e.g. `Pool_Fx_Death`: prewarm 60, capacity/max 120, persist 1. 23 pool assets; max capacity mostly 50 (17), 100 (3), 500 (2) | V |
| Spawn | `PoolPrefabGlobal.Get<ParticleSystem>(cfg)` / `Release(cfg, go)` | Used by `Fx_FollowTarget`, `Factory_Fx.CreateLandingFx()` (ME) | V |
| Registry | `Factory_Effect` (KT): `_fxDeath`, `_fxLanding` + status durations `_burnKillDelay 1`, `_freezeDuration 8`, `_poisonDuration 5` (s). `Factory_Fx` (ME): only `_poolFxLanding` | V |
| One-shot bursts | `GlobalFx` (MonoSingleton, persists across scenes): `FxData{id, fxPrefab, ParticleEmitConfig[]{particleSystem, emitCount=50, positionOffset, rotationOffset}}`; emits from ONE shared particle system instead of instantiating | V |
| Selector | `Fx_Info{Type: PoolPrefab|GlobalFx, PoolPrefabConfig, GlobalFxId}` - inspector-level choice per feature | V |
| Attach/aux | `Fx_Follow`, `Fx_FollowTarget`, `Fx_Owner`, `Fx_ToggleEmit`, `Fx_Trail` (trail width via `UpdateWidth`), `Fx_Combo`, `Fx_Tornado`, `Fx_Mesh` | V names |
| Cosmetic trails (ME) | `Trail_Asset` SO (`_multiplier 1.5`, IAP/dailylogin gate, `_prefab`, icons) in `Configs/Trails` | V |
| Rule of use | GlobalFx = one-shot only; continuous attached FX = pooled prefab (doc comment in `GlobalFx.cs`) | V |

## 7. Currency spread FX (reward fly-to-HUD)

V `KT/_Game/Scripts/Logic/Currency/Spread/Currency_Spread.cs`, `Currency_Spread_Config.cs`, `Configs/Currency_Spread_{Money,Gem,Cup}.asset` (same 3 assets in ME).

| Parameter (Money asset) | Value | Meaning |
|---|---|---|
| `_fadeInDuration` / `_fadeOutDuration` | 0.3 / 0.2 s | Background dim image |
| `_sequenceDelay` / `_sequenceDuration` | 0 / 0.5 s | Items spawn staggered: `delayBetween = sequenceDuration / max(1,count-1)` |
| `_scaleDuration`, `_scaleEase` | 0.5 s, Ease 30 (OutBounce, I) | Pop-in at spawn |
| `_backDuration` / `_backDistance` | 0.09 s / 0.5 | Small wind-up move opposite to travel |
| `_flyDelay` / `_flyDuration` | 0.5 / 0.3 s | Wait, then fly |
| `_flyCurve` | 0->1 linear-ish, slopes 2 | Acceleration toward HUD |
| `_controlStart` / `_controlEnd` | (0,8,0) / (6,-6,0) | Cubic Bezier control points (`PathType.CubicBezier`, `Sidescroller2D`) |
| `reachEndDelay` (derived) | 0 + 0.5 + 0.09 + 0.5 + 0.3 = **1.39 s** | Time until last item lands |
| Extras | `_vfxEnd` prefab at the HUD icon, `_sfxEnd` AudioConfig (Money: none), `_spreadOutBurstDuration 0.6` with `DOSpiral` burst mode; `Sequence`s are DOTween | V |

Architecture: wallet pill `Currency_Bar` (+ `Currency_Bar_Spread`, `Currency_Bar_Size`) subscribes to the event; start/amount/type payload (`Event_Currency_Spread_Start`, see skill `currency-spread-fx`). KT bar also has `Currency_MoreCup`. Per-currency config = per-currency item prefab + end VFX. Uses DOTween (not PrimeTween) - this subsystem predates the PrimeTween preference (I).

## 8. Animation

| Topic | Finding | Tag |
|---|---|---|
| Runtime stack | Unity `Animator` + controllers (KT 35 in `_Art`, ME 5+5) + DOTween/PrimeTween for UI/world motion. No Animancer, no Spine C# usage (a `Spine` folder exists at KT Assets root, unused by code) | V |
| Param access | Hash IDs; ME has a `HashDictionary` (`TriggerWallJump`, `TriggerRolling`...), `SetTriggerParameterIfExists(int hash)` guard, `CrossFadeInFixedTime("Ground", max(0.01, d), 0, 0)` with default 0.1 s | V `ME/_Game/Scripts/Logic/Character/Character_Animator.cs:158-324` |
| Counts | `StringToHash` in 17 (KT) / 18 (ME) scripts; `SetTrigger/SetBool/SetFloat/CrossFade` in 20/15 | V |
| Animation events | **None** (0 `functionName:` entries in anims/FBX) - gameplay is driven from code state, not from clip events | V |
| Rig | Generic is the default (KT 199 Generic, 0 Humanoid; ME 107 Generic, 29 Humanoid, 29 `animationType 3`) - Humanoid used only for retargeted ME characters | V |
| Clip compression | Keyframe reduction (1) on 325/152 FBX; 21/32 optimal (3) | V |
| Ragdoll / traversal | `Character_Ragdoll`, `Character_AgentLinkTraversal` (NavMesh link jump) | V names |
| Skinning | KT `skinWeights 255` (unlimited) vs ME 4 bones: KT value is accidental for mobile (I) |
| Cinemachine | v2.10.7, 4/3 scripts; Timeline 1.8.12 installed | V manifest |

Intentional/accidental: absence of Animancer and animation events looks intentional (code-first); mixed DOTween/PrimeTween is accidental drift (KT 48 vs 39 files).

## 9. Audio

### 9.1 Layout and routing (V)

| Item | Detail |
|---|---|
| Clips | `Assets/_Game/Audios/{BGM,Sfx,...}` (KT also `SKB_SFX`, `SnakeTower SFX`; ME `SFX_Monkey`, `SKB_SFX`, `Treadmill`). Feature subfolders under `Sfx/`: `Battle, Common, DailyLogin, Jackpot, Squid, Trampoline, Weapon` (KT). Inconsistent: some packs sit at Audios root (accidental, I) |
| Configs | `Configs/Audio/{BGM,Sfx/<Feature>,Speed Keyboard}` (+`Monkey`, `Treadmill` in ME). **One `AudioConfig` SO per clip**: `Sfx_<Feature>_<Action>.asset` (e.g. `Sfx_Character_Jump`, `Sfx_Gem_Collected`), BGM `BGM_<Name>.asset`. KT: 64 SFX configs + 15 BGM configs |
| Generator | `CodeSketch/Tools/Audio Config Generator` editor window (`AudioConfigGeneratorWindow.cs`) creates configs from clips | V |
| `AudioConfig` fields | `_clip, _type (Sound=0/Music=1), _mode (2D=0/3D=1, Sound only), _earsDistance (min,max; default (1,10); SFX configs use (0.1,4)), _volume 0..1, _bus (AudioBus)` | V `Library/PackageCache/com.codesketch@0fe9d8bab8cb/Runtime/Audio/AudioConfig.cs` |
| Player | `AudioManager.Play(config, loop)` / `Play(config, position, loop)` via `ObjectPool<AudioScript>`; `AudioScript` returns itself to pool after `clip.length` (`Tween.Delay`); `AudioManager.EventStopAll(type)` | V |
| Bus enum | `AudioBus` comment rules: only Voice may duck Music; UI/Sound never duck Music; Ambience non-intrusive. Project values: SFX configs `_bus: 10` (all 64), BGM `_bus: 20` (13) / `10` (2) | V |
| Mixer | `AudioMixer.mixer` groups: Master, Music, Sound, SFX, UI, Ambience (+Send/Attenuation effects). **No ducking compressor/snapshot automation found** (a `Snapshot` exists but no sidechain) | V group names; I no ducking |
| Mixer mapping | `AudioMixerFactory.BusMapper{Bus, MixerGroup}`; Master/None bypass the lookup; `Factory_Audio.OnInitialize` calls `AudioMixerFactory.OverrideMixer(_overrideMixer)` | V |
| Facade | `Factory_Audio` (KT 70 lines): `AudioConfig[] SfxFades, SfxScreams, SfxTreadmill`, singles `SfxSlipeAndFall, SfxGemCollected, SfxItemPurchased, SfxPurchased, SfxCarpetWhoosh, SfxLevelUp`, `PlayResultWin()/PlayResultLose()` null-guarded. Feature audio mostly lives on component fields instead (inconsistent) | V |
| UI click | `AudioButtonSfx : IPointerDownHandler` plays on pointer **down** (not click), skipped if `Button.interactable` false; fallback `AudioMixerFactory.SfxUIButtonClick` | V |
| BGM | `BGMHelper` static: `CrossFadeAsync` (UniTask, cancel token), `FadeOutAndStopAsync`, `SetPitch`, `SetVolume`; `BGM_Area`, `BGMKickOff`, `BGMNoFallback` triggers | V |
| Settings | `DataSettings.SoundVolume` with `Audio_Volume` component scaling a scene `AudioSource` by remembered `_original` volume | V `Logic/Audio/Audio_Volume.cs` |
| Pitch variation | **None** for SFX (framework has no pitch randomization); variety is done by arrays of clips (`SfxFades[]`, `SfxScreams[]`, `SfxTreadmill[]`, 4 treadmill files) | V grep `.pitch`; I rationale |

### 9.2 Import settings and sizes (V `*.meta`)

| Setting | KT | ME |
|---|---|---|
| Formats | 176 ogg, 34 mp3, 21 wav | 172 ogg, 18 mp3, 10 wav |
| Total size | 42.4 MB (max `BGM_CyroPanther_Boss.mp3` 4.17 MB) | 18.4 MB (max `BGM_2.mp3` 3.5 MB) |
| `compressionFormat` | 1 (Vorbis) for 198/198 | 173/173 |
| `quality` | 1.0: 115, 0.6: 83 | 1.0: 112, 0.6: 60, 0.5: 1 |
| `loadType` | 0 DecompressOnLoad 188; 2 Streaming 10 (BGM) | 170 / 3 |
| `preloadAudioData` | 1: 158, 0: 40 | 142 / 31 |
| `forceToMono` | 0: 134, 1: 64 | 125 / 48 |
| `loadInBackground` | mostly 0; 1 on the 10 streamed | 0 (1 file) |

Volume defaults: SFX configs `_volume 1` (62), 0.8 (1), 0.2 (1); BGM 0.3 (1), 0.4 (1), 0.5 (3), 0.6 (6), 0.8 (1), 1 (3). Convention: SFX full-scale, BGM 0.4-0.6 (V `KT/_Game/Configs/Audio`). Home BGM = 0.4. Wav and mp3 are leftovers from vendor packs (I: accidental; ogg is the standard).

## 10. Intentional vs accidental summary

| Intentional (consistent across both projects) | Accidental / drift |
|---|---|
| URP Lit + custom world-space auto-tiling shaders; OmniShade only on skins | 3 of 17 custom shaders lack CBUFFER (not SRP Batcher compatible) |
| Single realtime light, bloom + color adjust, per-scene fog | HDR + soft shadows + shadow distance 50 on mobile; `PC` URP assets present but unused |
| Combine static meshes by material with ms budget; LODGroups disabled after combine | `_ARTs` + `_Art`, `Material` + `Materials`, `_Meshes`/`_Meshs`; mixed `globalScale` |
| Pooled FX via `PoolPrefabConfig` assets; GlobalFx for one-shot bursts | 150 vendor systems at `maxNumParticles 1000`; 562 MB Epic Toon FX unpruned |
| One `AudioConfig` per clip, bus enum, ogg Vorbis | wav/mp3 mixed in; some audio packs outside `Sfx/<Feature>` |
| Device tier detection instead of Unity Quality levels | DOTween + PrimeTween both in use; KT `skinWeights 255` |
| Animator + code tweens, no animation events | Hardcoded `D:\Blender Project`, Vietnamese strings in editor tool |

## 11. Proposed classification

| Candidate | Class | Proposed name | Must-haves (3-6) |
|---|---|---|---|
| World shader/material standard | RULE | `art-shader-material-rules` | URP Lit/SimpleLit default; custom shaders must have `CBUFFER_START(UnityPerMaterial)` (SRP Batcher) and `multi_compile_instancing` where populations are large; OmniShade only for character skins; color variants via material variants (`m_Parent`), not new materials; one shared material per set so the combiner can merge |
| Mobile URP + lighting baseline | RULE | `mobile-urp-lighting-baseline` | One quality level "Mobile"; URP asset: SRP Batcher on, MSAA off, 1 cascade, 512 shadow map; decide HDR/soft shadows per measured need (reference ships them on); single realtime directional light, no lightmaps/probes; global volume only Bloom + ColorAdjustments; fog per scene (linear) |
| Device tier gating | SKILL | `device-tier-quality-gating` | `Device.Tier` from GPU name + RAM; forced-tier cheat; gate outline method (HighlightPlus vs shader outline), post-FX, FX counts by tier; log tier at startup |
| Texture import | RULE | `texture-import-standard` | Android ASTC 6x6 default (4x4 for UI/hero, 8x8 for backgrounds); max 1024 for 3D world, <=256 for icons; mipmaps off for UI/sprites and on for 3D; no crunch; `isReadable` off; no unused 2048 defaults |
| Mesh import + readable | RULE | `mesh-import-standard` | Scale 1 at import (no per-FBX 0.3/100); `isReadable` on only for combinable static meshes; mesh compression off or Medium consistently; no cameras/lights/blendshapes; Generic rig unless retargeting |
| Static mesh combine | SKILL | `world-batching-culling` (extend) | Bake `BakedRendererGroup` per material; runtime/loader budget (6 ms play, 200 ms loader); UInt32 index above 65,535 verts; `UploadMeshData(true)`; exclude dynamic keywords + opt-out tag; disable LODGroups after combine |
| Blender level round trip | TOOL | `unity-to-blender-csv-tool` | Clean (delete inactive, unique names) then export CSV (name, position, path, `_Color` hex); configurable export dir (not hardcoded `D:`); English UI; selection-root required |
| Particle/FX budget | RULE | `vfx-budget-rules` | Cap `maxNumParticles` per prefab (reference: 10-50 typical, 100 max); never ship vendor 1000 default; pool every spawned FX; one-shot bursts via a shared GlobalFx emitter; delete unused vendor packs before build |
| FX factory + pooling | RECIPE | `fx-pool-factory-recipe` | `Factory_Fx/Effect` registry of `PoolPrefabConfig`; asset fields `_poolPrewarm/_poolCapacity/_poolCapacityMax`; `Fx_Info` (PoolPrefab vs GlobalFx); release on stop; sort order 0 except UI overlays |
| Reward currency fly | SKILL | `currency-spread-fx` (exists) | Config SO per currency; timings from section 7 (1.39 s total); event-driven; VFX+SFX at end; fix DOTween vs PrimeTween choice in new work |
| Audio config/bus system | SKILL | `game-audio-system` (extend) | One `AudioConfig` per clip with generator; bus enum + mixer groups; SFX `_volume` 1, BGM 0.4-0.6; Vorbis ogg q0.6-1.0, SFX decompress-on-load, BGM streaming; `AudioButtonSfx` for UI |
| SFX variation + ducking | RECIPE | `sfx-variation-ducking` | Gap not covered by reference: add `Vector2 pitchRange` to `AudioConfig`/play call; clip arrays for variants; Voice bus ducks Music with a mixer snapshot or sidechain; cooldown per config to avoid stacking |
| Animator conventions | RULE | `animator-conventions` | Hash IDs via a `HashDictionary`; guard missing params; `CrossFadeInFixedTime` default 0.1 s; Generic rig; no AnimationEvents (code state drives it); compress clips (keyframe reduction); `skinWeights` 4 |
| Tween library selection | RULE | `tween-library-choice` | PrimeTween for new code; keep DOTween only in legacy (currency spread, 48 files KT); never mix inside one component |
| Art folder layout | DATA | `art-folder-layout` | `_Art/{2D,3D,Fx,Shader,Skyboxes}`; `_Game/Materials` (not `Material`); `_Game/_Meshes`; vendor packs under `Packages Fx`; single art root (avoid `_ARTs`) |
| Perf audit of art | RECIPE | `art-perf-audit` | Count: unique materials/scene, non-CBUFFER shaders, textures >1024 on Android, particle systems with `maxNumParticles` >100, readable meshes, unused vendor packs |

## 12. Gaps / not verified

- Unique-material count per scene not computed (python unavailable); sizes in section 2.4 are renderer counts only.
- Per-clip lengths and total SFX trigger frequency not sampled; `clip.length` drives pool return (V) but no per-clip stats gathered.
- Hovl Studio per-prefab particle counts inside vendor folders not audited (vendor `maxNumParticles` shown only for `_Game` prefabs).
- `Ease 30` = OutBounce and ASTC enum ids are from DOTween/Unity enum tables (INFERRED).
- No SpriteAtlas/Addressables audit for textures; `MeshSceneCombiner` runtime draw-call gain was not measured.
