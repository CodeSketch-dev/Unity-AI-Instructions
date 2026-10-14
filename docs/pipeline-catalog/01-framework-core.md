# 01 - Framework core, singletons, initialization

Scope: the in-house Unity framework (CodeSketch = old snapshot, SketchEngine = current, same lineage), its singleton patterns, and boot order.
Tags: **VERIFIED** = read in code (cited). **INFERRED** = my reasoning.

Sources read:
- CS = `knife-tower/knife-tower-troll-unity/Library/PackageCache/com.codesketch@0fe9d8bab8cb/Runtime` (package 0.1.1). Same code in monkey-escape (VERIFIED manifest: both use `com.codesketch`).
- SE = `thunder-break-egg/break-and-steal-unity/Library/PackageCache/com.sketchengine@522ef3079890/Runtime` (package 1.0.1). Only project on SketchEngine; vibe-coded, so read for API only.
- Game code: `knife-tower/.../Assets/_Game/Scripts` (KT), `monkey-escape/.../Assets/_Game/Scripts` (ME).

## 1. Version delta: CodeSketch (old) -> SketchEngine (current)

Same framework, renamed and refactored (per user; consistent with identical file layouts, VERIFIED by diffs). SketchEngine is the target for new projects. Do not hand-translate by regex: use the table.

| Area | CodeSketch (CS) | SketchEngine (SE) | Tag |
|---|---|---|---|
| Root namespace / package | `CodeSketch`, `com.codesketch` 0.1.1, asmdef `CodeSketch` | `SketchEngine`, `com.sketchengine` 1.0.1 | VERIFIED package.json |
| Debug class | `CodeSketchDebug` | `SketchDebug` | VERIFIED |
| Factory-of-framework SO | `CodeSketchFactory` | `SketchEngineFactory` (Core/SketchEngineFactory.cs:1-297, prefab overrides via static `Set*Override`) | VERIFIED |
| Helper | `CodeSketchViewHelper.PushAsync` | `SketchEngineViewHelper.PushAsync` (null-safe on ViewContainer, SE View/SketchEngineViewHelper.cs) | VERIFIED |
| Audio type enum | `AudioType` | `SketchAudioType` (avoids clash with `UnityEngine.AudioType`) | VERIFIED; reason INFERRED |
| Utility classes | `Utils*` (`UtilsMath`, `UtilsTime`...) | `Utility*` (`UtilityMath`...), plus `RNG`, `UtilityCanvas` | VERIFIED file list |
| Haptics | `Haptic*` | `Modules/Taptic` (`Taptic.tapticOn`; KT GameMasterInit.cs:55 uses `Taptic`) | VERIFIED |
| DataBlock accessor | `DataBlock<T>.Instance` | `DataBlock<T>.INSTANCE` (SE DataBlock.cs:23). Game code `Data_X.Instance._field` becomes `INSTANCE._field` (SE DataSettings.cs:13) | VERIFIED |
| DataValue | plain setter fires `OnValueChanged` always (CS DataValue.cs:81-89) | setter skips when equal, fires `OnValueChanged`, then `DataDirtyNotifier.Raise()`; event is `[field: NonSerialized]` (SE DataValue.cs:157-172) | VERIFIED |
| Persistence | save only on app pause/quit (CS DataBlock.cs:36-49); synchronous write w/ hash dedupe (CS DataFileHandler.cs:14) | adds debounced autosave 2 s after any DataValue change (SE DataBlock.cs:11,90-96), background writer thread, atomic tmp->bak->final write, `.bak` crash recovery, FNV-1a hash skip (SE DataFileHandler.cs:63-249) | VERIFIED |
| Serializer | `#if CODESKETCH_MEMORYPACK / CODESKETCH_ODINSERIALIZER / else BinaryFormatter` (CS DataSerializer.cs) | Odin binary with 4-byte `SKO1` magic header; falls back to legacy BinaryFormatter for old saves (SE DataSerializer.cs:10-42) | VERIFIED |
| Load warmup | none in package; KT hand-rolls `DataBlockPreloader.PreloadAll()` (reflection scan) | `DataBlockWarmup` auto-runs `BeforeSceneLoad`, scans assemblies (or build-time generated registry `DataBlockRegistryBuilder`), calls `Warmup()` per block; switch `DataWarmupConfig.Enabled` (SE DataBlockWarmup.cs:188-231) | VERIFIED |
| Save of unused block | `Save()` calls `Instance` (creates it) | `Save()` returns if `_INS == null` (SE DataBlock.cs:120-126) | VERIFIED |
| Mono base | `MonoBase` (registers Tick/LateTick/FixedTick on `MonoCallback.SafeInstance`, CS MonoBase.cs:60-110) + `MonoBaseOpt` + `MonoCached` (data only) | `MonoBase`/`MonoBaseOpt` removed. `MonoCached` has `public virtual Tick/LateTick/FixedTick` but no dispatcher in the package (SE MonoCached.cs:43-57; grep found no caller). `MonoCachedOpt` = old MonoBaseOpt | VERIFIED; "Tick is dead unless project dispatches" INFERRED |
| MonoSingleton base | `MonoSingleton<T> : MonoBase` | `: MonoCached` (SE MonoSingleton.cs:17) | VERIFIED |
| Collision register | generic `OptCollisionRegister<T>`, `Register2<T1,T2>`, `Register3` (CS OptCollisionRegister.cs:10) | non-generic `abstract class OptCollisionRegister : MonoCached`; owner implements any number of interfaces; plus `OptCollisionMap` (SE OptCollisionRegister.cs:10) | VERIFIED |
| Popup root | `FindObjectsOfType<Canvas>`, no events | `FindObjectsByType`, `EventPopupOpened/Closed`, `Count`, `SelectRootFromScene` prefers `PopupRootSetter`, else highest-order overlay canvas (SE PopupManager.cs:17-81) | VERIFIED |
| Popup animation | n/a | DOTween `Sequence` played forwards, closed by `PlayBackwards`, `Sequence_OnRewind` destroys (SE Popup.cs:206-383) | VERIFIED |
| View push | `ViewContainer.PushAsync(AssetReference)` | same, plus try/finally `_isTransiting` reset and Addressables handle release on failure (SE ViewContainer.cs:67-113) | VERIFIED |
| Audio | `HashsetActives` tracking, `ReturnPool` | pooled `UnityEngine.Pool.ObjectPool<AudioScript>`, `Release` internal (SE AudioManager.cs) | VERIFIED |
| Extra modules | Stat/Buff, HealthBar, TextDamage, AdsLoading, BigNumber, Billboard, OptCollision Pair/Triple 2D | Not in SE package (moved to project or dropped) | VERIFIED file lists |
| New in SE | - | `UITextCompactValue`, `CompactValueFormatter`, `Sprite_Button/Sprite_Animated` (world touch), `InternetPopupView`, `UIScrollRect`, `WorldCanvasEnabler` | VERIFIED file list |
| SO singleton Resources folder | `Resources/CodeSketch/ScriptableObjectSingletons/` | `Resources/SketchEngine/ScriptableObjectSingletons/` | VERIFIED |
| Deps | Odin optional via define | SE requires `OdinSerializer`, PrimeTween (DataBlock), DOTween (Popup), UniTask, Addressables, Odin Inspector | VERIFIED usings |

