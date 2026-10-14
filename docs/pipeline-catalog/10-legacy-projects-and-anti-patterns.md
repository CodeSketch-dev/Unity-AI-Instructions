# 10 - Legacy projects (CFramework era): what to keep, what is a warning

Scope: read-only reverse-engineering of `bike-obby` and `climb-and-jump-tower` (both Unity 2022.3.62f3, CFramework, landscape, Android), plus an inventory of every other project under `C:\Unity\GitProject`. Purpose: feed skills/rules for the AI game-production pipeline.

Legend: **[V]** verified by reading the cited file/grep; **[I]** inferred. Paths: `OBBY` = `bike-obby/obby-unity/Assets`, `CLIMB` = `climb-and-jump-tower/climb-tower-unity/Assets`, `KT` = `knife-tower/knife-tower-troll-unity`.

## 1. Project inventory (all of C:\Unity\GitProject)

| Project | Unity | Framework | Genre / what it is | Size (own `_Game` .cs) | Use as reference for |
|---|---|---|---|---|---|
| bike-obby/obby-unity | 2022.3.62f3 [V ProjectVersion] | CFramework (in-project, `Assets/CFramework`, 182 .cs) | "Bike Parkour: Obby Game" - bike/bicycle obby, 8 scenes (ParkourNormal, ParkourRace, Dropper, FloorIsLava, RaceMaster, ParkourNoel, ParkourHalloween, Home) | 331 .cs / 21.2k lines [V] | bike physics, race+AI, stage constructor, season clones; NOT code style |
| climb-and-jump-tower/climb-tower-unity | 2022.3.62f3 [V] | CFramework (same fork, newer) + Animancer, A*, SoftMask, RaycastPro, Digger, Lean.Pool, PrimeTween+DOTween | "Dig To Earth's Core" (productName) hub with 6 modes: ClimbTowerJump, BubbleGumSimulator, FlyToSpace, BombToGround, DigToEarth, BuildingAHouse | 734 .cs / ~50k lines in `_Game*` dirs [V] | multi-mode hub, pet gacha, world selection, config volume; NOT code style |
| knife-tower/knife-tower-troll-unity | Unity 6 (6000.x) [I from newer set] | CodeSketch (`com.codesketch`) + PrimeTween | "Keyboard Escape - Speed Parkour" [V productName] | 713 .cs, 18 scenes [V] | PRIMARY reference |
| monkey-escape/monkey-escape-unity | 6000.x [I] | CodeSketch + PrimeTween | "Monkey Obby - Master Escape" [V] | 417 .cs, 9 scenes [V] | PRIMARY reference |
| ride-a-pet | 6000.3.22f1 [V] | CodeSketch (csproj list: AdsLoading, Audio, Data, Popup, StatSystem, TextDamageSystem...) + PrimeTween | "Ride A Pet" [V]; has `MIGRATION_ENGINE.md` | 262 .cs, 5 scenes [V] | pet riding, stat system, migration notes (project root is Unity root, no sub-folder) |
| thunder-break-egg/break-and-steal-unity | 6000.3.22f1 [V] | SketchEngine (+CodeSketch in manifest) + PrimeTween; has AGENTS.md + `docs/` (clone-plan, feedback-notes, balance, agent-handoff) | "Break An Egg - Steal & Run" [V] | 342 .cs, 2 scenes [V] | NEWEST pipeline-driven project: docs layout, SketchEngine usage, egg/steal/pet/shop features |
| Tiny Relax World/tiny-relaxing-world-unity | 6000.3.22f1 [V] | CodeSketch + PrimeTween | tiny farm / relax world (2D tiles, crops, houses, day time) [V folder names: TinyFarm, Crop, Tile, Time_Game.cs] | 104 .cs, 2 scenes [V] | 2D tile/farm, FourDirectionSpriteAnimation |
| problox (project root = Unity root) | 6000.3.22f1 [V] | SketchEngine csproj list + LitMotion + DOTS (Unity.Entities, ProjectDawn.Navigation, KCC, A*, Odin) | "Robox": multi-game container: 2_Game_Parkour (9 sub-worlds: Easy/Grow/Lava/Noel/Race/Horror/NoJump/Spiral), 3_SlapTower (Steal a Pet), 4_Game_HungryWorm | scripts live outside `_Game` (0 found there) | multi-game container; ECS navigation; not deep-read |
| steal-an-egg | 6000.0.78f1 [V] | no CodeSketch/CFramework csproj; Spine, Odin, MCPForUnity, Bounce SDK, MaxSdk | "Steal Eggs: Monster Escape" [V]; code in `_ROOT`, `vanhuy_probloxengine` | 0 under `_Game` | Spine animation, MCP-driven; not deep-read |

Takeaways [I]: framework lineage is CFramework (2022.3, 2023-24) -> CodeSketch (Unity 6, early 2025+) -> SketchEngine (newest, thunder-break-egg/problox). Only the last four-five are valid style references. Both legacy projects share the Bounce SDK (ads/analytics/remote config wrapper; `CLIMB/BounceSdk`, `CLIMB/CFramework/BounceSdk`) [V dirs].

## 2. CFramework: what it provides [V: `OBBY/CFramework`, ~182 .cs, namespace `CFramework`]

