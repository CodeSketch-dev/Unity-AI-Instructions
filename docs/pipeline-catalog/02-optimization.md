# 02 - Optimization catalog (reverse-engineered from production projects)

Scope: collision dispatch, Logic/Optimize, Pool, far-clip zones, CullingGroup, mesh combining, `*_Optimized` scenes, ProjectSettings, import conventions.
Tags: VERIFIED = read in code/settings (path cited). INFERRED = deduced, not proven.
Abbrev: KT = `knife-tower/knife-tower-troll-unity` (Unity 6000.0.78, CodeSketch), ME = `monkey-escape/monkey-escape-unity` (6000.3.22, CodeSketch), BSE = `thunder-break-egg/break-and-steal-unity` (6000.3.22, SketchEngine, vibe-coded: API/discipline reference only).
Framework roots: CS = `ME/Library/PackageCache/com.codesketch@0fe9d8bab8cb/Runtime`, SE = `BSE/Library/PackageCache/com.sketchengine@522ef3079890/Runtime`.

Framework identity (user correction, applied): SketchEngine is the SAME framework as CodeSketch, optimized and renamed. Treat the differences below as a VERSION DELTA (CodeSketch = v1, SketchEngine = v2), not two frameworks. Same folder layout (`Optimize/Collision/{2D,3D}`, `OptCanvasLayout`, `OptScriptLookup`); namespace `CodeSketch.*` -> `SketchEngine.*`.

---------------------------------------------------------------------------------------------------

## 1. Collision dispatch: OptCollisionRegister / Sensor / Lookup

### 1.1 Problem it solves (INFERRED from design + comments, consistent with code)
Classic pattern: every world object has `OnTriggerEnter(Collider o){ o.GetComponent<Character>() ... }`. Cost: one PhysX callback marshalled into C# PER world object touched, plus a `GetComponent` (native lookup, fails for non-matching colliders, and `TryGetComponent` still walks the component list). On a level with hundreds of triggers, the player touching several colliders per frame multiplies this.
Registry pattern inverts it: ONLY the moving actor (Character) has the physics callback (single callback owner). It resolves "who owns the collider I touched" with one `Dictionary<int,...>` read keyed by `collider.GetInstanceID()` - no GetComponent, no allocation after warm-up. World objects carry no `OnTriggerEnter` at all.
Cost model (INFERRED, not profiled): per contact = 1 Unity callback + 1 int-dict lookup + virtual call(s); vs N callbacks + N GetComponent. No profiler numbers exist in the repos (no evidence found); do not quote speedups.

### 1.2 CodeSketch v1 mechanics (VERIFIED: `CS/Optimize/Collision/3D/*.cs`)
- `OptCollisionLookup` (static). Internal `TypedMap<T>` = `static readonly Dictionary<int, T[]>` per interface type T (static generic => one map per T). Value is an immutable array snapshot: Register/Unregister allocate a NEW array (copy-on-write); duplicate owner ignored (`ReferenceEquals`). Many owners per collider allowed.
- Key = `Collider.GetInstanceID()`.
- Query API: `ForEach<T>(collider, Action<T>)`, zero-alloc `ForEach<T,TAction>(collider, ref TAction)` (struct implementing `IOptCollisionAction<T>`), `TryGetFirst<T>`, `GetSnapshot<T>(collider, List<T>)`, `Clear()` (runs registered clear callbacks).
- `OptCollisionRegister<T> : MonoCached` (T = interface, e.g. `ICharacterCollidable`): `Awake` fills `_colliders = GetComponentsInChildren<Collider>(true)` if empty; `OnEnable` -> `Register<T>((T)(object)this, _colliders)`; `OnDisable` -> `Unregister`; `OnValidate` (editor, not playing, unless `_manuallyAssignColliders`) refreshes `_colliders`. Variants `OptCollisionRegister2<T1,T2>` and `Register3<T1,T2,T3>` register the same object under 2/3 interface types (KT: `FNAF_Tower_Floor_Detector : OptCollisionRegister2<ICharacterCollidable, IFNAF_Snake_Collidable>`).
- `OptCollisionSensor<T>` / `OptCollisionSensorFast<T>` (the latter on `MonoCachedFast`): virtual `OnCollisionEnter/Exit`, `OnTriggerEnter/Exit` call `OptCollisionLookup.ForEach<T>(col, cachedDelegate)`; the 4 delegates are lazily cached on first use (`_cachedX ??= OnXFunc`), so no per-event allocation. Subclass overrides `OnCollisionEnterFunc(T target)` etc.
- Actor side (KT `Logic/Character/Character.cs:33,964-971`): `class Character : OptCollisionSensorFast<ICharacterCollidable>`; `protected override void OnTriggerEnterFunc(ICharacterCollidable t) => t.OnTriggerEnterFunc(this);` (same for collision enter/exit/trigger exit). World side implements `ICharacterCollidable { OnCollisionEnterFunc/ExitFunc, OnTriggerEnterFunc/ExitFunc (Character) }`.
- Static state: `TypedMap<T>.Map` is never auto-cleared on scene unload or domain-reload-off Enter Play Mode; nothing in CS calls `OptCollisionLookup.Clear()` (grep: no callers). Correctness relies on every owner running `OnDisable` (scene unload does that). VERIFIED absence of a reset hook.