Mechanical migration CS -> SE: namespace rename; `Instance` -> `INSTANCE` on `DataBlock` only (NOT on `ScriptableObjectSingleton`/`MonoSingleton`, which keep `Instance`); `Utils` -> `Utility`; `AudioType` -> `SketchAudioType`; `OptCollisionRegister<T>` -> `OptCollisionRegister` (drop generic argument, keep interface); singleton asset folder rename; `MonoBase` -> `MonoCached`; `Haptic` -> `Taptic`. Verified only by reading both trees; no migration was compiled by me.

Project-local shadow: KT defines its own `Game.MonoCached : MonoBehaviour` (KT Core/MonoCached.cs:1-40) duplicating the framework `CodeSketch.Mono.MonoCached`. VERIFIED duplicate; cause INFERRED (older project predating the framework class). Do not copy into new projects.

## 2. DataBlock<T> / DataValue<T> (persistent data)

What: a `[Serializable]` class per save domain with a static lazy singleton, auto file persistence in `Application.persistentDataPath/<Root>/<typeof(T)>` (CS root `CodeSketch.Data`?, SE `SketchEngine.Data`, SE DataFileHandler.cs:39,53-56). VERIFIED SE; CS root name INFERRED.

How (SE DataBlock.cs:23-39, CS DataBlock.cs:11-27):
1. First access to `INSTANCE`/`Instance`: `DataFileHandler.LoadFromDevice<T>(typeof(T).ToString())` (key includes namespace, e.g. `Game.Data_Currency`).
2. If null (no file / load error), `Activator.CreateInstance(typeof(T))` (parameterless ctor, field initializers run; deserialized objects skip ctors).
3. `Init()` runs ONCE on the instance, loaded or new. Base `Init` subscribes pause/quit to `MonoCallback` (auto-created singleton) so the block saves when app leaves foreground. Comments say Android `OnApplicationPause(true)` is the only reliable save point and `OnApplicationFocus` must not be used (ad overlays/permission dialogs fire it -> ANR) (CS DataBlock.cs:31-35; stated in code).
4. SE additionally: `DataValue.Value` set -> `DataDirtyNotifier.Raise()` -> `MarkDirty` -> PrimeTween delay 2 s (unscaled) -> `Save()` (SE DataBlock.cs:90-102). Comment: batches changes, crash loses at most a few seconds (stated in code, Vietnamese).

Why `??=` in `Init`: deserialization leaves new fields null when a save predates them; `Init` back-fills (INFERRED from pattern; every block does it: KT Data_Currency.cs:124-136, SE DataMaster.cs:17-25). Binary serializers do not run initializers on load, so a field added in an update is null for existing players unless back-filled (INFERRED, standard behavior).