| Area | Types (file under `CFramework/Runtime`) | Behaviour |
|---|---|---|
| Persistence | `Data/CDataBlock<T>`, `Data/CDataHelper`, `Core/CValue<T>` | Lazy static `instance`: load `persistentDataPath/CFramework/<TypeName>` via OdinSerializer **binary**, else `Activator.CreateInstance`; `Init()` hooks `MonoCallback` pause/quit to auto-Save; `CValue<T>` has `value`, `eventValueBeforeChange`, `eventValueChanged` (fires only when changed) |
| Events | `Patterns/EventBus/StaticBus<T>`, `EventBus`, `IEvent`, README | Static `Action<T>` per event type: `Subscribe/Unsubscribe/Post`. README warns against publisher+subscriber classes and event chains |
| Singletons | `Patterns/Singleton/Singleton<T>`, `Mono/MonoSingleton<T>`, `MonoUISingleton<T>` | plain-class singleton; MonoBehaviour singleton (finds/creates, DontDestroyOnLoad) |
| Cached mono | `Mono/MonoCached`, `MonoCachedAll`, `MonoUICached`, `MonoCallback` | lazy `transformCached`, `gameObjectCached`; MonoCallback relays pause/quit/update |
| State machine | `Patterns/StateMachine/StateMachine<T>`, `IStateMachine` | delegate-style label FSM (add state with delegates, set `CurrentState`) - NOT the class-per-state API of CodeSketch |
| Pooling | `Patterns/Pool/PoolPrefab`, `PoolPrefabConfig`, `PoolPrefabGlobal`, `PoolPrefabItem` | wraps `UnityEngine.Pool.ObjectPool<GameObject>`; SetActive on get/release |
| Config singletons | `ScriptableObject/` + `Game/Scripts/Factory/FactoryAudio` | `ScriptableObjectSingleton<T>` with static `instance` (lowercase) - used as `FactoryXxx` [V `OBBY/_Game/Scripts/Factory/FactoryConfig.cs`] |
| UI | `View/View`, `ViewContainer`, `ViewHelper.PushAsync(AssetReference)`, `View/Transition/*` (CanvasGroup, Move, Scale, Rotate); `Utilities/Popup/Popup`, `PopupManager.Create(prefab)` + stack (`PushToStack/PopFromStack`), `Popup/Animation/*`; `Utilities/UI/Button/*` (OpenPopup/OpenView/LoadScene/ReloadScene/OpenURL/SpawnObject), `UI/Layout`, `UI/ScrollView` | Addressable-driven views, popup stack hides top |
| Audio | `Utilities/AudioManager/AudioManager`, `AudioConfig`, `AudioScript`, `AudioType` | static `Play(AudioConfig, loop)`, pooled `AudioScript`, `CValue<float>` volumes for music/sound |
| Game settings | `Game/Module/Setting/*` (`DataSettings`, Music/Sound/Vibration buttons) | persisted toggles |
| Utilities | `Utilities/HCollect/*` (fly-to-HUD currency collect w/ steps), `AnimationSequence/*` (14 step types), `Text/Animation/*`, `Camera/Orthographic|Perspective` fit, `World/Canvas`, `Random/*`, `Paint`, `Vfx`, `Scene` | |
| Modules | `Module/HealthBar`, `WorldText/TextDamage`, `TextFloatingWorld` | world-space text pop |
| Async | `Async/MainThreadDispatcher`, `Async/Coroutine` | UniTask is a separate package (`com.cysharp.unitask`) [V manifest] |
| Diagnostics/Editor | `Diagnostics/CDebug`, `Editor/*` (data viewer, SO tools) | `CLIMB/Editor/DataViewerTool.cs` (761 lines) views saved data |

Not in CFramework (vs CodeSketch) [V by absence in `CFramework/Runtime`]: `MonoCachedFast/Hub`, `CancelToken`, `OptCollision*` registry, Haptic module, `DataBlockPreloader/Warmup`, class-based state machine, CullingGroup/mesh combiner helpers.

### Mapping table CFramework -> CodeSketch -> SketchEngine

CodeSketch refs: `KT/Library/PackageCache/com.codesketch@0fe9d8bab8cb/Runtime`; SketchEngine refs: `thunder-break-egg/.../com.sketchengine@522ef3079890/Runtime` [V file listings].

| Concept | CFramework (legacy) | CodeSketch | SketchEngine | Porting note |
|---|---|---|---|---|
| Namespace | `CFramework` | `CodeSketch.Data`, `CodeSketch.Patterns.Observer`, ... (split asmdefs) | `SketchEngine.Data`, `SketchEngine.SO`, ... | never mass-replace; inspect asmdefs |
| Data block | `CDataBlock<T>.instance` (lowercase) | `DataBlock<T>` + `DataFileHandler`/`DataSerializer` (Odin binary) [V `Runtime/Data/`] | `DataBlock<T>` + `DataBlockWarmup` / `DataBlockRegistryBuilder` editor [V] | casing `instance`->`Instance`, `value`->`Value` |
| Observable value | `CValue<T>` (`value`, `eventValueChanged`) | `DataValue<T>` | `DataValue<T>` with `Value`, `OnValueChanged` [V `Core/Data/DataValue.cs`] | rename members |
| Event bus | `StaticBus<T>` Subscribe/Unsubscribe/Post | same API | same (`Core/Patterns/EventBus/StaticBus.cs`) | 1:1, lifetimes must be paired |
| MonoBehaviour cache | `MonoCached` (lazy `transformCached`) | `MonoCached`, `MonoCachedFast`, `MonoCachedHub<T>`, `MonoCachedOpt` | same four | `transformCached` -> base members; prefer Hub for root-child |
| Mono singleton | `MonoSingleton<T>` (find/create) | prefer `ScriptableObjectSingleton` factories + explicit scene owners | same | do not copy MonoSingleton spam (see 4.2) |
| SO singleton / factory | `ScriptableObjectSingleton<T>.instance`, `Resources/ScriptableObjectSingletons` [V `CLIMB/_Game/Resources/ScriptableObjectSingletons`] | `ScriptableObjectSingleton<T>`, `SerializedScriptableObjectSingleton<T>`, assets in `Resources/CodeSketch/ScriptableObjectSingletons` | `SketchEngine.SO` equivalents, `Resources/SketchEngine` [V dir] | path convention differs per framework |
| State machine | delegate FSM `StateMachine<T>` | class-based `StateMachine<TEnum>` + `IStateMachine` | same family | AI states in OBBY (`Logic/AI/State/AIState*`) are the legacy usage |
| Pool | `PoolPrefab*` on `ObjectPool<GameObject>`; CLIMB also uses `Lean.Pool` | `Pooler`, `PoolPrefab*`, `PoolReleaseScheduler`, `PoolAutoReleaseParticle`, `IPoolRelease` | same | legacy has no release scheduler |
| Popup | `PopupManager.Create(prefab)`, `Popup` | `Popup`, `PopupManager` | `Core/Popup/*` incl. `PopupAnimation{Fade,Scale,Background}` | |
| View | `View`, `ViewHelper.PushAsync(AssetReference)` | `View/*` | `Core/View/*`, `SketchEngineViewHelper` | Addressable-based push is legacy-only |
| Audio | `AudioManager`, `AudioConfig` static | `Audio/AudioManager` | `Audio/AudioManager` | |
| Haptic | none in framework (project uses NiceVibrations/Taptic) | `Haptic/*` | n/a [I] | |
| Async | UniTask + coroutines; no token wrapper | `Core/Async/CancelToken`, `AdsLoadingCancelToken` | [I] same | legacy code ignores cancellation |
| Collision dispatch | none; per-object `OnTriggerEnter` + `GetComponent` | `Optimize/Collision/{2D,3D}/OptCollision*` (generic Register) | non-generic Register | legacy `ICharacterCollidable` exists (`OBBY/_Game/Scripts/Logic/Character/ICharacterCollidable.cs`) but still routed via callbacks [I] |
| Debug | `CDebug` | `Diagnostics` | `Diagnostics` | |

