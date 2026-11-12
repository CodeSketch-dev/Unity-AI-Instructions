# 03 - Object creation, pooling, config, wiring (reverse-engineered)

Sources. KT = `C:\Unity\GitProject\knife-tower\knife-tower-troll-unity\Assets\_Game` (CodeSketch, primary). ME = `C:\Unity\GitProject\monkey-escape\monkey-escape-unity\Assets\_Game` (CodeSketch). BS = `C:\Unity\GitProject\thunder-break-egg\break-and-steal-unity` (SketchEngine, `com.sketchengine`). Package paths: `<proj>\Library\PackageCache\com.codesketch@0fe9d8bab8cb\Runtime` (CS) and `com.sketchengine@522ef3079890\Runtime` (SE).
Tags: VERIFIED = read in cited file; INFERRED = deduced, not directly confirmed.

## 1. Pool system

### 1.1 Three pool APIs coexist in KT (VERIFIED)
| API | Key | Config asset | Use |
|---|---|---|---|
| `PoolPrefabGlobal` (framework, CS `Core/Patterns/Pool/PoolPrefabGlobal.cs`) | `PoolPrefabConfig` SO | yes (`Configs/Pool/*.asset`) | default: fx, text, projectiles, mini-bosses, thrown weapons |
| `PoolPrefabShared` + `PoolPrefab : ObjectPool<GameObject>` (`KT Scripts/Logic/Pool/`) | the prefab GameObject | no | ad-hoc: `CharacterTail` segments and tail destroy fx (`CharacterTail.cs:224,236,538`) |
| `PrefabPooler` (`KT Scripts/Core/Pool/PrefabPooler.cs`) | prefab GameObject | no | standalone; all pools destroyed on active-scene change |

Anything with authored tuning or shared by several scripts goes through `PoolPrefabConfig`. Do not create a fourth. (INFERRED: Shared/PrefabPooler are legacy/vibe-coded; the config pool is the house style.)

### 1.2 `PoolPrefabConfig` (VERIFIED: CS `PoolPrefabConfig.cs`, `KT Configs/Pool/Pool_Fx_Hit.asset`)
Plain `ScriptableObject`. Fields: `_prefab`, `_persistAcrossScenes`, `_deactiveOnRelease` (default true), `_poolPrewarm`, `_poolCapacity` (10), `_poolCapacityMax` (1000). Example `Pool_Fx_Hit`: persist=1, prewarm 25, capacity 50, max 50. Naming `Pool_<Kind>_<Name>.asset`, Kind in `Fx|Text|Bullet|Weapon` (VERIFIED by `ls Configs/Pool`). Subfolder `Configs/Pool/MinigameEvent/` for feature-specific pools.

### 1.3 Registry and init (VERIFIED)
- `Factory_Pool : ScriptableObjectSingleton<Factory_Pool>` (`KT Scripts/Factory/Factory_Pool.cs`): `[AssetList(Path="_Game/Configs/Pool/", AutoPopulate=true)] PoolPrefabConfig[] _configs` (auto-collects the folder) plus named hot refs (`FxAttackWave`, `FxShield`, `FxHit`) as read-only statics.
- `Pool_Manager : MonoSingleton<Pool_Manager>` (`KT Scripts/Logic/Pool/Pool_Manager.cs`, `PersistAcrossScenes=true`): in `Awake` validates each config (prewarm <= max; prefab must carry `PoolPrefabItem`, else `LogError`), then `PoolPrefabGlobal.Init(configs)` once (static `_isInitialized`).
- Feature factories hold their own `PoolPrefabConfig` fields: `Factory_Effect.FxDeath/FxLanding`, `Factory_Character.FxLevelUp`, `Factory_PaintKeyboard`/`Factory_SpeedKeyboard` money/speed text. ME has no Pool_Manager; `Factory_Text.OnInitialize()` calls `PoolPrefabGlobal.Init(Instance._speedText)` itself (VERIFIED `ME Scripts/Factory/Factory_Text.cs`).
- Local fields are also allowed: `Item_Gun._poolProjectile`, `Fx_FollowTarget._pool/_fxOnStop`, `Shop_Stand` reading `linear.Pool`. The config is passed by reference, never looked up by string/enum id.