Why DataValue: observable value with `OnValueChanged` so UI binds without polling (INFERRED; used by `AudioManager.VolumnMusic`, KT GameMasterInit.cs:42-53). Events are not serialized in SE (`[field: NonSerialized]`); in CS the event field is serializable via BinaryFormatter default? Unknown, INFERRED risk: avoid binding listeners that must survive save.

Minimal usage (real, KT Data_Currency.cs:68-136, adapted to SE):
```csharp
public class Data_Currency : DataBlock<Data_Currency>
{
    [SerializeField] DataValue<double> _gem;
    [SerializeField] Dictionary<string, bool> _flags;
    public static DataValue<double> Gem => INSTANCE._gem;   // CS: Instance
    protected override void Init()
    {
        base.Init();
        _gem ??= new DataValue<double>(0);
        _flags ??= new Dictionary<string, bool>();
    }
}
// read/write
Data_Currency.Gem.Value += 10;                 // fires OnValueChanged, marks dirty
Data_Currency.Gem.OnValueChanged += UpdateUI;  // unsubscribe symmetrically
```

Keyed record pattern: `Dictionary<K, DataValue<T>>` + `TryAdd` lazily (KT Data_Currency.cs:93, 107). VERIFIED.

Common mistakes:
- Forgetting `base.Init()` -> no pause/quit save hook (SE: also no dirty hook) (VERIFIED from code; effect INFERRED).
- Not null-guarding new fields with `??=` -> NRE for existing saves.
- Mutating a collection inside the block (`_dict[k] = v`, `_list.Add`) without a `DataValue` change: SE autosave is NOT triggered (dirty only raised by `DataValue.Value` setter); only pause/quit saves it. VERIFIED code path; consequence INFERRED.
- Storing scene objects/UnityEngine.Object refs in a block (binary serializer fails). INFERRED.
- Calling `DataBlock.Save()` repeatedly in a loop (CS writes synchronously every call; hash dedupe only avoids writing unchanged bytes, CS DataFileHandler.cs:36-37).
- Reading `Instance` at the first frame of a heavy scene: first access pays disk read + deserialization. Hence preloading (section 8).
- Changing a field's type/name between releases: BinaryFormatter / Odin mismatch -> load fails -> `Load` catches, returns null, a FRESH block is created (progress loss). VERIFIED catch/null path (SE DataFileHandler.cs:253-279); consequence follows.
- Debug wipe: `DataBlock<T>.Delete()` nulls the instance but other holders keep the old reference. VERIFIED code.

## 3. ScriptableObjectSingleton<T> / SerializedScriptableObjectSingleton<T>

What: a ScriptableObject that is its own global singleton; the house "Factory" base. Serialized variant derives Odin `SerializedScriptableObject` (dictionaries, polymorphism). VERIFIED (SE ScriptableObjectSingleton.cs:5-112; Serialized...:5-170 identical logic).

Locate/create/load (first `Instance` access):
1. `Resources.Load<T>("<Root>/<typeof(T)>")`. `typeof(T)` prints the FULL name including namespace, so the asset file is `Game.Factory_Currency.asset` (VERIFIED KT folder listing `Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_*.asset`; SE: `Assets/Resources/SketchEngine/ScriptableObjectSingletons/Game.Factory_Audio.asset`).
2. `#if UNITY_EDITOR` and still null: creates dir `Assets/Resources/<Root>/` and a NEW EMPTY asset via `ScriptableObjectHelper.CreateAsset` (AssetDatabase.CreateAsset + Refresh). So in editor a missing asset is silently auto-created with default values (SE :77-87). In a player build a missing asset yields null -> NRE at first access.
3. `OnInitialize()` virtual runs once, right after load, before `Instance` returns (SE :88). Build dictionaries/caches here. A static accessor called from inside `OnInitialize` of the same type recurses? `s_instance` is already assigned before `OnInitialize`, so re-entry is safe (VERIFIED order: assign at :75/:85, init at :88).
4. `Release()` runs `OnRelease`, nulls the instance and `Resources.UnloadUnusedAssets()` (:95-101). Note: it calls `Instance` first, so releasing an unloaded singleton loads it.
Note root path is any `Resources` folder: KT and ME keep them under `Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/` (VERIFIED), SE project under `Assets/Resources/SketchEngine/...` (VERIFIED); the editor auto-create path is always `Assets/Resources/...`, which is why a freshly auto-created asset lands outside `_Game` and must be moved (INFERRED consequence; moving via AssetDatabase keeps the Resources lookup valid).

Why (INFERRED, not stated in code): zero scene wiring, designers tune values in one asset per feature, accessible statically from anywhere (`Factory_Currency.ReceiveMoreCupAmount`), loaded lazily, no boot-order dependency; Resources chosen because it needs no registry. Cost: everything referenced by a singleton is loaded when it is first touched and lives in memory (Resources.Load pulls dependencies), so heavy prefab refs in one factory inflate memory (INFERRED, standard Unity behavior).