### 1.3 SketchEngine v2 delta (VERIFIED: `SE/Optimize/Collision/OptCollisionMap.cs`, `3D/*.cs`)
| Aspect | CodeSketch v1 | SketchEngine v2 |
|---|---|---|
| Register base | `OptCollisionRegister<T>` generic; `Register2/3` for multi-interface | `OptCollisionRegister` NON-generic; implement any number of `I*Collidable` on the same class (BSE `Pet_Wild : OptCollisionRegister, ICharacterCollidable`) |
| Storage | one static dict per T (`TypedMap<T>`), copy-on-write `T[]` per add/remove | ONE shared `Dictionary<int, OptSlot>` for 2D+3D; `OptSlot{ MonoBehaviour[] Items; Count; Live }`; slots pooled in a `Stack<OptSlot>`; arrays doubled, never copied per add |
| Remove | allocates new array | tombstone (set null, `Live--`); compacted only when `s_dispatchDepth == 0`; slot recycled when `Live==0` |
| Unregister key | iterates `_colliders` and calls `GetInstanceID()`; a collider that was destroyed (`col == null`) is skipped => stale entry can remain | register returns `int[] _colliderIds`; unregister uses the STORED ids, so it works even after colliders are destroyed. `OnDisable` no longer early-returns on empty colliders |
| Sensor type test | per-T map lookup, no cast | sensor iterates all owners in the slot and filters `owner is T` (sealed overrides `OnTriggerEnterOwner` -> `OnTriggerEnterFunc(T)`); non-generic `OptCollisionSensorFast` base exposes `*Owner(MonoBehaviour)` for custom filtering |
| Reentrancy | safe because iteration reads an immutable snapshot | `BeginDispatch/EndDispatch` (depth counter, try/finally) so an owner that disables itself inside a callback only tombstones |
| Delegates | 4 cached `Action<T>` per sensor | none (direct virtual call) - removes delegate field/alloc |
| Query helpers | `ForEach`, `ForEach<T,TAction>`, `TryGetFirst`, `GetSnapshot` | `TryFindFirst<T>(collider, out T)`, `TryGetAll<T>(collider, List<T>)` (for Overlap/Raycast results; no GetComponent) |
| Clear | `Clear()` callbacks | `OptCollisionLookup.Clear()` -> `OptCollisionMap.Clear()` (still no automatic caller found) |
Net v1 -> v2: removes generic explosion and per-add array allocs, fixes stale-entry-on-destroyed-collider, adds safe removal during dispatch, one table for 2D+3D. Trade-off (INFERRED): an `is T` test per owner per event instead of a direct typed array (negligible for 1-4 owners/collider).
Also in SE only: `OptScriptLookup` has a scene-unloaded clear (`RuntimeInitializeOnLoadMethod(AfterSceneLoad)` -> `SceneManager.sceneUnloaded`); VERIFIED `SE/Optimize/OptScriptLookup.cs`. It is a separate Collider->MonoBehaviour list map (exists in both versions).

### 1.4 Three real usages (VERIFIED)
1. Instant-kill platform: KT `Logic/Platform/PlatformKill.cs` - `class PlatformKill : OptCollisionRegister<ICharacterCollidable>, ICharacterCollidable`; 4 tiny callbacks; collision + trigger both call `character.Kill(_type)`; exit callbacks empty. No Unity physics message on the object.
2. Overlapping trigger zones + static reset: KT `Logic/Camera/CameraFarDistanceZone.cs` - registers the zone BoxCollider; `OnTriggerEnter/ExitFunc` filter `character.IsPlayer`; static `List<CameraFarDistanceZone> s_active` + `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)] ResetStatics()` (this is the origin of the AGENTS.md "reset statics" rule); picks the zone the player is DEEPEST inside (min distance to the AABB faces) to resolve overlapping zones in the same frame.
3. Multi-interface + query use: KT `Logic/Minigame/Climb FNAF Tower/Tower/FNAF_Tower_Floor_Detector.cs` (`OptCollisionRegister2<ICharacterCollidable, IFNAF_Snake_Collidable>`, hit by two different sensors: `Character` and `FNAF_Snake : OptCollisionSensor<IFNAF_Snake_Collidable>`); KT `Character/KinematicController (KC)/CharacterKC.cs:1540,1775` uses `OptCollisionLookup.GetSnapshot(hitCollider, _trampolineInterfaceSnapshot)` to resolve a trampoline from a KCC hit WITHOUT GetComponent (reused List). SketchEngine equivalent: BSE `Logic/Pet/Pet_Wild.cs:18` `sealed class Pet_Wild : OptCollisionRegister, ICharacterCollidable`.
Adoption: KT has ~45 register subclasses (Platform*, Checkpoint, Collect, Shop_*, Trigger_*, Obs_*, Interactive_*, PKB_*, SKB_*); ME has 26 files; BSE has register users too.