### 1.4 Spawn / despawn API (VERIFIED, CS `PoolPrefabGlobal.cs`)
```csharp
var fx  = PoolPrefabGlobal.Get(Factory_Effect.FxDeath);              // PoolPrefabItem (TransformCached/GameObjectCached)
fx.TransformCached.position = pos;                                   // caller positions AFTER Get
var txt = PoolPrefabGlobal.Get<Text_Spread>(Instance._speedText);    // typed component via GetCached<T>
PoolPrefabGlobal.Release(cfg, gameObject);   // or Release<T>(cfg, component)
```
Internals: `_poolLookup[config]`; sets `s_Released/s_PendingInstances/s_Actives`; `Release` is idempotent (ignores released/pending); `SetActive(false)` if `DeactiveOnRelease`. If the instance has `IPoolRelease`/`IPoolReleaseAync` components, release is deferred via `PoolReleaseScheduler` ("smooth fps"); else immediate. `Clean()` runs on active-scene change: clears sets, drops non-persistent pools. Verbs are `Get`/`Release` (no Spawn/Despawn). No LeanPool in KT/ME (grep found none; `UnityEngine.Pool.ObjectPool` is used inside `PoolPrefab`).
Edge: `SKB_MinigameEvent_TrophyOrb.cs:71` comment says `Release` must not be called from a physics callback (package may `DestroyImmediate`); VERIFIED comment, behavior INFERRED.

### 1.5 How pooled objects reset state
- No central reset (VERIFIED). Each pooled component re-inits in `OnEnable` or an `Init(...)` the spawner calls right after `Get`: `Item_Gun.Shoot` positions the projectile then calls `Item_Gun_Projectile.Init(owner,target,speed,lifetime,range)`; `Text_Spread.Show(msg,pos)` stops tweens, resets scale, restarts tween; `OnDisable` stops tweens.
- Self-release: object holds its own `PoolPrefabConfig` (`_pool`, or `_poolScript.Config` via `PoolPrefabItem`) and calls `PoolPrefabGlobal.Release(_pool, GameObjectCached)` at end of life (`Text_Spread.ReleaseSelf`, `Fx_FollowTarget.CompleteFollow`, `Item_Throw_Linear.cs:261`). `Text_Spread.ReleaseSelf` does `SetParent(null)` before release - always unparent first (VERIFIED).
- `PoolPrefabItem` subscribes to `MonoCallback.EventActiveSceneChanged` and releases itself on scene change (VERIFIED, CS `PoolPrefabItem.cs`). It caches interfaces via `GetCachedInterfaces<IPoolRelease>()`; `GetCached<T>()` avoids repeated GetComponent.
- Framework helper `PoolAutoReleaseParticle` exists (VERIFIED file; usage INFERRED). No `IPoolRelease` implementer found in KT Logic (VERIFIED grep) - the deferred-release path is unused by game code.
- `IPoolCallbackReceiver {OnGet, OnRelease}` exists only for KT-local `PoolPrefabShared` (called via `GetComponentsInChildren` into a static buffer).

### 1.6 What is pooled vs not (VERIFIED by grep)
Pooled: hit/death/landing/level-up/shield fx, floating text (`Text_Spread`), gun projectiles, thrown weapons (Shuriken/Mjolnir/CaptainShield), SKB event mini-bosses/trophy orbs, tail segments. Raw `Instantiate` (files in grep): UI list items (`Minigame_Selection`), gacha boxes, jackpot UI, skin switcher/renderer, `CarpetController`, `Area_Battle`, and one fx exception `SKB_BoxEvent_Boss._effectDespawn`. Instantiate is acceptable for UI built once per screen and skin swaps.

### 1.7 SketchEngine delta (VERIFIED)
SE ships the same API under `SketchEngine.Patterns.Pool` (identical method list for `PoolPrefabGlobal`). BS (vibe-coded SE project) does NOT use it; it hand-rolls `Stack<T>` pools in `Egg_FloatingText`, `Egg_Fx`, `Pet_Manager` - a counter-example, not the standard. New SE work should use `PoolPrefabGlobal` + `PoolPrefabConfig`.