Usage (KT Factory/Factory_Currency.cs:1-30):
```csharp
public class Factory_Currency : ScriptableObjectSingleton<Factory_Currency>
{
    [SerializeField] GameObject _moreCupPopup;
    [SerializeField] int _receiveMoreCupAmount = 100;
    public static int ReceiveMoreCupAmount => Instance._receiveMoreCupAmount;
    public static void OpenMoreGemShop() => PopupManager.Create(Instance._moreCupPopup);
}
```
Pitfalls: generic arg must be the class itself (`T` = self) or the cast `s_instance as ScriptableObjectSingleton<T>` returns null and `OnInitialize` never runs (VERIFIED cast). Renaming the class or namespace breaks the Resources name (asset must be renamed too, GUID refs stay). Static fields in a factory persist across domain-reload-off Play sessions: reset with `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` (KT Factory_Jackpot.cs:41 shows a related init; Character_Static.cs:19, CameraFarDistanceZone.cs:29 reset statics). Editing a singleton asset from code at runtime in the Editor writes the asset to disk (ScriptableObject), not in builds.

## 4. MonoSingleton<T> and MonoCallback

VERIFIED (SE MonoSingleton.cs; CS MonoSingleton.cs:16-152 same logic).
- `[DefaultExecutionOrder(-50)]`, abstract `PersistAcrossScenes`.
- `Instance`: returns cached; else `FindFirstObjectByType<T>()` (scene lookup, NOT creation). Returns null and logs an error if `IsDestroyed` (quit/destroyed).
- `SafeInstance`: `Instance` or creates `new GameObject("[Singleton] <T>")` + AddComponent (CS :60-107). Use it only for infrastructure that must exist (MonoCallback, AudioManager pool).
- `Awake`: first one wins, optional `DontDestroyOnLoad`; duplicates `Destroy` their GameObject (CS :111-129). `OnDestroy` flags `IsDestroyed = true`.
- `HasInstance`, `Attach(Transform)`.
- Subclasses MUST call `base.Awake()`/`base.OnDestroy()` (they are `protected virtual`); e.g. SE ViewContainer.cs:22-34, AudioManager.cs `Awake` calls `base.Awake(); InitPool();`.
- `MonoCallback : MonoSingleton<MonoCallback>` (persistent) forwards Update/LateUpdate/FixedUpdate/Pause/Focus/Quit/ActiveSceneChanged as C# events for non-MonoBehaviour classes (CS MonoCallback.cs:312-391). DataBlocks use it for save hooks.
Project singleton example: `GameSingleton : MonoSingleton<GameSingleton>` with `PersistAcrossScenes => true` (KT Logic/Game/GameSingleton.cs).
Why: INFERRED. `IsDestroyed` guard prevents resurrecting objects during OnDestroy/quit ("Check HasInstance ... destructor" message, CS :38-40, stated).
Mistakes: using `Instance` (not `SafeInstance`) and assuming non-null in the first frame (HasInstance check used in KT Currency_MoreCup.cs `HasInstance`); accessing `X.Instance` from `OnDestroy` of another object during quit (logs error, returns null); putting two in the Home and next scene without `PersistAcrossScenes` consistency.

## 5. StaticBus<T> / IEvent

SE Core/Patterns/EventBus/StaticBus.cs:13-43 (CS identical, namespace `CodeSketch.Patterns.Observer`). VERIFIED.
- `static Action<T> s_Action = delegate {}` per event type; `Subscribe(+=)`, `Unsubscribe(-=)`, `Post(T)` = direct delegate invoke. Synchronous, no queue, no allocation except the event object.
- Doc comment (stated): fastest simplest bus; do not use in packages (conflicts with user project); use only inside a project you own.
- No unsubscribe on destroy automatically: a destroyed MonoBehaviour left subscribed throws `MissingReferenceException` on next Post, and static state survives Play-mode sessions when domain reload is off (INFERRED).
Event class (KT Event/Character/Event_Character_Booster.cs): `class X : IEvent` with constructor-set `{ get; private set; }` payload. Post: `StaticBus<Event_AI_ConstructAllowed>.Post(new ...)`.
Subscribe in real code: KT AI.cs:86-89 subscribes in `Awake`, handler `StaticBus_Event_AI_RollingWeapon_Start`. NOTE: grep of AI.cs found no matching `Unsubscribe` (OnDestroy at :91 does not remove it) - VERIFIED absent in that file; so the reference project itself leaks here. The rule "pair every Subscribe with Unsubscribe" is a house rule that the reference code does not always follow.
Why events instead of direct refs: many-to-many between UI/AI/gameplay (INFERRED). Cost: a new event instance per Post (use sparingly in per-frame paths).

## 6. StateMachine<TLabel> / IStateMachine