### 1.5 Failure modes (VERIFIED from source; field incidents INFERRED)
- Forgot base calls: overriding `OnEnable/OnDisable/Awake` without `base.` => never registered / never unregistered (KT `Pet.cs:62-92` correctly does `protected override ... base.OnEnable()`). Silent: no error, trigger just never fires.
- Collider list stale: `_colliders` is serialized and refreshed only in `OnValidate` outside Play and when `_manuallyAssignColliders` is false. Colliders added at runtime or on children created later are NOT registered. Multi-collider objects are supported (all registered) but must be present at `OnEnable`.
- v1 unregister after collider destroyed: `col == null` skipped => stale id kept in `TypedMap` (later reuse of the id by a new collider can resolve to a dead owner). Fixed in v2 by stored ids.
- Pooled objects: register/unregister are tied to `OnEnable/OnDisable`, so `SetActive(false)` on return-to-pool unregisters correctly (good). Pitfall: toggling only the collider's `enabled` leaves the registration in place (harmless) but a pooled object whose `_colliders` array contains a collider that was swapped between spawns keeps old ids in v1.
- Domain reload off / Enter Play Mode options: static `TypedMap`/`OptCollisionMap` persist between plays; `OnDisable` of last play is not guaranteed -> stale entries. No `SubsystemRegistration` reset exists in the framework (VERIFIED absence). Mitigation: call `OptCollisionLookup.Clear()` from a project `RuntimeInitializeOnLoadMethod(SubsystemRegistration)` hook.
- Callback target mismatch: sensor `T` must equal the interface the world object implements; v1 registers under the type argument only (an object registered as `ICharacterCollidable` is invisible to an `IMonsterCollidable` sensor). v2 `is T` makes any implemented interface visible.
- Raw physics messages still exist: KT keeps raw `OnTriggerEnter/OnCollisionEnter` in ~15 files (`Item_Gun_Projectile`, `Item_Throw_Linear`, `SKB_Key`, `SKB_Character`, `SKB_AI_Boss_Zone`, `Keyboard_Vertex_*PressTracker`, `SKB_BoxEvent_*`, `SKB_MinigameEvent_Boss`...). These are actor-vs-actor or per-key/tracker cases and the late SpeedKeyboard minigame; the "never raw OnTrigger" rule is therefore NOT universally followed even in the reference project (INFERRED intent: raw callbacks tolerated for pooled projectiles and non-Character actors).

---------------------------------------------------------------------------------------------------

## 2. Logic/Optimize, Pool, culling, combining, scenes

### 2.1 KT `Assets/_Game/Scripts/Logic/Optimize/` (VERIFIED, 8 files; ME has NONE of this folder)
- `DevicePolicy.cs` (static): tier-driven runtime policy. `ApplyRenderPolicy()` edits the ACTIVE URP asset properties in place (never swaps asset): `supportsCameraDepthTexture = High only`, `renderScale = Low 0.8 / else 1`, `shadowDistance = Low 0 / else 50`, `supportsHDR = High only`, `msaaSampleCount = 1` on Low. Comment states WHY: assigning `QualitySettings.renderPipeline` at runtime tears down the pipeline and CRASHES many low-end Adreno/Mali GPUs. `ApplyPhysicsPolicy()`: `Time.maximumDeltaTime = 0.1` for ALL tiers (anti death-spiral; Unity default 0.333 allows ~16 catch-up steps), and on Low `fixedDeltaTime = 1/30`. `ApplyCameraPolicy(cam)`: Low only: `renderPostProcessing=false`, `depthTextureMode=None`. Debug kill-switch booleans (`EnableRenderPolicy`, `EnablePhysicsPolicy`, `EnableCameraPolicy`, `EnableLodBias=false`) were added to bisect a Low-end crash (comment). `LowEndLodBias=0.5` exists but disabled. Paint-Keyboard scene has Apply/Restore pair that snapshots and restores depth/HDR/shadow values. Called from `Logic/Game/GameMasterInit.cs` (`RuntimeInitializeOnLoadMethod(AfterSceneLoad)`): on mobile `Application.targetFrameRate = min(refreshRate,60)`, `vSyncCount = 0`; then `ApplyRenderPolicy`, `ApplyPhysicsPolicy`. ME has the same GameMasterInit frame-rate lines (grep) but no DevicePolicy.
- Gotcha (INFERRED, standard Unity behaviour): mutating URP asset fields in the Editor writes them into the asset on disk (Medium/Low runs in the editor dirty `Mobile_RPAsset`). The Editor forces `DeviceTier.High` (`Device.cs DetectTier #if UNITY_EDITOR`), so editor does not trigger Low edits unless `Factory_Keyboard.ForceTier` cheat is set - then asset is dirtied.
- `Logic/Settings/Device.cs`: tier detection from `SystemInfo.graphicsDeviceName` (Adreno number: >=700 High; 690 Medium; >=650 High; >=612 Medium; else Low; Mali/Immortalis/Xclipse/PowerVR/Tegra/Intel/Vivante families) with RAM fallback `<3000MB Low, >=8000MB High`. Editor = High; `UseHighlightPlusOutline = IsHighEnd`. ME: no Device class found (INFERRED not present).
- Per-object policies: `DestroyIfLowEnd` (Awake destroy decor on Low), `DisableRenderersIfLowEnd` (disable listed transparent renderers on Low = overdraw cut), `LowEndCameraPolicy` (per-camera `ApplyCameraPolicy` in OnEnable), `AutoTiling_BumpToggle`, `OutlineController`/`OutlineMeshBaker` (outline via baked hull mesh vs Highlight Plus, tier-gated), `Material_Instancing_Unifier` (runtime pass in `Start`: collapses all MeshRenderers using the same shader onto ONE shared instanced material (`Factory_Material.AutoTiling`), per-object colour/tiling kept via a single reused `MaterialPropertyBlock`, logs ms + count; scope via `_roots`).
- Keyboard chunk culling thresholds (`DevicePolicy`): Low 45 m, Medium 80 m, High 150 m (`KeyboardChunkCullDistance`).