## 3. Games and mechanics

### 3.1 bike-obby (`OBBY/_Game`)

Structure [V]: 8 scenes; each mode = `Manager` + `LevelConstructor` + `Level` + `GUI`; per-mode `Factory*` SOs (`FactoryPakourRace`, `FactoryDropper`, `FactoryFloorIsLava`, `FactoryParkourNoel/Halloween`, `FactoryBike`, `FactoryBooster`, `FactoryWorld`, `FactoryConfig`), 10 `Data*` blocks (`DataBike`, `DataCharacter`, `DataPlayer`, `DataPakourRace`, ...), ~35 event folders (`Event/ParkourRace` 17 files, `Event/Character` 15).

| Mode | How it works | Evidence |
|---|---|---|
| ParkourNormal / ByLevel | World SO list (`Configs/ParkourNormal/World1..8`), `Stage`s concatenated by `LevelConstructor`; checkpoints between stages; bounds/start/end offsets per stage | `Logic/Stage/Stage.cs` (start/end check-point size default 8x1x8), `ParkourByLevel_LevelConstructor`, 8 World assets [V] |
| ParkourRace | `Level1..10` configs; `_totalPlayer = 21` (player+20 bots); `_reachEndDelay 1.5`, `_findPlayerDuration 3`, `_idleFallDuration 1`, `_fallDuration 3`; optional overrides `_overrideBikeSpeed`, `_overrideJumpHeight 5`, `_bikeMaxVelocityY 10`, `_isPlayerStunnable`; cutscene `1 + 1.5 s`; bot respawn `_botRemoveAfter 3` | `Factory/FactoryPakourRace.cs`, `FactoryConfig.cs` [V]. Lobby/progress GUI = `ParkourRace_GUI_Lobby` (279 lines), `GUI/ParkourRace_GUI_Progress` (255) |
| Dropper | falling-down levels with a hole target; `_gravity -9.81`, `_bikeForceVelocity 1`, on-air rotation 40/40 deg/s; levels are `AssetReference` list | `Factory/FactoryDropper.cs` [V] |
| FloorIsLava | 6-line subclass of `ParkourManager` overriding `GetMinigame/GetWorld` | `Logic/FloorIsLava/FloorIsLava_Manager.cs` [V] - good example of thin mode |
| RaceMaster | scene + minigame asset only; logic reused [I] | `Configs/Minigame/RaceMaster.asset` |

**Bike physics** [V `Logic/Bike/Partial/BikeController.cs`, `BikeProperties.cs`]: Rigidbody velocity set in `FixedUpdate` (not forces); a KCC-style `Character` provides grounding report. Input = joystick vector -> target yaw `atan2(x,z)`; yaw rate = `Lerp(rotationSpeedLimit.x .. .y, rotationCurve(|angleDiff|/90))` capped per frame (`Time.deltaTime`, inside FixedUpdate); speed ramps `forwardSpeed/maxSpeedInSecond` (accel) and `forwardSpeed/stopInSecond` (decel); no input -> decel to 0; lean via Animator (`Leaning`), steering handle/wheel visuals. Defaults in `BikeConfig` class: forwardSpeed 3, maxSpeedInSecond 3, stopInSecond 1, moveForwardLessThan 10, tiltAngle 35, tiltSmooth 0.05, maxSteeringAngle 30, steeringSmooth 0.1, rotationSpeedLimit (50, 280), onAirRotation (40,40), groundCoyoteTime 0.15, jumpHeight 4, jumpForwardRatio 1.2, maxSlopeAngle 75, slope up/down factor 0.5. External impulses decay `ForceImpulseDecayRate 0.95`, cap `ExternalForceMax 10`, bike-vs-bike push `BikePushForce (5,10)` lerped by speed ratio (`FactoryConfig.cs`, `BikeController.cs:417`). Per-bike overrides live in prefabs/scenes (binary, not read) [I]. Camera: Cinemachine FreeLook, FOV 60 -> 70 by `SpeedRatio`, smoothDamp 0.2, respawn offset Y 2.5 (`Camera/CameraFollow.cs`).