## 2. Registries (Factory_*) and prefab lookup (VERIFIED unless noted)
- Base: `ScriptableObjectSingleton<T>` (plain) or `SerializedScriptableObjectSingleton<T>` (Odin; needed for `Dictionary` fields e.g. `Factory_Item._frameByRank`). Instance asset: `Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_X.asset` (29 present in KT, one per factory, incl. `Game.Factory_Pool.asset`, `Game.Factory_Prefab.asset`).
- `Factory_Prefab` (KT/ME): ~5 serialized GameObject fields (rating popup, debug popup, notification text, quest focus msg/pointer) as `public static GameObject X => Instance._x;`. Lookup is by named static property, not id/enum. It is for UI/popup prefabs instantiated on demand, not gameplay spawns.
- `Factory_Effect`: scalar tuning (`BurnKillDelay`, `FreezeDuration`, `PoisonDuration`) + two `PoolPrefabConfig`. `Factory_Fx` (ME, has `[CreateAssetMenu]`): `CreateLandingFx()` wraps `PoolPrefabGlobal.Get<ParticleSystem>`; pattern "factory exposes a creator method, callers never see the config".
- Id-keyed registries are for authored entries, not prefabs: `Factory_Item` (`Get(string ID)`, `Get(Item_Type)`), `Factory_Character` (`_skinDictionary` by `Character_Skin_Asset.ID`), `Factory_Minigame` (`Minigame_Type`), `Factory_Shop` (`_boostByID`, `_boostByIAPProductId`).
- Pattern: serialized array + `[NonSerialized] Dictionary<>` built in `protected override void OnInitialize()` (`base.OnInitialize()` first). `Factory_Minigame` warns `Duplicate Minigame Type`; `Factory_Item` and `Factory_Character.PushToDict` overwrite silently; `Get` returns null on miss (Factory_Minigame logs error). Validation is weak/inconsistent (INFERRED gap).
- `[AssetList(Path="_Game/Configs/<Feature>/", AutoPopulate=true)]` auto-collects folder assets (`Factory_Pool`); `Factory_Item` uses AssetList without AutoPopulate.
- Runtime Instantiate avoided via: pool config refs (gameplay), factory-held prefab statics (UI), `Item_Asset.Prefab` / `Character_Skin_Asset.ReferencePrefab` resolved through factory + equip state.

## 3. Config ScriptableObject pattern (VERIFIED)
- One asset per entry, folder per feature under `Configs/<Feature>/`: `Configs/Minigame/*.asset` (6), `Configs/Character/{Brainrot,Parkour,Transformer,VIP}/`, `Configs/Item/Attack/{v1,v2}`, `Configs/Shop_Knife/`, `Configs/Wing/Wing_*.asset`, `Configs/Pool/`, `Configs/Audio/`. File prefix = type role (`Pool_Fx_*`, `Character_Brainrot_*`, `Battle_*`, `Shop_*`, `Wing_*`).
- Plain `ScriptableObject` by default (`Character_Skin_Asset`, `Item_Asset`, `PoolPrefabConfig`); `SerializedScriptableObject` only when Odin fields needed (`Minigame_Selection_Asset` with `[OdinSerialize] AI_Spawn_Config`).
- Polymorphic data without Odin: `Item_Asset` holds `[SerializeReference] Item_Info _info`; subclasses `Item_Info_Weapon/_Cape/_CoilSpring/_SpeedBoost` in `Logic/Item/Info/`; `TryGetInfo<T>(out T)` downcast.
- Authored fields are `[SerializeField]` private with read-only properties; runtime state is not stored in assets except `[NonSerialized]` caches (`Item_Asset._cachedInfo`, `Character_Skin_Asset._data`). Persistent state is reached via `Data_X.Get(ID)` (lazy `TryAdd`, e.g. `Data_Item.Get`, `Data_Character.Get`).
- Odin authoring UX: `[PreviewField]`, `[ShowIf]`, `[ValueDropdown("@IAP.IAPCatalog.GetProductIdDropdown()")]`, `[Button]`.
- Editor validation inside assets: `Minigame_Selection_Asset.OnValidate` copies `SceneAsset` name to `_sceneName`, with `[Button] Add/Remove from Build Settings`; `Character_Skin_Asset` caches mesh/material from `_referencePrefab`; `Pool_Manager.Awake` validates pools at runtime. No central config validator (INFERRED gap).
- BS (SketchEngine) keeps config SO classes in `Scripts/Configs/` (`EggZone_Asset`, `Egg_Asset`, `Pickaxe_Asset`, `Cage_Asset`; `[CreateAssetMenu(menuName="Game/Egg/Egg Zone Asset")]`) with clamped accessors; assets under `Assets/_Game/Configs/<Feature>`. Project-local convention wins over the global layout.