### 2.2 Distance culling with CullingGroup (VERIFIED)
- KT `Logic/Keyboard/Keyboard_Chunk_Culling_Manager.cs` (230 lines): one `CullingGroup`, `onStateChanged += OnStateChanged` (-= on destroy, line ~71), `SetBoundingDistances(new[]{distance})` (single band), `SetDistanceReferencePoint(camera.transform)`, `targetCamera`; spheres pushed once per entry (`PushSphereBuffer`); handler toggles `entry.Renderer.enabled`. `Camera.main` is re-resolved only when null/changed (`UpdateCamera`) - acceptable, not per-frame.
- KT/ME `_ARTs/Scripts/DistanceCullManager.cs`: same pattern for SpriteRenderer/TMP_Text/legacy Text, `static float CULLING_DISTANCE = 85f`, one band; editor button "Fetch All Renderers From Prefabs" fills lists; deliberately EXCLUDES `Platform_Fade_Countdown` text (must always be visible) - origin of AGENTS.md "exclude indicators" rule. Bake integrated in `Scene_Optimizer.Bake()`.
- AGENTS.md says "set distance bands once": confirmed (`SetBoundingDistances` once, refreshed only if the tier distance changes).
- BSE (vibe-coded) `Map_DecorCulling`: per-chunk show/hide distances (feedback notes: show <420 / hide >460, hysteresis band) - INFERRED hysteresis is a good addition not in KT (single band => possible flicker at the boundary).

### 2.3 Far-clip zones (VERIFIED `KT Logic/Camera/CameraFarDistanceZone.cs`, ME has same file)
BoxCollider trigger (via OptCollisionRegister) sets `CameraThirdPerson.SetFarClip(far)` -> `_freeLook.m_Lens.FarClipPlane` (Cinemachine FreeLook). Default `_farDistance = 200`; `LowEndCameraFar = 200` constant in DevicePolicy is not wired to it. Class comment: applies to ALL devices (no longer low-end only). Editor "Fit Box To Stage" button encloses child MeshRenderers (skips TMP/TextMesh). Overlap rule = deepest interior distance wins. Author workflow: one zone per enclosed stage/room, far small in enclosed rooms, large in open areas.

### 2.4 Mesh combining (VERIFIED `Core/Mesh/MeshSceneCombiner.cs` KT 446 lines; ME copy differs by Lego/Decoration-layer logic)
- Editor "Bake Renderer Groups": one traversal groups eligible static MeshRenderers BY MATERIAL and stores them in the component (`BakedRendererGroup{material, renderers[]}`) - no mesh assets written to disk, no build size cost. Runtime: loops baked list, `MeshCombineHelper.BuildCombinedMesh(material, items)`, async with ms budget (`_budgetMs = 6` in-play, `_budgetMsViaLoader = 200` behind LoadingScreen, `0` = single frame), yields at `PlayerLoopTiming.LastUpdate` (UniTask). Unbaked => runtime scan fallback (slower, same result).
- Exclusions: `_excludeRoots`, `Tag_SkipMeshSceneCombiner`, dynamic detection by name keywords `{"AnimationSequence","Move","Rotate","Tsunami","Ladder","Treadmill"}` + components (prune subtree), KT also `Decoration` layer (keeps LOD, not combined) and Lego authoring renderers (`SketchEngine.LegoEnvironment` using - note KT already references SketchEngine, i.e. mid-migration project).
- LOD: LOD0 renderers of non-dynamic LODGroups are combined, then the LODGroup is disabled and LOD1/2 renderers forced off (`DisableLodGroups`, "tắt trước rồi ép renderer off"). Net: combined static geometry loses LOD (accepted trade).
- Entry point: `Scene_Optimizer : MonoSingleton` (`Logic/Scene/Scene_Optimizer.cs`), menu `Tools/Scene Optimizer/Bake (Ctrl+Shift+B)` runs in order: MeshSceneCombiner.BakeRendererGroups -> DistanceCullManager.FetchRenderersFromPrefabs -> NavMeshSurface.BuildNavMesh -> AI waypoints -> keyboard bake/PrebakeChunk -> treadmill load; marks scene dirty. This is the "one button pre-build bake" pattern.
- Related Editor tools in KT `Scripts/Editor`: `MaterialCollectorWindow`, `Material_Match_Finder_Window`, `ColliderExtractorWindow`, `DebugVertexColors`.

### 2.5 `*_Optimized` scenes (KT `Assets/_Game/Scenes`)
Files: `Minigame_SpeedKeyboard_W1/W2/W3.unity` and `..._Optimized.unity` (VERIFIED list). Sizes (bytes): W1 3.88M vs W1_Opt 1.68M; W2 5.14M vs 3.22M; W3 4.61M vs 9.22M. Object counts (text YAML grep): W1 = 21 GO, 4985 MeshRenderers, 64 prefab instances; W3_Opt = 18 GO, 5487 MR vs W3 5482 MR. `W1_Optimized` is saved in BINARY scene format (header bytes, grep finds 0 YAML objects), W3_Optimized is text.
What differs (partly INFERRED): git commit `953d539f4 "* Optimize Keyboard & Loading Progression"` rewrote all three Optimized scenes together with `Scripts/Editor/SKB_Keyboard_Window.cs`, `Keyboard`/`Factory_Keyboard` (material `M_Keyboard_Optimized`, shader `URP_Mobile_Diffuse_KeyVertexAlphabetPress(_Fade)`), `Keyboard_Chunk_Culling_Manager`. `Keyboard` has `_isPrebakedChunk/_hasPrebakedCollider`, `PrebakeChunk()` (Grid layout only), `ClearChunk()`; `Scene_Optimizer.BakeKeyboardsWithoutPreview` does Initial bake -> `CollectFromScene` -> Clear chunks -> Prebake chunks -> Final bake. Conclusion (INFERRED): `_Optimized` = same stage content as the original but with keyboards pre-baked in-editor (combined mesh chunks + prebaked colliders + chunk culling registrations) instead of building key objects at load. Originals are retained as the editable authoring source. Folder `Assets/_Game/_Optimized/` holds `FBX_Exporter.unity` and "Speed Keyboard" NavMesh data + stage FBXs (`.../Fbx/World 1/W1_Stage_N.fbx`, ~15 stages per world). Nothing in code references the `_Optimized` scene names (grep of `Scripts`: only material mentions), so selection is via scene lists/Addressables (not verified).
Hazard (VERIFIED by file sizes/format): two parallel scene copies drift (W3_Opt is 2x larger than W3 despite "optimized"); binary scenes cannot be diffed/merged.