SE Core/Patterns/StateMachine (CS identical). VERIFIED.
- `IStateMachine`: `Init, OnStart, OnUpdate, OnFixedUpdate, OnStop, OnDestroy`.
- `StateMachine<TLabel>`: dictionary label -> delegates. `AddState(label, IStateMachine)` calls `Init()` immediately and binds delegates (:213-218); delegate overloads allow partial states (`AddState(label)` = empty state, used for `Stop`). `CurrentState` setter -> `ChangeState`: calls `onStop` of the old state, switches, `onStart` of the new, fires `OnStateChanged(prev,new)`. Transition to same state re-runs stop/start (:304-327).
- `Update()/FixedUpdate()` must be forwarded by the owner (it is not a MonoBehaviour). `Dispose()` invokes every state's `onDestroy` (finalizer also calls Dispose).
- Gotchas: `CurrentState` getter throws NRE before first assignment (`currentState.lable`; the owner must set an initial state - KT does `CurrentState = AI_State.Stop`, AI.cs:197); `PreviousState` is never set (the assignment is commented out at :314), so it equals current; `ChangeState` throws `KeyNotFoundException` for an unregistered label; `OnDestroy` is only called via `Dispose`, call it in the owner's `OnDestroy` (KT AI.cs:91-97 does not, INFERRED leak of nothing important).
Real owner pattern (KT Logic/AI/AI.cs:55-60, 179-198; states in Logic/AI/State/AI_State_*.cs, enum in AI_State.cs):
```csharp
StateMachine<AI_State> _sm;
void InitStateMachine() {
    _sm = new StateMachine<AI_State>();
    _sm.AddState(AI_State.Idle, new AI_State_Idle(this)); // class AI_State_Idle : IStateMachine, ctor(owner)
    _sm.AddState(AI_State.Stop);
    _sm.CurrentState = AI_State.Stop;
}
void Update() => _sm?.Update();
public AI_State State { get => _sm.CurrentState; set => _sm.CurrentState = value; }
```
Why: INFERRED. replaces boolean flag soup; states are plain classes that get the owner via constructor.

## 7. MonoCached family

| Class | What | Tag |
|---|---|---|
| `MonoCached` | cached `TransformCached`, `RectTransformCached`, `GameObjectCached` (lazy `!_x` Unity-null check). SE adds public virtual `Tick/LateTick/FixedTick` (no dispatcher) | VERIFIED SE MonoCached.cs:5-57 |
| `MonoCachedFast : MonoCached` | `GetCached<T>(includeInactive, retryIfMissing)`: per-instance `Dictionary<Type,Component>` + `_missingCache`; looks `GetComponent` then `GetComponentInChildren`; stale (destroyed) entries are dropped and re-resolved | VERIFIED CS MonoCachedFast.cs:160-211 |
| `MonoCachedOpt` (SE) / `MonoBaseOpt` (CS) | resolve-once cache of single/multiple components and INTERFACES (`GetCachedInterface<T>`, array results), no null caching | VERIFIED SE MonoCachedOpt.cs:8-80 |
| `MonoCachedHub<THub>` | `Hub` property: serialized `_hub` field, lazily `GetComponentInChildren` then `GetComponentInParent`; `OnValidate` fills it in editor. Used for child components of a root (`AI_Renderer : MonoCachedHub<AI>`, `Character_Fx : MonoCachedHub<Character_Renderer>`, `IAP_NoAds_Popup : MonoCachedHub<Popup>`) | VERIFIED CS MonoCachedHub.cs:216-241; KT usages |
| CS `MonoBase` | MonoCached + Tick dispatch through `MonoCallback` events, registered in `Start`, unregistered in `OnDisable` (CS MonoBase.cs:60-110) | VERIFIED |
Why: avoid repeated `GetComponent`/`.transform` marshalling on hot paths (INFERRED; the "Cached" naming and the Opt docs "No repeated GetComponent" are stated at CS MonoBaseOpt.cs doc comment).
Mistakes: `MonoCachedHub` subclass overriding `OnValidate` without `base.OnValidate()` (field not filled; method is `protected virtual` only under `UNITY_EDITOR`, CS :234-240 - an override outside `#if UNITY_EDITOR` will not compile in builds); `Hub` null when the hub is a sibling (searches children first, then parents only); `GetCached` on a hierarchy that changes at runtime keeps stale entries only until destroyed; Tick hooks in SE do nothing unless something calls them; TickCS requires `base.Awake/Start/OnDisable` calls in subclasses (they are `protected virtual`, CS MonoBase.cs:60-90).
KT uses a SECOND parallel `Game.MonoCached` (see section 1) in many scripts: check which `MonoCached` a file's `using` resolves to.

## 8. Boot sequence

### 8.1 Knife Tower / Monkey Escape (CodeSketch + BounceSdk) - VERIFIED