**Platform/booster tuning** [V]: Jetpack 30 s, road expand 4 m, gas velocity 2 (`Booster/BoosterJetpackConfig.cs`); Trampoline pressedSpeed 15, jumpHeight 4, forwardRatio 1.2; SpeedBoost x1.5 for 1 s; Fan force 3, rotate 90 deg/s; Break platform: shake 20 Hz/0.05/0.5 s, fragments scale 0.95, break force 15, restore 2 s (`Platform/*`). Kill platform flags `_jumping/_revive/_deathForceRagdoll`.

Level authoring [V]: prefab-per-stage built from ProBuilder shapes + AI waypoints; editor tools `Tools/Stage Converter` (`StageConverter.cs`, 494 lines, batch prefab conversion) and `Tools/ProBuilder Shape Replacer` (357 lines), `MeshCombinerWithAtlas.cs` (298 lines, atlas+merge), SuperCombiner/MeshCombiner plugins. World content is selected by SO (`WorldConfig`, `MinigameConfig`) and seasonal variants (Noel, Halloween) are separate scenes + factories.

### 3.2 climb-and-jump-tower (`CLIMB`)

Hub: `_Game/Scenes/Home.unity` -> mode select (`MinigameSelection*`, `MinigameConfig`, `DataMinigame.Type`), per-mode scenes/modules. Configs: 178 SO assets under `_Game/Configs/Minigame/ClimbTowerJump` [V count].

| Mode | Mechanics | Tuning/evidence |
|---|---|---|
| ClimbTowerJump (CTJ) | Roblox-style character (`RobloxCharacter`, KCC `CharacterKC` 1032 lines) climbs ladders (`Ladder`, `Ladder_Pointer`), jumps off; height = reward: `CoinRewardCalculator`: `max(minimumReward 5, height * baseCoinRewardPerMeter 10)` x map multiplier, collected on landing after `rewardCollectionDelay 0.5`; `HeightTracker.heightMultiplier 4`, threshold 0.1. Worlds (`CTJ_World_Config`: ID, CostCup string like "1K", `coinMultiplier`, `climbMultiplier`, UnlockType Cup/Free) unlock by cups; wings, pets, character skins, gacha eggs, lucky wheel, daily gift/reward | `Scripts/_Truong_Scripts/Character/Movement/{CoinRewardCalculator,HeightTracker}.cs`, `Logic/Minigame/ClimbTowerJump/World/CTJ_World_Config.cs`, `Factory/Minigame/ClimbTowerJump/Factory_CTJ_Pet.cs` (`_maxPetSlotStack 60`, `_maxEquipStack 3`, `_requireCraftStack 3`, `_viewNextCount 10`) [V] |
| BubbleGumSimulator | hold-to-chew (`holdThreshold 0.5`, `chewCooldown 0.5`, `bubblesPerChew 1`), storage `maxBubbles 10`, balloon scale 0.5..4.0 (+0.05 per bubble, diminishing 2.0, anim 0.3 s); selling `coinsPerBubble 1`, `sellingDelay 0.5`; jump height from bubble count via hard-coded tables (bubbles 0->15, <=35->20, <=75->25, then keys 75/715/3015/6115 -> 25/110/170/210 with diff 40/200/300/1000); islands unlock by portal, pets/gacha, trampoline & one-way platforms | `_Game/BubbleGumSimulator/Scripts/{Chewing,Selling,Island,Pets,Platform,Portal}/*` [V]. Imported module with its own mini-framework (`FakeMG.FakeMGFramework`: Singleton, SOEventSystem channels, Audio, UI) and `PlayerDataManager` JsonUtility save [V] - parallel infra |
| FlyToSpace | code NOT in repo: only configs/art (Rocket_1.asset `_boost 1`, `_boostPercentNormal 0.05`, Characters x14, DailyGift Space_1 x12+, A_Star, BehaviorTree, Eggs, LuckyWheel, Pet), `FTS_GameManager.prefab`, `FTS_Player_GUI.prefab`, shader `FTS_TextureScroll` | `Configs/Minigame/FlyToSpace/*`, `_Art/Shader/FlyToSpace` [V]; mechanic (rocket boost climb, scrolling texture sky) INFERRED |
| BombToGround (`_Game_BombMode`) | throw bomb (`ThrownBomb`: `RequireComponent(Rigidbody)`, RaycastPro `RangeDetector`, coroutine explode after delay, LeanPool) at terrain/blocks; 9 bombs: Bomb1 power x1, throwSpeed 2.2, delay 2 s, coin x2 -> Bomb9 power x10, speed 8.5, delay 7 s, coin x14; cost strings ("1K"), `UnlockType` Free/Coin; NPC bots with `AdvancedBombBrain`, `INpcBombBrain`, cooldown system; 3 worlds | `Configs/Bombs/Bomb 1/9.asset`, `Scripts/Bomb/BombConfig.cs` (AssetReferenceGameObject prefab, `Cost`/`CoinMultiplier` as strings) [V] |
| DigToEarth (`_Game_DigMode`) | player digs terrain downward with Digger Pro (`DiggerData`, `DigController` 613 lines: digRange 10, digSize 3, opacity 1, BrushType.Sphere, sphereCastRadius 0.3, `editAsynchronously`), depth tracking (`DepthTracker` 525 lines, `DiggerDepthManager`), jetpack/fly, underground items spawner (536 lines), pickaxes (19: Wood power 1.1/speed 2/coin 8 -> P19 power 15.25/speed 3.6/coin 113B, cost "35a" idle-number notation), pets (gacha 738 lines, craft), NPC diggers, chests, lucky wheel, daily reward, 9 world scenes (`World_Digger_1..4`, `Large`, `World_Bomb_1..3`) | `Scripts/Character/Movement/DigController.cs`, `Configs/Pickaxe/*.asset` [V] |
| BuildingAHouse | only a minigame asset | `Configs/Minigame/Minigame_BuildingAHouse.asset` [V]; mechanic unknown |