## 4. World objects and collision registration (VERIFIED)
- Interface `ICharacterCollidable` (`KT Logic/Character/ICharacterCollidable.cs`): `OnCollisionEnterFunc/OnCollisionExitFunc/OnTriggerEnterFunc/OnTriggerExitFunc(Character)`.
- Sensor owner: `Character : OptCollisionSensorFast<ICharacterCollidable>` with `protected override void OnCollisionEnterFunc(ICharacterCollidable t) => t.OnCollisionEnterFunc(this);` (`Character.cs:33,964-971`). `CharacterKC` also uses the interface.
- Register base (CodeSketch): `OptCollisionRegister<T> : MonoCached` (CS `Optimize/Collision/3D/OptCollisionRegister.cs`): `[SerializeField] Collider[] _colliders`, `_manuallyAssignColliders`; `Awake` collects `GetComponentsInChildren<Collider>(true)`; `OnEnable` -> `OptCollisionLookup.Register<T>(this,_colliders)`; `OnDisable` -> `Unregister`; `OnValidate` re-collects in editor. Members are `protected virtual`; subclasses call `base.Awake()/OnValidate()` (`Teleporter.cs`, `Collect_Gem.cs`).
- ~28 users (grep): `Collect`, `Collect_Gem`, `Checkpoint`, `Teleporter`, `CameraFarDistanceZone`, `BGM_Area`, `Area_Battle`, `Gacha_Box_Stand`, `Interactive_Button_On/Off/Fade`, `Interactive_Caculator_Door`, FNAF safe zone/floor detector, `Obby_Checkpoint`, PKB zones/levers/tank, SKB `TeleportGate/Return_Stage/Step_Stand`.
- `Collect : OptCollisionRegister<ICharacterCollidable>, ICharacterCollidable`: four empty `virtual` callbacks = base class for pickups.
- `Collect_Gem : Collect`: `[SerializeField] string _GUID` generated in `OnValidate` only for scene instances (skips prefab asset and prefab stage), `[Button] GenerateGUID`; `OnTriggerEnterFunc` -> guard `character.IsPlayer`, `Data_Currency.Gem.Value += value`, `AudioManager.Play(Factory_Audio.SfxGemCollected)`, `UINotificationText.Push`, `SetActive(false)`, PrimeTween delay respawn (`_pTweenRespawn.Stop()` in `OnDestroy`).
- `Checkpoint : ..., ICheckpoint`: `[SerializeField] int _index`; `Construct(int)` is Undo/SetDirty aware; `SetCollisionEnabled` loops `_colliders`; `OnTriggerEnterFunc` posts `StaticBus<Event_Checkpoint_Enter>` for every character but writes `Data_Checkpoint` only for `IsPlayer` and when `_index > saved`; `[Button] SnapToGround` raycasts down.
- `Teleporter`: `_otherTeleporter` or `_destination`; `async UniTaskVoid TryTeleport` with `finally` restoring control; static `HashSet<Character>` guard not reset via `RuntimeInitializeOnLoadMethod` (INFERRED risk).
- Platforms (`Platform/*`) and obstacles (`Obs_*`) follow the same family (INFERRED from listing; not read).
- SketchEngine: `OptCollisionRegister` non-generic, sensor filters `owner is T` (per global instructions; SE file `Optimize/Collision/3D/OptCollisionRegister.cs` exists, body not read - INFERRED).