### 2.6 Pooling (VERIFIED KT `Logic/Pool`, 5 files)
`Pool_Manager : MonoSingleton` (persist across scenes) reads `Factory_Pool.Configs` (`Prefab`, `PoolPrewarm`, `PoolCapacityMax`), validates prewarm<=max and presence of `PoolPrefabItem` on the prefab, then `PoolPrefabGlobal.Init(configs)` (framework `CodeSketch.Patterns.Pool`; SE has `Core/Patterns/Pool/{Pooler,PoolPrefab,PoolPrefabConfig,IPoolRelease,PoolAutoReleaseParticle}`). `PoolPrefab : UnityEngine.Pool.ObjectPool<GameObject>` (create=Instantiate, get=SetActive(true), release=SetActive(false), collection check only in editor). `IPoolCallbackReceiver`/`PoolCallbackHelper` for spawn/despawn hooks. AGENTS.md mentions LeanPool; grep finds 0 LeanPool usages in KT `_Game` => the actual standard is the framework Pool (CONTRADICTION, see 5).

### 2.7 Update-less / tick throttling (VERIFIED counts, INFERRED meaning)
KT `_Game/Scripts`: 64 files with `void Update()`, 23 `LateUpdate`, 5 `FixedUpdate`, only 5 override a framework `Tick/FixedTick`. `FindObjectOfType/GameObject.Find`-family: 1 hit; `Camera.main`: 15 hits. So the codebase is largely event-driven for world objects (registry callbacks, CullingGroup, tween callbacks via PrimeTween) but NOT Update-free for actors/UI; "avoid Update on large populations" is respected for world props, not as a global rule. Low-end physics: 30 Hz fixed step policy (see 2.1).

---------------------------------------------------------------------------------------------------

## 3. ProjectSettings (VERIFIED unless noted)

| Setting | KT | ME | BSE |
|---|---|---|---|
| Unity | 6000.0.78f1 | 6000.3.22f1 | 6000.3.22f1 |
| URP package | 17.0.4 | 17.3.0 | (same asset guids as KT/ME) |
| Quality levels | 1 ("Mobile", `m_PerPlatformDefaultQuality: {}`) | 1 ("Mobile") | 2 ("Mobile","PC"); Android -> level 0 |
| Quality->URP asset | Mobile_RPAsset (guid 5e6cbd92) | same | Mobile + PC_RPAsset (guid 4b83569d) |
| vSyncCount (quality) | 0 | 0 | 0 |
| Quality shadows/dist/cascades | hard+soft(2)/40/2 | same | same |
| pixelLightCount / lodBias / skinWeights | 2 / 1 / 255 (=unlimited) | 2 / 1 / 4 | 2 / 1 (PC lodBias 2) / 2 |
| globalTextureMipmapLimit | 1 (half-res textures globally!) | 0 | 0 |
| streaming mipmaps | off | off | off |
| Fixed Timestep | 0.02 | 0.02 | 0.02 |
| Max allowed timestep | 0.1 | 0.1 | 0.333 (default) ; timeScale 20 (QA leftover!) |
| Physics solver iter/vel | 6 / 1 | 6 / 1 | 6 / 1 |
| autoSyncTransforms | 0 (off) | 0 | 0 |
| reuseCollisionCallbacks | 1 | 1 | 1 |
| contactOffset, sleep, bounce | 0.01, 0.005, 2 | same | same |
| queriesHitTriggers | 1 (default) | 1 | 1 |
| Android scripting backend | IL2CPP (`scriptingBackend Android:1`) | IL2CPP | IL2CPP |
| Android arch | ARM64 only (`AndroidTargetArchitectures: 2`) | ARM64 | ARM64 |
| Min SDK | 24 | 25 | 25 |
| Graphics API Android (manual) | GLES3 first then Vulkan (`0b000000 15000000`) | same order | Vulkan first then GLES3 |
| Managed stripping Android | 4 (High) ; stripEngineCode 1 | default | default |
| Minify release/debug | 1/1 | 1/1 | 1/1 |
| GC | incremental on | on | on |
| Static / dynamic batching (Android) | not listed in manifest grep (default) | 1 / 1 | 1 / 1 |
| androidBlitType / Swappy | 0 / off | same | same |
| runInBackground | 1 | 1 | 0 |