Economy conventions [V]: huge numbers handled as `double` + string notation (`UtilsNumber.ParseCompactNumber("35a")`), `CTJ_Static.CoinFactor/MapCoinMultiplier` as `CValue<double>`.

## 4. Architecture and code-quality observations (label: anti-patterns seen in the wild)

Counts are grep matches over own code [V] (bike: `OBBY/_Game/Scripts`; climb: `_Game*`, `_GameModule`).

| Metric | bike-obby | climb-tower | Reference (CodeSketch rule) |
|---|---|---|---|
| `Update/LateUpdate/FixedUpdate` methods | 32 | 105 (81 files with `Update`) | avoid on populations |
| `FindObjectOfType/GameObject.Find/FindWithTag` | 0 | 78 | none in hot paths |
| `Camera.main` | 8 | 31 | cache |
| `GetComponent<` | 158 | 464 | cache / Hub |
| LINQ-ish (`Where/Select/FirstOrDefault/ToList/Any`) | 9 | 99 | none in hot paths |
| coroutines (`StartCoroutine/new WaitForSeconds`) | 19 | 99 | UniTask + cancel |
| `Debug.Log` | 75 | 1121 | gate/strip |
| `OnTriggerEnter/OnCollisionEnter` | 21 | 75 | registry dispatch |
| DOTween vs PrimeTween usage | 28 / 7 | 270 / 118 | PrimeTween |
| `#region` | 19 | 87 | avoid |

### 4.1 Anti-pattern catalogue (with file examples)

| ID | Anti-pattern | Example [V] | Fix in house style |
|---|---|---|---|
| AP-01 | God class / partial-class sprawl | `CLIMB/_Game/Scripts/Logic/Character/KinematicController (KC)/CharacterKC.cs` 1032 lines (+`partial`); `BubbleGumSimulator/.../CharacterManager.cs` 845; `OBBY/.../Bike/Partial/BikeController.cs` 538 (steering, tilt, wheel, slope, collisions, push in one) | split into focused sibling components under a hub |
| AP-02 | Static god bag | `CLIMB/_Game/Scripts/Logic/Minigame/ClimbTowerJump/CTJ_Static.cs`: static refs to player, popups, gacha, culling helpers, `Action` events, `InitializedFromSplash`; static `CValue<double>` multipliers | data in `DataBlock`, events on StaticBus, popups via manager |
| AP-03 | Singleton overuse | `OBBY`: `MonoSingleton` x10+ (`CameraFollow`, `CameraManager`, `CameraPivot`, `GameSingleton`, `ParkourRace_Manager`, `ParkourManager`, `AIWaypointManager`...); `CLIMB`: `CTJ_GameManager : MonoSingleton`, `FakeMG Singleton<T>` | explicit scene owner / factory SO |
| AP-04 | Find in init paths of managers | `CLIMB/_Game_DigMode/Scripts/Character/Management/DiggerDepthManager.cs` 14 hits (`FindObjectOfType<DepthDisplayUI>`, `DigProgressBar`, `FlyButton`...); `BothDiggerInputProvider.cs:33-57`; `DigController.cs:87`; `_Game/Scripts/Logic/Game/ClimbRewardManager.cs` `FindWithTag("Player")` + runtime `AddComponent<HeightTracker>()` | serialized refs / events [I: most are in Start paths, not per-frame] |
| AP-05 | Per-frame work with no throttle | `DepthTracker.cs:151` `Update() => UpdateDepth(transform.position)`; `CTJ_GameManager.cs` `LateUpdate` polls `DataLuckyWheel.IsReadyToGiveSpin()` every frame; `OBBY BikeController.FixedUpdate` uses `Time.deltaTime` inside FixedUpdate | event-driven / timers |
| AP-06 | Copy-paste mode bugs | `CTJ_GameManager.Awake` sets `DataMinigame.Type.value = MinigameType.BombToGround` (CTJ mode mislabelled); `OBBY FactoryParkourNoel.cs` vs `FactoryParkourHalloween.cs` identical 16-line copies | one generic world factory |
| AP-07 | Parallel infrastructure | BGS module ships `FakeMG` singleton/event-channel/audio/UI + JsonUtility saves (`PlayerDataManager.cs` 613 lines, `JsonUtility.ToJson` at :482) beside CFramework `CDataBlock` | reuse installed data/event frameworks |
| AP-08 | Mixed namespaces / styles | `CLIMB`: `Game`, `ClimbAndJump.*`, `DiggerMode`, `BombMode.*`, `Game.BubbleGumSimulator.*`, `FakeMG.*`; folder `_Truong_Scripts` (author name), `__Utils`; both DOTween (270) and PrimeTween (118); both `Lean.Pool` and `PoolPrefab` | single namespace, one tween lib |
| AP-09 | Logging noise | 1121 `Debug.Log` in climb; emoji logs in `CTJ_GameManager` (`catch (OperationCanceledException)` logs warning); `DigMode_GroundBottom_Trigger.cs` 29 logs | `CDebug`/gated logs |
| AP-10 | Hard-coded tuning tables | `JumpHeightCalculator.cs` lists `{75,715,3015,6115}`, `{40,200,300,1000}`, `{25,110,170,210}` + const 15/20/25 | SO curve/config asset |
| AP-11 | String-number economy fields | `BombConfig.CoinMultiplier = "1K"`, `Pickaxe.Cost = "35a"`, `CTJ_World_Config.CostCup` string parsed at runtime | typed `double`/BigNumber + formatter |
| AP-12 | Comments/identifiers in Vietnamese + vendor mix | `BikeProperties.cs` (`// Góc nghiêng tối đa khi cua`), `ParkourRace` etc. | English comments (house rule) |
| AP-13 | Per-object collision callbacks + GetComponent | `OBBY BikeController.cs:417` `collision.gameObject.GetComponent<BikeController>()`; 21 / 75 trigger callbacks | `OptCollisionRegister` dispatch |
| AP-14 | Runtime AddComponent for authored deps | `ClimbRewardManager.SetupPlayerComponents` | author on prefab |
| AP-15 | Scenes serialized as binary | `OBBY/_Game/Scenes/*.unity` start with non-YAML bytes, `ProjectSettings` binary (grep cannot read) | force text serialization (diffable, MCP-readable) |
| AP-16 | `partial` class split as modularity | `Bike/Partial/{BikeController,BikeImplementFunc,BikeProperties}.cs` | components |
| AP-17 | Config SO with project-global asmless code | no asmdefs under `_Game` [I: only third-party asmdefs seen] | asmdefs per layer |
| AP-18 | Swallowed exceptions | `CTJ_Static.SetLockPlayer` `catch { // }` | log + fix cause |