## 5. Scene vs prefab vs minigame conventions
- Scene-authored objects: collectibles, checkpoints, teleporters, zones are placed in minigame scenes and tuned by serialized fields; per-scene identity via GUID (`Collect_Gem._GUID`) or index (`Checkpoint._index`). Global tuning goes to a Factory/config (VERIFIED for those types).
- Each minigame is a scene (`Minigame_Selection_Asset._sceneName`), loaded by `SceneLoaderPlus.Load` or `LoadingScreen.Load` per `Minigame_LoadType`; `Minigame_Static.Type` (DataValue) holds the current type; `Minigame_Master` sets it in `Awake` (VERIFIED from `Minigame_Static` comment; Master body not read).
- Addressables: `com.unity.addressables 2.9.1` is in the KT manifest and `Assets/AddressableAssetsData` exists, but grep `Addressables\.` in KT `Scripts` finds no calls -> unused for gameplay loading (VERIFIED for KT only; ME not checked).
- AI spawn per minigame lives in `Minigame_Selection_Asset._aiSpawnConfig` (`AI_Spawn_Config`, Odin-serialized). Pickups respawn in place (disable/enable) rather than spawn/despawn.

## 6. Worked examples

### Example A - add a new pickup (`Collect_Coin`)
Traced from `Logic/Collect/Collect.cs`, `Collect_Gem.cs`, `Data_Currency`, `Factory_Audio`.
1. Script `Assets/_Game/Scripts/Logic/Collect/Collect_Coin.cs`: `public class Collect_Coin : Collect`; serialized `_value`, `_respawnTimeInSeconds`; override `OnTriggerEnterFunc(Character c)`, call `base`, guard `if (!c.IsPlayer) return;`.
2. Persistence only if "collect once" memory is needed: add a keyed accessor to `Data_Currency` (pattern `IsGemWorldCollectedFirstTime(_GUID)` / `SetGemWorldCollected`), lazily created; copy the `ShouldGenerateGuidInScene` guard for GUID generation.
3. Effect: `Data_Currency.<X>.Value += value` (DataValue change drives HUD), `AudioManager.Play(Factory_Audio.SfxX)` (new `AudioConfig` field in `Factory_Audio` + asset in `Configs/Audio/`), `UINotificationText.Push(GameConstants.MsgReceiveX(value))`.
4. Collision wiring: nothing manual; `Collect` base registers child colliders in `OnEnable`. Prefab: root with `Collect_Coin`, child collider `isTrigger=true` on a layer the Character matrix hits, mesh/vfx child; save `Prefabs/Collect/Collect_Coin.prefab` (folder INFERRED), place instances in scene.
5. Respawn: `SetActive(false)` + `PrimeTween.Tween.Delay(...).OnComplete(OnRespawn)`; stop tween in `OnDestroy`; `OnRespawn` checks `this == null`.
6. Pickup fx: add `PoolPrefabConfig` field, `PoolPrefabGlobal.Get(cfg)` then position; never `Instantiate`.
7. Verify: Play, collect as player, check value + HUD, restart for persistence, re-enable after delay, no console errors (pipeline checks, not read from code).

### Example B - add a new character skin (Brainrot)
Traced from `Logic/Character/Skin/Character_Skin_Asset.cs`, `Factory_Character.cs`, `Data_Character.cs`, `Event_Character_Skin_Equip.cs`, `Logic/Shop/Skin/Shop_Skin.cs`.
1. Reference prefab with `SkinnedMeshRenderer` or `MeshFilter` + material; `ResolveMeshFromPrefab` reads mesh/material from `_referencePrefab` (`_useSharedMesh=true` shares the skeleton; disable for a different skeleton).
2. Asset `Configs/Character/Brainrot/Character_Brainrot_<Name>.asset` (`Character_Skin_Asset`): `_type=Brainrot`, `_skinName` (ID key into `Data_Character._skins`), `_unlockType` (`Currency_Type.Gem` + `_unlockPrice`; `IAP_NoneConsumable/IAP_Subscription` + `_iapProductId` via IAPCatalog dropdown; or `_dailyLoginOnly`), thumbnail/avatar sprites, `_infoWeapon` (`Item_Info_Weapon`, shown for Brainrot).
3. Registry: add to `Factory_Character._skinBrainRot[]` (or `_skinNormal/_skinSquid/_skinTransformer/_skinVIP`). `OnInitialize` fills `_skinDictionary` (by ID, silent overwrite) and `AllSkin` (Normal + BrainRot only). A brand-new type needs enum + `PushToDict` + shop edits (INFERRED).
4. Persistence: no code; `Data_Character.Get(ID)` does `TryAdd(new CharacterSkinData())`.
5. Shop: `Shop_Skin` iterates `Factory_Character.SkinNormal/SkinVIP` (lines ~210-222), so factory listing makes it visible (VERIFIED for Normal/VIP; Brainrot INFERRED).
6. Events: `UnlockOnly()` posts `Event_Character_Skin_Unlocked`; `Equip()` posts `Event_Character_Skin_Equip(skin, character)`; `Character_Skin_Switcher` consumes and swaps mesh. Expired subscription falls back to `SkinDefault.Equip()` (`Factory_Character.SubscriptionStatus_OnChanged`).
7. Verify: no missing refs, shows in shop, unlock -> equip -> mesh swaps in game, equipped skin survives restart, default fallback works.