### 3.1 URP assets (Mobile_RPAsset vs PC_RPAsset, identical numbers in KT and ME unless noted)
- Mobile: SRP Batcher 1; MSAA field 1 (= off); render scale 1; HDR **1 (on)**; main light shadows on, shadowmap 512, 1 cascade, shadow distance 50 (asset) / 40 (quality), soft shadows supported (quality 2); additional lights per-pixel mode 1 with per-object limit 1, additional shadow res 2048 (unused value); depth/opaque texture default; dynamic batching 1; reflection probe blending/box-projection off; LUT size 16; fast sRGB conversion on; ShEvalMode 3 (KT) / 0 (ME); Adaptive Performance **on**; GPU Resident Drawer off; light layers on; light cookies off (KT) / on (ME).
- PC: shadowmap 2048, 4 cascades, additional limit 4, opaque downsampling, probe blending+box projection on, LUT 32, cookies on, dynamic batching off.
- KT Mobile has a second renderer (`Mobile_Renderer_Outline`, `m_RendererDataList` index 1, used by Highlight Plus outline on High tier); `Mobile_Renderer`: Forward (`m_RenderingMode 0`), no depth priming, intermediate texture auto.
- BSE gotcha (feedback notes): PC renderer is Deferred so baked shaders must include a GBuffer pass; Android uses Mobile Forward.
Intentional vs accidental: 512 shadow map, 1 cascade, MSAA off, SRP Batcher on, LUT16, fast sRGB, 1 per-object extra light = intentional mobile tuning (INFERRED from low values + DevicePolicy comments). HDR on in the Mobile asset, soft shadows enabled, shadow distance 50 and Adaptive Performance on = look INHERITED from the URP template, partly overridden at runtime (DevicePolicy turns HDR/depth off for non-High). `skinWeights 255` (KT) vs 4 (ME), `globalTextureMipmapLimit 1` in KT only (halves every texture - probably an intentional memory cut but undocumented; INFERRED), `timeScale 20` + `maxAllowedTimestep 0.333` in BSE = accidental QA leftover (TimeManager `m_TimeScale: 20`).

### 3.2 Frame rate / vSync (VERIFIED `GameMasterInit.cs`, KT and ME)
`Application.isMobilePlatform` -> `targetFrameRate = Mathf.Min(Screen.currentResolution.refreshRate, 60)` and `QualitySettings.vSyncCount = 0`. Cap at 60 even on 90/120 Hz devices (intentional battery/thermal limit, INFERRED). Executed in `AfterSceneLoad`, i.e. after the first scene's Awake.

### 3.3 Physics layer collision matrix
Not extracted in this pass (the `m_LayerCollisionMatrix` blob in DynamicsManager.asset was not decoded). INFERRED only. TODO for a follow-up: decode and count disabled pairs; AGENTS.md rule "keep matrix tight" is therefore UNVERIFIED against the reference projects.

### 3.4 AndroidHardwareAccelerationPostprocessor (VERIFIED, ME only: `Assets/_Game/Editor/AndroidHardwareAccelerationPostprocessor.cs`)
`IPostGenerateGradleAndroidProject`, `callbackOrder = int.MaxValue`; rewrites generated `AndroidManifest.xml` so `UnityPlayerActivity` and `UnityPlayerGameActivity` carry `android:hardwareAccelerated="true"`; throws if manifest/activity missing (fails the build loudly). Reason in the comment: Unity 6 writes `hardwareAccelerated="false"` on generated activities even when the custom manifest says true; native Google Mobile Ads video views need an accelerated Activity window from creation. It is an AD compatibility fix, not a perf optimization; KT does not have it (grep found no match) - INFERRED KT has no GMA video views or it is a latent bug. Candidate for the mobile-build-release skill, not for perf rules.

---------------------------------------------------------------------------------------------------

## 4. Import conventions (sampled; python unavailable, shell counts; KT only)

Sample: 143 texture metas, 131 FBX metas, 231 audio metas (some paths with spaces skipped by the shell; counts approximate). All VERIFIED as counts, intent INFERRED.
- Textures: Android override present on most; formats ASTC 6x6 (53), ASTC 4x4 (44), ASTC 8x8 (10) (TextureFormat 50/48/51); max size mix 256 (48), 512 (33), 1024 (13), 128 (10), 2048 (7) on the Android override, default tab larger (2048 on ~130 entries). Crunch compression 0 everywhere (142). `isReadable`: 99 off / 14 on (the 14 are likely accidental or for runtime sampling; each doubles memory). `streamingMipmaps` 0 for all 113. `sRGB` 110 on / 3 off (the 3 are normal/mask maps). Atlased/UI sprites not sampled.
- FBX (131 sampled): `materialImportMode: 2` (materials from "Import via MaterialDescription"? value 2 = Standard/legacy in Unity 6 - exact meaning not verified) on 67; `isReadable` ON for 39 of 67 sampled models (accidental or required by MeshCombiner at runtime: `CombineMeshes` needs readable source meshes in builds - INFERRED, this is a REAL requirement for `MeshSceneCombiner`); `meshCompression` 0 (43) / 1 Low (15) / 3 High (9); `weldVertices` 1 (64); `generateSecondaryUV` 0 (all); `importBlendShapes` 0 (41) vs 1 (26) (26 models import blend shapes unnecessarily - likely accidental); `importCameras/Lights` 0 (53) vs 1 (14-14) (accidental defaults); `indexFormat` auto (58) / 32-bit (9).
- Audio (231 sampled, `Assets/_Game/Audios`): `loadType` 0 DecompressOnLoad (188) / 2 Streaming (10); Vorbis (`compressionFormat: 1`) 198; quality 1.0 (115) vs 0.6 (83); `forceToMono` 0 (134) / 1 (64); `preloadAudioData` 1 (158) / 0 (40); `loadInBackground` 0 (188) / 1 (10, the streamed ones); sample rate setting 1 (preserve? "Optimize Sample Rate") on 190. Short SFX decompress-on-load, long BGM streaming = standard; quality-1.0 Vorbis everywhere is probably not tuned (INFERRED).
- No per-project import presets / `AssetPostprocessor` enforcing these were found in `Scripts/Editor` (listing: no texture/audio importer scripts) - conventions are by hand, i.e. inconsistent (INFERRED).