### 4.2 Positive observations worth copying (cite files)

| ID | Idea | File [V] |
|---|---|---|
| G-01 | Thin mode subclass: `FloorIsLava_Manager` = 6 lines over `ParkourManager` (abstract `GetMinigame/GetWorld`) | `OBBY/_Game/Scripts/Logic/FloorIsLava/FloorIsLava_Manager.cs` |
| G-02 | Mode registry: `MinigameConfig` SO + `FactoryConfig.GetMinigame(MinigameType)` | `OBBY/.../Minigame/MinigameConfig.cs`, `Factory/FactoryConfig.cs` |
| G-03 | `Data*` as typed dictionary records, `BikeConfig.Unlock()` -> posts `EventBikeSkinUpdate` through StaticBus | `OBBY/.../Bike/BikeConfig.cs`, `Data/DataBike.cs` |
| G-04 | Event files one-class-per-file, feature folders (`Event/ParkourRace` 17 files) | `OBBY/_Game/Scripts/Event/*` |
| G-05 | Bike tuning fully data-driven (`[Serializable] BikeConfig` + `AnimationCurve` for rotation, speed-on-rotation, slope, air rotation) | `Bike/Partial/BikeProperties.cs` |
| G-06 | Coyote time + speed-ratio-driven FOV + speed-scaled push force | `BikeProperties.cs`, `CameraFollow.cs:97`, `BikeController.cs:417` |
| G-07 | Level constructor pattern: `LevelConstructor` assembles stage prefabs from SO list; `Stage` stores bounds/start/end/waypoints, editor `StageConverter` | `Logic/Stage/Stage.cs`, `StageConverter.cs` |
| G-08 | Race AI: 20 bots by state classes (`AIStateChasePlayer/WalkAround/JumpToPoint/MoveToPoint/ChaseOtherUntilFall`) over waypoints, bots removed after 3 s | `Logic/AI/State/*`, `FactoryConfig._botRemoveAfter` |
| G-09 | Gacha/pet pipeline split Data/Factory/Config/Popup (`CTJ_Gacha`, `PetCraftingSystem`, `PetGachaSystem`) | `CLIMB/_Game/Scripts/Logic/Minigame/ClimbTowerJump/Gacha`, `_Game_DigMode/Scripts/Pet/*` |
| G-10 | World selection as SO list + popup + teleport event (`Factory_CTJ_World.Switch()`, `Event_CTJ_Teleport`, `CTJ_World_Selection`) reused for DigMode (`DigMode_World_*`) | `CLIMB/_Game/Scripts/Factory/Factory_CTJ_World.cs` |
| G-11 | Underground-item and NPC spawner pattern with config SOs | `_Game_DigMode/Scripts/UndergroundItems`, `NPC/NPCSpawner` |
| G-12 | Async view load with cancellation guard (`_isLoadingView`, `try/catch OperationCanceledException/finally`) and `UniTask.DelayFrame(5)` before push | `CTJ_GameManager.LoadViewGameplay` (pattern good, logging poor) |
| G-13 | Pair subscribe/unsubscribe in Awake/OnDestroy for StaticBus | `CTJ_GameManager.cs` (5 events symmetrical) |
| G-14 | Mouse-free mobile look control: `UIPointerDrag` delta / `Screen.dpi` for DPI-independent sensitivity | `CTJ_PlayerControl.cs` |
| G-15 | Idle-number economy notation + prestige-style multipliers per world (`coinMultiplier`, `climbMultiplier`) | `CTJ_World_Config.cs` |
| G-16 | Fly-to-HUD currency collect (HCollect with Step classes) | `OBBY/CFramework/Runtime/Utilities/HCollect/*` (CodeSketch equivalent: currency spread FX) |
| G-17 | Debug cheat classes per currency (`DebugCurrencyCoin/Cup/Gem`, `DebugAddRocket`) | `CLIMB/_Game/Scripts/Logic/Debug/*` |
| G-18 | Platform kit: Break (shake->fragments->restore), Fan, Move, Trampoline, SpeedBoost, Kill, Swing as small config-struct components | `OBBY/.../Logic/Platform/*` |
| G-19 | `SafeArea` object in HUD prefab (`Player_GUI.prefab`: SafeArea > Root > Action_Jump/Action_Jetpack/Look) | `CLIMB/_Game/Prefabs/Player/Player_GUI.prefab` |
| G-20 | Editor tools for batch import settings (`AutoAdjustFBXImportSettingsWindow`, `AutoAdjustTextureMaxSizeWindow`, `DataViewerTool`) | `CLIMB/_Game/Scripts/__Utils`, `CLIMB/Editor/DataViewerTool.cs` |