### Example C - add a new minigame entry
Traced from `Logic/Minigame/Minigame_Type.cs`, `Selection/Minigame_Selection_Asset.cs`, `Factory_Minigame.cs`, `Data_Minigame.cs`, `Selection/Minigame_Selection.cs`, `Minigame_Static.cs`.
1. Enum: add to `Minigame_Type` with a stable explicit number (`SpeedKeyboard=0, SnakeTower=1, CamoTower=2, EasyObby=11, MonsterTower=101, PaintKeyboard=201`; ids grouped by family). The enum is a dictionary key in `Data_Minigame` and names are saved in `_activedSortOrder`, so never renumber/rename. `Minigame_Helper.ToCheckpoint/ToDeath/ToRevive/...` generate analytics names `{type}_...` automatically.
2. Scene under `Scenes/` with `Minigame_Master`, player spawn, checkpoints (ascending `_index`), collectibles; add the type to `Minigame_Static.IsWeaponAllowedForType` false-list if weapons are off.
3. Asset `Configs/Minigame/<Title>.asset` (`Minigame_Selection_Asset`): `_type`, `_title`, `_loadType` (TransitionPlus default; LoadingScreen for heavy init), `_thumbnail`, `_loadingBackground`, `_isCommingSoon`, `_aiSpawnConfig`, `_scene` SceneAsset. `OnValidate` fills `_sceneName`; click `Add to Build Settings`.
4. Registry: append to `Factory_Minigame._minigames[]`; `OnInitialize` builds `_mapMinigame` (duplicate -> warning). `Get(type)` logs error if missing.
5. Data: `Data_Minigame.GetEnter(type)` / `GetCompletedThisSession(type)` are keyed `DataValue`s created lazily (no schema edit). Own persistent domain -> new `Data_<Name>` + `Factory_<Name>` (as `Data_SpeedKeyboard`/`Factory_SpeedKeyboard`, `Data_PaintKeyboard`/`Factory_PaintKeyboard`).
6. UI: `Minigame_Selection.Start` instantiates one large + N small items from `Factory_Minigame.GetActiveListMinigame()` (saved sort order else array order). Remote config can reorder via `OnRemoteConfigLoaded` (aliases: enum name, PascalCase-split, Title).
7. Feature code: `Event/Minigame/<Name>/Event_<Name>_*.cs`, `Logic/Minigame/<Name>/`, new `Game.Factory_<Name>.asset` under `Resources/CodeSketch/ScriptableObjectSingletons/` if tuning is added; pooled fx under `Configs/Pool/<Name>/` (auto-collected) with `PoolPrefabItem` on prefab.
8. Verify: selection shows entry, tap loads scene, `Factory_Minigame.Reload()` and `BackHome()` work, no duplicate-type warning.

## 7. Gaps and risks noticed
- No tool/test that every config asset is registered in its factory (except `AutoPopulate` pools) or that IDs are unique (INFERRED; warnings in only some factories).
- Three pool systems in KT; two should be avoided in new code.
- `Teleporter.s_teleportingCharacters` static not reset on subsystem registration (INFERRED; violates global rule).
- Pooled prefab root requires `PoolPrefabItem`; only checked at `Pool_Manager.Awake` via `LogError`, not at authoring time.
- BS hand-rolls pools instead of the SE framework pool.