---------------------------------------------------------------------------------------------------

## 5. Mesh/material discipline for vibe-coded projects (user rule; cross-ref BSE, another agent mines the pipeline)

User rule: meshes/FBX are produced in a controlled way, ONE shared material, per-object colour baked into VERTEX COLORS instead of per-object textures/materials.
Evidence in BSE (`thunder-break-egg/docs/feedback-notes.md` lines 69, 80-84, 431; VERIFIED text):
- Measured before: map 3767 renderers / 149 distinct materials; decor 1290 / 97 materials. After `Map_BatchBaker` + `Map_BatchedStatic`: map segment = ONE mesh + ONE material `M_Problox_Batched` (shader `Bounce/Problox/SurfaceProboxBatched`, colour/lego/checker/albedo-slot/emission baked into vertex data); decor = 1 mesh + 1 material per chunk (146 renderers / 1 material, was 1290 / 97); play-mode measure 93 batches / 62 set-pass calls (Mobile Forward); chunks distance-culled (28/136 active at ~42k verts). Egg models baked "1 mesh + vertex color + M_VertexColor" (88 prefabs -> `Prefabs/Egg/Baked`). Baked MeshRenderers keep `ShadowCastingMode.Off`.
- Why it ties to SRP Batcher/draw calls (INFERRED standard URP behaviour, consistent with the above numbers): SRP Batcher batches by SHADER VARIANT, not by material, but each distinct material still costs a per-material CBUFFER upload and breaks `CombineMeshes`/static batching groups; combining requires identical material per group. One material + vertex colors => a combiner can merge everything static into one mesh => 1 draw call per chunk; set-pass count tracks shader variants, so a single shader keeps it near 1. MaterialPropertyBlock removes a renderer from the SRP Batcher (AGENTS.md) so colour must come from vertex data, not MPB, for large populations.
- KT counterpart (VERIFIED): `Material_Instancing_Unifier` (shared instanced material + MPB colour, for hundreds not thousands), `M_Keyboard_Optimized` + vertex-colour keyboard shader `URP_Mobile_Diffuse_KeyVertexAlphabetPress`, `MeshSceneCombiner` grouping by material, `DebugVertexColors` editor tool. Fade variant needs a separate shader: "property-driven Blend/ZWrite makes the whole shader lose SRP Batcher" (comment in `Factory_Keyboard.cs`), so keep Opaque hard-coded and split transparent variants.
- Gotcha from BSE notes: overwriting a mesh asset in place left a stale GPU mesh (delete+recreate instead); mesh assets written by bake tools are overwritten on re-run (document the bake as idempotent and keep authoring objects).

---------------------------------------------------------------------------------------------------

## 6. Contradictions with current AGENTS.md "Low-end mobile performance" (flag for edit)
1. "The reference projects ship a Mobile URP asset and a PC URP asset with per-tier Quality levels": KT and ME have ONE Quality level ("Mobile"); PC asset exists but is unreferenced by quality there. Only BSE has Mobile+PC levels. Real tiering in KT is RUNTIME (`Device.Tier` + `DevicePolicy` editing the single Mobile asset). Never swap the pipeline asset at runtime (documented crash on Adreno/Mali).
2. "HDR off unless required", "no soft shadows", "shadow 512-1024, short distance": Mobile asset has HDR ON, soft shadows supported, distance 50/40, `UseAdaptivePerformance` on. Only the shadow map (512), cascade (1) and MSAA (off) match. HDR/shadow are turned off at RUNTIME for non-High tiers.
3. "Pool with PoolManager/LeanPool": KT/ME use the framework `Pool_Manager`/`PoolPrefabGlobal` + `Factory_Pool` configs; LeanPool has 0 hits.
4. "Do not give every object OnTriggerEnter...": followed for ~45 world classes but ~15 KT files still use raw callbacks (see 1.5).
5. "Disable Physics.autoSyncTransforms, reuseCollisionCallbacks on, solver iterations default or lower": VERIFIED true in all three (6/1 is Unity default). Not mentioned in AGENTS.md but real: `maximumDeltaTime 0.1` (KT/ME) and low-end 30 Hz fixed step.
6. "Reset static collections with SubsystemRegistration": true for `CameraFarDistanceZone`; but the framework's own `OptCollisionLookup` static maps have no such reset (see 1.2).
7. "Throttle with Tick hooks": only 5 KT files use framework `Tick`; 64 use `Update`.
8. AGENTS.md states v1/v2 differences correctly (generic vs non-generic, `owner is T`, `TryFindFirst/TryGetAll`); add: stored collider ids, tombstones, shared 2D/3D map, `Clear` has no auto-caller, `OptCollisionSensorFast` is now an abstract base plus `<T>` subclass.
9. Frame rate: 60 cap (`min(refreshRate,60)`) + vSync 0 is NOT in AGENTS.md; add.

---------------------------------------------------------------------------------------------------

## Proposed classification