## 5. UI content and layout approach

Scenes: OBBY scenes are **binary-serialized** [V], so UI content could not be read from scenes; screens listed from scripts/prefabs [V names, I contents]. CLIMB scenes/prefabs are YAML [V].

| Project | Screens/popups found | Layout approach |
|---|---|---|
| OBBY | Home (`HomeUI`, `HomeButtonSelectMinigame`, `HomeButtonMinigameFrame`, `HomeCharacter`), Shop (`ShopCharacter`, `ShopTab/Page/Pagination`, `Bike Shop`), ParkourRace Lobby + Progress GUI, Result (Win/Lose/Revive/Death/WinOrReplay), Reward (`RewardUnlockSkin(+Immediate)`, confirm), Settings, Rating, Announcement, Tutorial, Checkpoint popup, Loading screen, popups: Debug/Rate/RewardConfirm/InternetRequire (`Prefabs/UI/Popup`), World-space popups (`UI/PopupWorld`), `UIViewPanel.prefab` | Addressable `AssetReference` views (`_viewGUI`, `_viewWin` in `Dropper_Manager`) + `PopupManager`; joystick pack + touch detector |
| CLIMB | Gameplay HUD `Player_GUI` (`SafeArea`, `Look` drag area, Jump, Jetpack, height/reward displays: `HeightDisplayUI`, `RewardDisplayUI`, `WorldRewardUI`), CTJ: world selection (home + popup), gacha (stand + popup + info), wing shop, character skin shop, pet inventory/confirm popups, lucky wheel, daily gift/reward; DigMode canvases named "--- GAME CANVAS ---", "--- INPUT CANVAS ---", "--- GAMEPLAY UI --- (Digger)", "--- SHOW REWARD CANVAS ---", `DigMode_View_Gameplay`, Pickaxe shop/confirm, pet gacha popup, chest popup, `RewardClaimedUI`, depth marker/progress bar; Bomb: `Bomb_Shop`, `Bomb_Confirm_Popup`; many shops are world-space "Stand" objects (`Stand_*`) with their own canvases | multiple canvases per mode (input/game/reward separation), SafeArea child, world-space canvases for in-world stands |

### 5.1 Inconsistencies (do NOT learn from) [V counts via grep over prefabs/scenes in `_Game*`, `_GameModule`, `CFramework` of CLIMB]

| Issue | Evidence | Rule it breaks |
|---|---|---|
| Three reference resolutions | `m_ReferenceResolution`: 1920x1080 x29, 800x600 x14 (Unity default; incl. world-space stand canvases like `Stand_Pet_Special`, `Teleport`, `Pet Stand`), 1280x720 x6 | one project-wide reference (house UI skill: single portrait/landscape reference) |
| Mixed scale modes | `m_UiScaleMode: 1` (Scale With Screen Size) x35 vs `0` (Constant Pixel Size) x14; `m_MatchWidthOrHeight` 0 x48 (match width) with `m_ScreenMatchMode 1` (Expand) on HUD | choose scale mode + match consistently |
| Landscape 1920x1080 on a game that allows only landscape (`defaultScreenOrientation: 4`, autorotate L/R) | `CLIMB/ProjectSettings` [V] | OK for landscape only; do not reuse for portrait projects |
| TMP autosize inconsistent | `m_enableAutoSizing: 0` x394 vs `1` x191 (about one in three texts autosized); word wrap off x113 | autosize + min/max + wrap on every dynamic text |
| Raycast targets left on | `m_RaycastTarget: 1` x795 vs `0` x864 (nearly half of graphics) | disable on non-interactive graphics |
| Text wider than button / long labels | [I] cost strings like "113B"/"35a" in fixed-width buttons; not measured | validate by layout test (see `unity-ui`) |
| Canvas naming with decoration `--- GAME CANVAS ---` | `_Game_DigMode/Prefabs/` | plain names |
| Mixed Vietnamese/English object names | e.g. `Pet Stand`, `_Truong_Prefabs` | English naming |

## 6. Gaps, limits, unknowns

- OBBY scene/prefab YAML not readable (binary) so per-bike values, HUD hierarchy and canvas settings of OBBY are not verified; only code defaults.
- FlyToSpace and BuildingAHouse logic is absent from the repo (configs/art only).
- Unity 6 project versions for KT/monkey-escape not re-read here [I]; ride-a-pet/problox/steal-an-egg/tiny-relax were only inventoried, not deep-read.
- No Profiler data: all performance remarks are static-analysis only [I].
- `OBBY/CFramework` and `CLIMB/CFramework` may differ slightly (CLIMB has `Piloto Studio`, `Febucci`, PrimeTween); only OBBY CFramework was read.

## 7. Proposed classification

Skill names in `code` are proposals; check overlap with existing `skills/` (e.g. `config-driven-feature`, `zone-level-design`, `npc-bots-and-enemies`, `roblox-genre-patterns`, `roblox-character-camera`, `ui-popup-from-demo`, `unity-code-templates`, `world-batching-culling`, `reference-port`).