Build settings scene 0 = `Assets/BounceSdk/BounceSdk/Scene/Splash.unity`, scene 1 = `Assets/_Game/Scenes/Home.unity`, then minigame scenes (KT/ME `ProjectSettings/EditorBuildSettings.asset:9-36`). VERIFIED.
Order:
1. Unity engine init; `RuntimeInitializeOnLoadMethod` hooks by stage: `BeforeSplashScreen` (KT IAPCatalog.cs:24), `SubsystemRegistration` (static resets: Character_Static.cs:19, CameraFarDistanceZone.cs:29, AdsBreak_Static.cs:20), `BeforeSceneLoad` (AdsBreak_Static.cs:28), then scene 0 loads.
2. Splash scene (3rd-party BounceSdk; "Splash shows loading ~5 s") calls partial class hook `SplashScene.DevInitConfig()` -> `DataBlockPreloader.PreloadAll()` (KT BounceDev/SplashScene.Dev.cs:11-14): reflection-scans the `Game` assembly (`Assembly.GetExecutingAssembly()` - only the assembly containing the preloader), finds every `DataBlock<>` subclass, reads its static `Instance` property, loading all saves behind the splash. Per-type try/catch. Comment: "just inheriting DataBlock<T> gets auto-preloaded" (stated, Vietnamese, DataBlockPreloader.cs:9-10). ME has no `PreloadAll` call (grep found none), so ME loads blocks lazily on first access (VERIFIED absence).
3. `SplashScene.InitSplashCompleteAndChangeToNextScene()` -> `LoadSceneAsync(1)` = Home (:17-21).
4. After Home scene objects awake: `GameMasterInit.RuntimeInit` ([RuntimeInitializeOnLoadMethod AfterSceneLoad], KT GameMasterInit.cs:10-30). NOTE this fires after the FIRST scene load (the Splash scene), not after Home (INFERRED from Unity semantics: AfterSceneLoad runs once after the first scene's Awake/OnEnable). It sets frame rate/vsync on mobile, `DevicePolicy.ApplyRenderPolicy/PhysicsPolicy`, `InitSettings` (copies `DataSettings` volumes into `AudioManager.VolumnMusic/VolumeSound`, subscribes `OnValueChanged` to push later changes, sets `Taptic.tapticOn`), `InitSRDebug`, `EnsureInitialBoostReward` (touches `Data_Shop`, forcing its load).
5. Singletons are lazy: factories load at first static access; `MonoCallback` is created by the first DataBlock `Init` (`SafeInstance`); `AudioManager.SafeInstance` creates itself with its pool; `ViewContainer`/`PopupManager` root come from the scene canvases.
6. Gameplay scenes: `Minigame_GUI_Loader` pushes the GUI view via `CodeSketchViewHelper.PushAsync(AssetReference)` (KT Logic/Minigame/Minigame_GUI_Loader.cs:39); `ViewContainer` closes all views on `activeSceneChanged` (SE ViewContainer.cs:36-41).

Key consequences (INFERRED unless stated): DataBlock load time is paid under the splash; anything touching a DataBlock in a `BeforeSplashScreen`/`SubsystemRegistration` hook loads it before the splash; there is no single "Bootstrap" scene or MonoBehaviour: init is spread over static hooks plus lazy singletons.

### 8.2 SketchEngine project (break-and-steal) - VERIFIED where cited
- `DataBlockWarmup.WarmupAll` runs automatically at `BeforeSceneLoad` (SE DataBlockWarmup.cs:200-209): generated registry (build-time `DataBlockRegistryBuilder`, SE `Editor/Data/`) else assembly reflection scan; each block's `Warmup()` loads + `Init()`s + serializes once to prime serializer metadata. Result: the project no longer needs a hand-written preloader (BounceDev `DevInitConfig` is empty there, VERIFIED SplashScene.Dev.cs:10-13). Disable with `DataWarmupConfig.Enabled=false` set in a `SubsystemRegistration` hook.
- Project statics: `Game_Settings.cs:11,18` uses `SubsystemRegistration` + `BeforeSceneLoad`; `Factory_Egg.cs:67`, `AdsBreak_Static.cs:22,32` same pattern. Content not read in detail (INFERRED purpose: reset statics / apply settings).
- Note the same Splash -> scene 1 flow (BounceSdk) is present (VERIFIED file exists).

## 9. Popups and Views

Two UI systems, VERIFIED SE:
- **Popup**: prefab with `Popup` component (`[RequireComponent(CanvasGroup)]`). `PopupManager.Create(prefab[, root])` instantiates inactive (`prefab.Create(root,false)`), finds `Popup`, `SetAsLastSibling` (SE PopupManager.cs:125-148). Opening = enabling: `OnEnable` pushes the popup on the static stack (hides input on previous top via `SetEnabled(false)`), runs the open sequence, plays `_sfxOpen` through `AudioManager.Play` (SE Popup.cs:251-270). Close(): reverse the DOTween sequence at speed `open/closeDuration`; `Sequence_OnRewind` destroys the GameObject; `Esc/Back` key triggers `Close` on the top enabled popup (`InputCheck`, Popup.cs:395-401). `PopupRootSetter` on a canvas child marks the popup parent canvas (highest sorting order wins); fallback is highest overlay canvas. Animations are `[SerializeReference] PopupAnimation[]` (Fade/Scale/Background).
- **View/ViewContainer**: persistent `MonoSingleton`, stack of full-screen `View`s loaded from Addressables `AssetReference`, `_isTransiting` gate, previous top gets `Block()`, on close `Reveal()` (SE ViewContainer.cs:14-120). Used for the HUD-per-minigame (`Minigame_GUI_Loader`, `FNAF_Tower_Master.cs:96`).
Why two systems: INFERRED. Popups are small overlays (shops, rewards) from Resources/prefab refs held by factories; Views are scene-scoped screens loaded via Addressables.
Mistakes: calling `popup.gameObject.SetActive(false)` instead of `Close()` (stack pop happens in `OnDisable`, but no close animation/`onCloseEnd` ordering, `RaiseCloseEnd` guards double fire); instantiating popups when no overlay canvas exists (`Root` null -> `Create` at null parent); keeping popup prefab references in scene components and in factories (double load); `PushAsync` while another transition is running returns null (SE ViewContainer.cs:70-74) - always null-check the result (KT `EasyObby_Master.cs:50` awaits it).

## 10. Audio, settings, async helpers

- **AudioManager** (`MonoSingleton`, persistent): `Play(AudioConfig[, position], loop)` pulls an `AudioScript` from a `UnityEngine.Pool.ObjectPool`, returns null if config/clip null; static `DataValue<float> VolumnMusic/VolumeSound` (typo "Volumn" is in the API; keep) (SE AudioManager.cs:9-50). `AudioConfig` is a ScriptableObject (clip, type, volume); `AudioMixerFactory` and `AudioButtonSfx` exist. Feature audio is resolved through project `Factory_Audio` (KT/ME/SE assets `Game.Factory_Audio.asset`, VERIFIED). Volume binding to saved settings is done manually in the project's boot code (KT GameMasterInit.cs:40-58), NOT by the framework (VERIFIED).
- **Settings**: `DataSettings : DataBlock` with `SoundVolume`, `MusicVolume`, `Vibration` `DataValue`s (SE DataSettings.cs:13-15) and `SettingMusic/Sound/VibrationButton` UI components (framework). The button components drive the values; the game must connect them to AudioManager/Taptic at boot (see 8.1 step 4). VERIFIED wiring is project-side.
- **CancelToken**: tiny wrapper over `CancellationTokenSource`: `Token` lazily creates the source; `Cancel()` cancels, disposes, nulls so the next `Token` is fresh (SE Core/Async/CancelToken.cs:5-26). Real use: KT AI.cs:93 `_cancelDeath?.Cancel()` in `OnDestroy`. Pattern: cancel the previous before starting a new async operation, pass `.Token` to UniTask calls, cancel in `OnDisable/OnDestroy`. Mistake: caching `Token` across a `Cancel()` (stale canceled token).
- **UniTask**: required by ViewContainer/ViewHelper (`UniTask<View>`), project code uses `await ... PushAsync`. Other async: `CoroutineGlobal/CoroutineUtility`, `MainThreadDispatcher`. Why UniTask: INFERRED (allocation-free awaits on mobile).
- **Other framework pieces for orientation (not detailed)**: Pool (`PoolPrefab*`, `Pooler`, `PoolReleaseScheduler`), `OptCanvasLayout`, `OptScriptLookup`, `OptCollision*` (see cluster on collision), `Timer`, `AnimationSequence`, WorldCanvas, Notification, Internet reachability popup, Debug toggles (`DebugButtonClearData`, ads-skip toggles backed by `DataMaster`, SE DataMaster.cs:5-26).

## 11. Initialization-order rules that follow (INFERRED from the above)
1. `ScriptableObjectSingleton.Instance` is safe from anywhere after Resources are available, including `BeforeSceneLoad` hooks (it uses Resources.Load only); it is NOT safe from a static constructor/field initializer that runs before `Resources` can load (rare).
2. A factory `OnInitialize` must not call into a DataBlock that in turn reads the same factory during its `Init` (A->B->A ordering) - re-entry returns the already-assigned instance but its caches may be half-built.
3. `DataBlock.Init` creates `MonoCallback` via `SafeInstance` (creates a GameObject): do not touch blocks inside `OnApplicationQuit`/`OnDestroy` paths where `MonoCallback.IsDestroyed`.
4. Static event subscriptions made in `RuntimeInitializeOnLoadMethod` run once per process; with domain reload disabled they accumulate across Play sessions unless reset at `SubsystemRegistration`.
5. UI subscriptions to `DataValue.OnValueChanged` must be removed (event lives on the block, which lives forever).

## 12. Proposed classification

| Item | Class | Proposed name | Skill/recipe must contain | Tag |
|---|---|---|---|---|
| Framework identity + version delta table, migration CS->SE | SKILL | `framework-version-map` | 1) detect framework from `manifest.json` (`com.codesketch` vs `com.sketchengine`); 2) the delta table of section 1; 3) mechanical migration checklist; 4) "never invent API from the other version" guard; 5) deps required (Odin, PrimeTween, DOTween, UniTask, Addressables); 6) how to open the package source under `Library/PackageCache` to confirm | VERIFIED |
| `INSTANCE` vs `Instance`, accessor naming per version | RULE | (in `framework-version-map`) | DataBlock accessor name per version | VERIFIED |
| DataBlock authoring (new persistent domain) | RECIPE/TEMPLATE | `data-block-template` | `Data_X : DataBlock<Data_X>`; `base.Init()` + `??=` for every field; static `DataValue` accessors; keyed dict `TryAdd`; list of "never store" (scene refs); field-rename warning; note SE autosave only triggers via `DataValue.Value`, not collection mutation | VERIFIED |
| DataBlock save/load internals and gotchas | DATA | `data-persistence-facts` | save triggers (pause/quit; SE +2 s debounce), file path root, key = full type name, atomic write/.bak, load failure = fresh block, Odin `SKO1` header, legacy BinaryFormatter fallback | VERIFIED |
| Preload / warmup of data blocks | SKILL | `boot-sequence-setup` | CS: add `DataBlockPreloader` template and call from `SplashScene.DevInitConfig`; SE: automatic `DataBlockWarmup`, `DataWarmupConfig`; boot-order diagram of 8.1/8.2; where to put one-time init (`AfterSceneLoad` hook like `GameMasterInit`); settings->audio/taptic binding; static-reset hooks at `SubsystemRegistration` | VERIFIED |
| ScriptableObjectSingleton factory authoring | RECIPE/TEMPLATE | `factory-singleton-template` | class self-generic rule; asset name = full type name (`Game.Factory_X.asset`) in `Resources/<CodeSketch|SketchEngine>/ScriptableObjectSingletons/`; editor auto-creates an EMPTY asset in `Assets/Resources/...` (move it, wire fields via MCP, never hand-write YAML); `OnInitialize` for dictionary build with duplicate-id validation; read-only static accessors; build fails with null if asset missing | VERIFIED |
| Singleton asset must exist in builds | RULE | (`done-means-wired`) | "after adding a factory, verify the asset exists under Resources and has serialized fields assigned" | VERIFIED (build null); policy INFERRED |
| MonoSingleton usage | RECIPE | `mono-singleton-template` | `PersistAcrossScenes`, `base.Awake/OnDestroy`, `Instance` vs `SafeInstance` vs `HasInstance`, `IsDestroyed` quit guard, when to prefer a static class/SO instead | VERIFIED |
| StaticBus events | RECIPE + RULE | `static-bus-events` | event class template (`IEvent`, ctor payload, private set); Subscribe/Unsubscribe symmetry in matching lifecycle (RULE: reference code sometimes leaks, KT AI.cs); handler naming `StaticBus_Event_X`; no bus for single-owner communication; reset statics concern | VERIFIED |
| StateMachine | RECIPE | `state-machine-template` | enum + `IStateMachine` state class ctor(owner); owner registers states, sets initial state explicitly (getter NRE), forwards `Update/FixedUpdate`, single transition property, `Dispose` in `OnDestroy`; `PreviousState` is not reliable; unregistered label throws | VERIFIED |
| MonoCached family selection | RULE | `mono-cached-selection` (or in `framework-version-map`) | MonoCached vs Fast vs Opt vs Hub decision; `Hub` lookup order; `OnValidate` override needs `#if UNITY_EDITOR`; beware project-local shadow `Game.MonoCached`; SE Tick has no dispatcher | VERIFIED / INFERRED |
| Popup / View | SKILL | `popup-view-system` | popup prefab requirements (`Popup`, CanvasGroup, `PopupRootSetter`), `PopupManager.Create`, close via `Close()`, Esc handling, animations; View via Addressables `PushAsync` + null check; when popup vs view; sfx via `AudioConfig` | VERIFIED |
| Audio + settings wiring | SKILL | `audio-settings-wiring` | `AudioConfig` assets, `AudioManager.Play`, `VolumnMusic/VolumeSound` typo, project boot binding to `DataSettings`, Taptic flag, factory-routed audio (links to existing `game-audio-system`) | VERIFIED |
| CancelToken / UniTask async ownership | RULE + RECIPE | `async-cancellation` | `CancelToken` semantics (Cancel disposes and nulls), cancel previous before restart, pass `.Token`, cancel in teardown, no `Task.Run` for Unity API | VERIFIED token; policy INFERRED |
| Collision register delta (non-generic in SE) | RULE | (in `framework-version-map`, details in collision cluster) | check generic vs non-generic register before writing code | VERIFIED |
| Quick framework API lookup (type -> file:line, per version) | TOOL | `framework-api-grep` | script that resolves package dir from `Packages/manifest.json` + `Library/PackageCache`, lists public types and greps a symbol in both CS and SE | INFERRED (proposal) |
| Project data-type survey (list `Data_*`, `Factory_*`, singleton assets, boot hooks) | TOOL | `framework-inventory` | script listing `DataBlock<` subclasses, `ScriptableObjectSingleton<` subclasses vs existing assets in `Resources/**/ScriptableObjectSingletons`, `RuntimeInitializeOnLoadMethod` hooks and their stages; flag missing asset files and unbalanced `StaticBus.Subscribe/Unsubscribe` | INFERRED (proposal) |

Open questions (not verified): exact CS persistence root folder name (read only SE's constant); whether KT/ME `MonoBase` Tick dispatch is used by game code; whether `AfterSceneLoad` in `GameMasterInit` really runs before Home (Unity semantics, not tested in Editor); no code was compiled or run for this catalog.