| # | Candidate | Type | Proposed name | Must contain |
|---|---|---|---|---|
| 1 | Collision registry usage | SKILL | `collision-registry` | (a) when to use vs raw OnTrigger (actor = sensor, world = register); (b) v1 generic vs v2 non-generic templates (`OptCollisionRegister`, `Fast<T>`, ICharacterCollidable 4 callbacks, base.OnEnable/OnDisable rules); (c) multi-collider/pooled/runtime-added collider rules; (d) failure-mode checklist (forgot base, stale colliders, domain-reload `Clear()` hook); (e) query helpers `TryFindFirst/TryGetAll` (v2) vs `ForEach/GetSnapshot` (v1) for overlap/raycast; (f) exceptions where raw callbacks are acceptable |
| 2 | Registry rule in AGENTS | RULE | `rule-no-raw-trigger` (edit existing AGENTS section) | one-paragraph rule + 3 allowed exceptions; reference `collision-registry` |
| 3 | Framework version delta | DATA | `framework-delta-codesketch-sketchengine` | table from 1.3, namespace map, files to read before coding, "same framework, v2 = optimized" statement; update when package updates |
| 4 | Device tier + runtime render policy | SKILL | `device-tier-policy` | `Device.Tier` detection (GPU family + RAM fallback numbers), DevicePolicy edits-not-swaps (+crash reason), per-tier table (depth/HDR/renderScale/shadow/MSAA/fixed step 30Hz/maxDeltaTime 0.1/post-processing), debug kill-switch bools, editor ForceTier cheat, URP-asset-dirtying gotcha, target 60 fps + vSync 0 |
| 5 | Low-end per-object toggles | RECIPE | `lowend-object-toggles` | DestroyIfLowEnd / DisableRenderersIfLowEnd / LowEndCameraPolicy components; when to use each; transparent overdraw rule |
| 6 | Distance culling | SKILL | `culling-group-distance` (merge into existing `world-batching-culling`) | single-band `CullingGroup` template, spheres pushed once, event handler toggles `enabled`, always-visible exclusion list, hysteresis (two thresholds) suggestion, tier distances 45/80/150 & 85, dispose/unsubscribe |
| 7 | Far-clip zones | RECIPE | `camera-far-zones` | zone via collision registry, deepest-zone resolution, SetFarClip into Cinemachine lens, Fit Box To Stage tool, SubsystemRegistration static reset |
| 8 | Static mesh combining | SKILL | `mesh-scene-combiner` | bake-groups-in-editor (store renderer lists in component, not mesh assets), runtime combine with ms budget behind loader (6 vs 200 ms), exclusion tags/keywords/layers, LODGroup disable, `isReadable` requirement on source meshes, never combine moving/fading/toggled objects, "Bake" menu orchestration (`Scene_Optimizer`) |
| 9 | One-button scene bake | TOOL | `scene-optimizer-bake` | ordered bake steps list, idempotency, mark-dirty, progress bar, local batch runner/MCP-callable static `Bake()` |
| 10 | Controlled mesh/material discipline | RULE + SKILL | `shared-material-vertexcolor` (rule in AGENTS, how-to in skill; cross-link BSE agent's pipeline doc) | ONE shared material per biome/chunk, colour in vertex colors, FBX created by controlled tool, SRP-Batcher/shader-variant reasoning, MPB caveat, transparent/fade shaders separated, bake idempotency + shadows Off on baked meshes, measured before/after (3767/149 -> 1/1; 93 batches/62 set-pass) |
| 11 | `_Optimized` scene variants | RECIPE | `optimized-scene-variant` | what moves into the variant (prebaked chunks/colliders/culling registration), keep original as authoring source, how to regenerate, hazard: drift + binary scenes (force text), who selects the scene; prefer ONE scene + bake step over two copies (recommendation, INFERRED) |
| 12 | Pooling | SKILL | `pool-framework-usage` | `Factory_Pool` config fields (Prefab/Prewarm/CapacityMax), `PoolPrefabItem` requirement, `IPoolCallbackReceiver`, register/unregister collision on enable/disable, return-on-disable; framework pool (not LeanPool) |
| 13 | ProjectSettings baseline | DATA + TOOL | `mobile-projectsettings-baseline` + editor validator | numbers in section 3 as target values (IL2CPP, ARM64, GLES3+Vulkan order, ASTC, autoSyncTransforms off, reuseCollisionCallbacks on, 6/1 solver, maxDeltaTime 0.1, vSync 0, 60 fps cap); validator that flags HDR on / soft shadows / timeScale != 1 / maxAllowedTimestep 0.333 / globalTextureMipmapLimit surprises |
| 14 | Import conventions | RULE + TOOL | `import-presets` | texture: Android ASTC 6x6 default (4x4 UI/hero, 8x8 backgrounds), max size by use, readable OFF, crunch off, streaming mips as needed; FBX: import lights/cameras/blendshapes OFF, readable only for combiner sources, mesh compression policy, no secondary UV; audio: SFX decompress-on-load + mono, BGM streaming, Vorbis quality ~0.5 (INFERRED target); AssetPostprocessor/Presets to enforce (none exist today) |
| 15 | Android hardware acceleration fix | RECIPE | `android-gradle-manifest-postprocess` (belongs to `mobile-build-release`) | IPostGenerateGradleAndroidProject template, why (Unity 6 writes hardwareAccelerated=false), fail-loudly behaviour, callbackOrder = int.MaxValue |
| 16 | Physics matrix + queries audit | TOOL | `physics-matrix-audit` | decode `m_LayerCollisionMatrix`, list enabled pairs, flag NonAlloc/layer-mask misuse; (matrix not yet verified in reference projects) |
| 17 | Profiling evidence | RULE | existing `mobile-perf-audit` | no profiler numbers exist in reference repos for registry/culling gains (only BSE batch counts) - require capture before claiming gains |