| # | Candidate | Class | Proposed name | Must-haves (3-6) |
|---|---|---|---|---|
| 1 | CFramework -> CodeSketch -> SketchEngine translation table | RECIPE | `legacy-framework-mapping` (could extend `reference-port`) | table of section 2; casing rules (`instance`->`Instance`, `value`->`Value`); never mass-replace namespaces; delegate-FSM -> class FSM; Odin binary save format location differs; verify with installed package source |
| 2 | Anti-pattern labels with file examples | RULE | `legacy-antipatterns` (append to `unity-code-templates` or `mobile-perf-audit`) | AP-01..AP-18 ids; each with file path + fix; "do not copy from legacy, copy concepts only"; mark KT/monkey-escape/thunder-break-egg as the style source |
| 3 | Legacy project trust ladder | DATA | `reference-trust-tiers.json` (inside `reference-index`) | tier per project (primary: KT, monkey-escape, thunder-break-egg; secondary: ride-a-pet, tiny-relax; legacy: bike-obby, climb-tower; unknown: problox, steal-an-egg); framework + Unity version; allowed use (mechanics only vs style) |
| 4 | Bike obby driving controller | RECIPE | `bike-parkour-controller` | velocity-based FixedUpdate with accel/decel times; yaw-rate curve (50-280 deg/s) + air rotation (40); coyote 0.15; lean/tilt via Animator or procedural; speed-ratio FOV 60-70; tuning in `[Serializable]` config + AnimationCurves; use `Time.fixedDeltaTime` in FixedUpdate (fix legacy bug) |
| 5 | Obby platform kit (break, fan, move, trampoline, speed boost, kill, swing, jetpack) | RECIPE | `obby-platform-kit` (extend `zone-level-design`) | default tuning table of section 3.1; registry collision dispatch (not per-object callbacks); config struct per platform; respawn/revive flags; pooled fragments for break |
| 6 | Mode-per-scene minigame hub | SKILL | `minigame-hub-architecture` | `MinigameConfig` SO + `MinigameType` enum + factory lookup; thin mode subclass over a base manager (G-01/G-02); Manager + LevelConstructor + Level + GUI quartet; world SO list per mode; avoid copy-pasted seasonal factories (AP-06) |
| 7 | Race mode with bots | RECIPE | `race-mode-with-bots` (extend `npc-bots-and-enemies`) | 1 player + N bots (21 total reference); state classes chase/walk/jump/move; waypoint stage data; bot removal delay; progress GUI + lobby + result; cutscene start timing |
| 8 | Stage/level constructor + editor converters | TOOL | `stage-constructor-tools` (extend `editor-tool-authoring`) | stage prefab with bounds/start/end/waypoints; concatenating constructor from SO list; batch prefab converter window; ProBuilder-shape replacer; mesh combine with atlas (compare with `world-batching-culling`) |
| 9 | Height-based climb reward loop | RECIPE | `climb-tower-reward-loop` (extend `roblox-genre-patterns`) | height tracker -> coin per meter (10/m, min 5) x world multipliers; collect on landing after delay; world unlock by currency (cup) with string-notated costs replaced by typed numbers; ladder + jump-off events |
| 10 | Idle number notation / big numbers | RECIPE | `idle-number-format` (extend `economy-progression-design`) | `double`/BigNumber storage; compact notation parser/formatter ("1K", "35a"); never store costs as free-text strings in new projects; world coin/climb multipliers |
| 11 | Pet / gacha / craft / equip system | SKILL | `pet-gacha-system` | Data (inventory, equipped, best-N auto-equip) / Factory / Config SO / popup split; craft rule (3 of same -> next); max slots (60) and equip (3) as config; view-next preview count; auto-hatch interval; use SketchEngine DataBlock, not legacy statics |
| 12 | Dig / bomb terrain-destruction modes | SKILL | `terrain-dig-and-bomb-modes` | Digger Pro brush config (range 10, size 3, sphere); depth tracker event-driven not per-frame; bomb stats (power/throwSpeed/delay/coinMultiplier); NPC rival brains; pickaxe/bomb ladders as SO lists; async edit toggle |
| 13 | Click-and-chew simulator loop (BGS) | RECIPE | `clicker-sim-loop` | hold threshold 0.5 s, cooldown 0.5 s, storage cap, sell trigger, island/portal unlock, jump height from stored count via curve asset (not tables) |
| 14 | World selection popup + teleport | RECIPE | `world-selection-flow` (extend `ui-pattern-library`) | SO world list; unlock by currency; `Event_Teleport` StaticBus; home selection + in-game popup share data; coming-soon flag |
| 15 | Multi-canvas HUD split | RULE | `ui-canvas-split-rule` (extend `unity-ui`) | separate input / game / reward canvases; SafeArea root; single reference resolution; world-space canvas reference documented separately (800x600 default is not a target) |
| 16 | UI inconsistency lint | TOOL | `ui-consistency-lint` (editor script) | report reference resolution / scale mode / match; TMP autosize off or no wrap; raycast target on non-interactive; text-vs-rect overflow; count per prefab; thresholds from section 5.1 |
| 17 | Force-text serialization & scene readability | RULE | `unity-serialization-text-mode` (extend `unity-project-bootstrap`) | require `m_SerializationMode: 2` (force text) so scenes/prefabs are agent-readable and diffable; check `ProjectSettings/EditorSettings.asset`; flag binary scenes as unreadable (OBBY) |
| 18 | Legacy scan: anti-pattern counters | TOOL | `legacy-metrics-scan` (extend `project-context-map` scanner) | counts of Update, Find*, Camera.main, GetComponent, LINQ, coroutine, Debug.Log, OnTrigger*, tween libs per assembly; top-N files; output table like section 4 |
| 19 | Project inventory | DATA | `project-catalog.json` (inside `reference-index`) | name, path, Unity version, framework, genre, `_Game` .cs count, scenes, notable systems, doc folder presence (section 1) |
| 20 | Fly-to-HUD currency collect | RECIPE | `currency-spread-fx` (already exists - cross-link only) | legacy `HCollect` steps as precedent; no new skill needed |