## 8. Proposed classification
| # | Kind | Proposed name | Must contain |
|---|---|---|---|
| 1 | RULE | `pool-everything-spawned-repeatedly` | `PoolPrefabGlobal.Get/Release` with a `PoolPrefabConfig` (no Instantiate/Destroy in loops); Release idempotent, never from physics callback; unparent before release; reset state in `Init(...)`/`OnEnable`, stop tweens in `OnDisable`; prefab root needs `PoolPrefabItem`; no extra pool implementations (not `PoolPrefabShared`, `PrefabPooler`, ad-hoc `Stack<>`). |
| 2 | RECIPE | `recipe-add-pooled-fx` | Prefab + `PoolPrefabItem` + `Pool_Fx_<Name>.asset` (persist/prewarm/capacity by frequency, prewarm <= max); place in `Configs/Pool/` (auto-listed in `Factory_Pool`); expose via factory static or serialized field; spawn + position call; self-release pattern; verify. |
| 3 | SKILL | `config-and-factory-authoring` (extends `config-driven-feature`) | Plain SO vs Odin decision; one asset per entry in `Configs/<Feature>/` with role-prefix names; `[SerializeReference]` polymorphic info; factory = array + `[NonSerialized]` dict in `OnInitialize` with duplicate/missing-ID errors (stronger than KT); singleton asset location per framework (CS `Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_X.asset`; SE: inspect loader); read-only static accessors; `OnValidate` derived fields. |
| 4 | RULE | `world-object-collision-registration` | Actor derives `OptCollisionSensorFast<IXCollidable>`; world object derives `OptCollisionRegister` (CS generic / SE non-generic) and implements the interface; no `OnTriggerEnter`+`GetComponent`; call `base.Awake/OnValidate`; empty unused callbacks; guard `IsPlayer`; reset statics with `RuntimeInitializeOnLoadMethod(SubsystemRegistration)`. |
| 5 | RECIPE | `recipe-add-pickup` | Example A: `Collect` subclass, scene-GUID guard, `DataValue` write, `Factory_Audio` sfx, notification, PrimeTween respawn + `OnDestroy` stop, prefab with trigger collider, verification. |
| 6 | RECIPE | `recipe-add-skin-or-item` | Example B: asset, ID uniqueness, factory array registration, unlock-type matrix (Gem/IAP/Subscription/DailyLogin), `Event_*_Unlocked/Equip`, shop visibility, default fallback, save/restart check. |
| 7 | RECIPE | `recipe-add-minigame` | Example C: enum numbering (never renumber), scene + Master, `Minigame_Selection_Asset`, Build Settings, factory registration, per-minigame Data/Factory/Event/Logic/Pool folders, remote-config sort alias, analytics-name helpers. |
| 8 | TOOL | `config-registry-audit` (editor menu/script) | Compare `Configs/<Feature>` assets vs factory arrays: unregistered assets, duplicate IDs, null prefab/sprite refs, pool config prefab missing `PoolPrefabItem`, prewarm > max, `Factory_*` class without singleton asset, minigame scene missing from Build Settings. |
| 9 | DATA | `object-creation-conventions.json` | Naming prefixes (`Pool_Fx_`, `Character_<Type>_`, `Shop_`, `Battle_`), folder map per feature, singleton path per framework (CS vs SE), API per object kind (fx/text/projectile pooled; UI list items Instantiate OK), enum id-family numbering. |
| 10 | SKILL | `framework-detect-pool-collision` | Detect CodeSketch vs SketchEngine from `manifest.json`; namespace map (`CodeSketch.Patterns.Pool` vs `SketchEngine.Patterns.Pool`); `OptCollisionRegister<T>` generic vs non-generic; never translate by memory; read installed `PoolPrefabGlobal.cs` / `OptCollisionRegister.cs` first. |
| 11 | RULE | `addressables-not-default` | Addressables installed but unused in KT gameplay code; do not introduce addressable loading unless asked; heavy content goes through scene + `LoadingScreen.Load`. Moderate confidence (grep of KT runtime scripts only). |
