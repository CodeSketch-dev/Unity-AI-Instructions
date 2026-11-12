# 06 - Minigames, Game Flow, Scenes and Canvas Structure

Sources (read-only): KT = `C:\Unity\GitProject\knife-tower\knife-tower-troll-unity\Assets\_Game` (Scripts/Logic/Minigame: 188 files), ME = `C:\Unity\GitProject\monkey-escape\monkey-escape-unity\Assets\_Game` (30 files).
Framework note (told by user): SketchEngine and CodeSketch are the SAME framework (optimized CodeSketch renamed). Both projects here use package `com.codesketch` (KT `Packages/manifest.json`; code read from `Library/PackageCache/com.codesketch@0fe9d8bab8cb`). Treat namespaces `CodeSketch.*` and `SketchEngine.*` as one lineage.
Tags: VERIFIED (file cited) / INFERRED.
Skills already in repo that overlap: clone-feature-recipes, roblox-genre-patterns, zone-level-design, ui-pattern-library, mobile-hud-layout.

## 1. Big picture

Neither game has a timed "round" loop. Both are persistent-progress Roblox-style obby/tycoon hybrids: a lobby (Home) lists minigames as cards; entering one loads a whole scene; there is no result screen on win in most modes. Death opens a revive popup; progress is checkpoint index (towers/obby) or level/trophy/money (keyboard modes). VERIFIED (Tower_Manager, Result_*, Data_Checkpoint).

| Fact | KT | ME | Evidence |
|---|---|---|---|
| Build scenes | 12 (Splash, Home, 3 SKB worlds, Snake/Camo/Monster tower, EasyObby, PaintKeyboard, 2 SKB event scenes) | 6 (Splash, Home, WukongEscape 1-4) | `ProjectSettings/EditorBuildSettings.asset` both |
| `Minigame_Type` enum | SpeedKeyboard=0, SnakeTower=1, CamoTower=2, EasyObby=11, MonsterTower=101, PaintKeyboard=201 (gaps = reserved decade ranges) | MonkeyEscape=0, MonkeyObby=1 | `Logic/Minigame/Minigame_Type.cs` |
| Persistent singleton prefab in every scene | `Prefabs/GameSingleton.prefab` | same name | scenes grep `GameSingleton` (9 KT scenes) |
| Scene count vs real modes | SKB has 3 worlds x (raw + `_Optimized`) + 2 event scenes; `Test*`, `New Scene`, `SpeedKeyboard_TestBoxBoss` are dev scenes not in build | WukongEscape_1..4 = 4 worlds; Test, Test_Portal not in build | Scenes folder |

## 2. Game-flow state machine (boot -> home -> select -> play -> result -> reward -> home)

There is NO enum/StateMachine for app flow. Flow is scene-driven plus StaticBus events. VERIFIED (no `StateMachine<` in Game/ or Scene/; GameManager uses StaticBus). StateMachine<T> is used only inside entities (e.g. `FNAF_Snake_State_*`, 5 states: Patrol, Chase, HideToSafeZone, ReturnToPatrol, ReturnToPit).

```
Splash.unity (BounceSdk, build idx 0)  -> BounceSdk SceneManager.LoadSceneAsync -> Home (idx 1)
Home: Minigame_Selection.Start -> Data_Minigame.ResetComplete -> Factory_Minigame.GetActiveListMinigame -> instantiate cards
card click: Minigame_Selection_Item.Button_OnClick
   -> Data_Minigame.GetEnter(type)++ ; LogHelper.EnterMiniGame / FirstEnterMiniGame (analytics)
   -> Minigame_Selection_Asset.Switch(): GameStatic.Reset(); ResolveSceneName();
        LoadType TransitionPlus -> SceneLoaderPlus.Load(scene)   (fade/mario wipe)
        LoadType LoadingScreen  -> LoadingScreen.Load(scene,...,bg) (progress bar, used for SKB bake)
   -> StaticBus<Event_Minigame_Selection>.Post  (GameManager shows banner; all cards disable)
Minigame scene Awake: Minigame_Master/Tower_Manager/SKB_Master/PKB_Master set Minigame_Static.Type, allowed skins, weapons, trails
Minigame scene Start: Minigame_GUI_Loader pushes GUI View (Addressables) into ViewContainer; Character_Checkpoint places player at checkpoint
play: checkpoint / level-up / money loop; death -> Event_Character_Dead -> Result_Factory.ShowReviveCheckpoint (rewarded-ad revive popup)
win (towers): Tower_WinDetector trigger -> Data_Minigame.CompletedThisSession=true + LogHelper.WinMiniGame
exit: Settings popup Home button -> Popup.Close -> OnCloseEnd: Event_Home_Return.Post + SceneLoaderPlus.Load("Home")
   GameManager.StaticBus_Home_Return: banner, LogHelper.ExitMiniGame, Factory_Character.SetAllowedSkinType(All), GameStatic.Reset, stop SFX
```
Evidence: `Logic/Scene/SceneLoaderPlus.cs`, `Logic/Minigame/Selection/Minigame_Selection*.cs`, `Logic/Game/GameManager.cs`, `Logic/Settings/Settings.cs` (BtnHome_OnClick), `Logic/Tower/Tower_WinDetector.cs`, `BounceSdk/BounceSdk/Scene/SceneManager.cs`. VERIFIED.

Key flow facts:
- Single-scene-per-minigame, `LoadSceneMode.Single`; NO additive scenes, no unload logic besides Single replacement. VERIFIED (`SceneManager.LoadSceneAsync(sceneName)` in SceneLoaderPlus; additive only in optional `LoadScene_FadeInOnly(loadMode)` param, default Single).
- Home is also the "result" destination: there is no dedicated Result scene. `Result_*` classes are revive popups (Result_Revive_Checkpoint/Killed/Stage/SkipCheckpoint). VERIFIED `Logic/Result/`, `Factory/Factory_Result.cs`.
- Reward: currency (Cup/Money/Gem) is granted inline during play (SKB steps, PKB ink, checkpoint) and by `SKB_MinigameEvent_WinPopup` Continue; `Event_SKB_ReturnBackWithReward` exists. No generic reward screen. VERIFIED (Event folder list, SKB_MinigameEvent_SceneManager L160-171).
- Reload/retry: `Factory_Minigame.Reload()` re-Switch current type; `Factory_Minigame.BackHome()` = `SceneLoaderPlus.Load(GameConstants.SCENE_HOME)`. `GameConstants.SCENE_HOME="Home"`. `GameStatic.IsSceneHome` hardcodes buildIndex==1 (fragile). VERIFIED.
- Busy guard: both loaders ignore calls while `_busy`; cards subscribe `SceneLoaderPlus.BusyChanged` to disable buttons. VERIFIED.
- Persistent objects across scenes: GameManager (`MonoSingleton`, PersistAcrossScenes), GameSingleton, ViewContainer, SceneLoaderPlus (DontDestroyOnLoad), LoadingScreen, PopupManager statics. ViewContainer closes all views on `activeSceneChanged`. VERIFIED (GameManager.cs, ViewContainer.cs, SceneLoaderPlus.Awake).

### 2a. Scene loaders
| Loader | Behaviour | Numbers |
|---|---|---|
| `SceneLoaderPlus` (TransitionsPlus asset) | fade-in covers screen, `onBeforeLoad`, LoadSceneAsync, `onComplete`, fade-out; `Overlay` vs `Classic` naming flips invert flag; APIs Load, Reload, FadeIn/Out, FadeToBlack/Clear, ForceBlack/ClearScreen, LoadScene_FadeInOnly | canvas sort 20000 (`Transition Plus.prefab`) / 100 (`Transitions Plus.prefab`) |
| `LoadingScreen` (MonoSingleton) | shows bar 0%, loads+ACTIVATES scene (freeze hidden), scene components call static `RegisterLoadTask(Func<IProgress<float>,UniTask>)` in Awake, bar driven by tasks, else fake fill; mutes audio during load | fade 0.25s, displayFollowSpeed 0.6/s, finalize 1.5s, holdAtFull 0.15s, 2 frames wait for register, scene progress mapped to 0.8 |
ME has the same two files under `Logic/Loading/` (copy). VERIFIED.

## 3. How a minigame is registered, entered, exited

Registration chain (3 touch points + build settings):
1. `Minigame_Type` enum value (`Minigame_Type.cs`) + `Minigame_Helper` string extensions for analytics keys (`{type}_Checkpoint`, `_Death`, `_Revive_Rewarded`, `_Result_Win_Continue/_Home`, `_Result_Lose_Retry/_Home`). VERIFIED.
2. `Minigame_Selection_Asset` (Odin `SerializedScriptableObject`, one per mode in `Configs/Minigame/`: Climb Camo Tower, Climb Snake Tower, Easy Obby, Monster Tower, Paint Keyboard, Speed Keyboard = 6 assets) with fields: Type, Title, LoadType, loadingBackground, Thumbnail, IsCommingSoon, `AI_Spawn_Config` (per device tier Low/Middle/High dictionary AI_Type->count), editor `SceneAsset` -> `_sceneName` via OnValidate, Odin buttons "Add/Remove to Build Settings". VERIFIED.
3. Add to `Factory_Minigame._minigames[]` (ScriptableObjectSingleton). `OnInitialize` builds `Dictionary<Minigame_Type,Asset>`, warns on duplicate, `SaveDefaultSortOrder`. VERIFIED.
4. Scene needs one master component setting `Minigame_Static.Type.Value` in Awake: `Minigame_Master` (generic, serialized `_type`), `Tower_Manager` (`_minigameType`), `PKB_Master` (hard-coded), `SKB_Master`. VERIFIED.

Ordering/remote: card order comes from `Data_Minigame._activedSortOrder` (persisted list of enum names), overridden by remote config `RemoteConfig.CONFIG.minigameSortOrder` (comma list, matched by enum name, spaced name or Title, case-insensitive). First item renders as a large card, rest as small grid cards (`Minigame_Selection.Start`). VERIFIED `Factory_Minigame.cs`, `Minigame_Selection.cs`. Large-card grid height hard-coded 747.
Persistent data: `Data_Minigame` = `_enter` (Dictionary<type, DataValue<int>>), `_completedThisSession` (re-created each Init, not persisted), `_activedSortOrder`. VERIFIED.

Per-mode policy is a set of switch statements keyed on type (anti-pattern, data opportunity):
| Policy | Where | Values |
|---|---|---|
| Weapons allowed | `Minigame_Static.IsWeaponAllowedForType` | false for MonsterTower, EasyObby, PaintKeyboard |
| Shield revive allowed | `IsShieldReviveAllowed` | false for SpeedKeyboard |
| AI drops high waypoints | `ShouldAbandonHighWaypoint` | true only SpeedKeyboard |
| Reset checkpoint on start | `ShouldResetCheckpointOnStart` | always true |
| Trail enabled | `Minigame_Master.Initialize` | false MonsterTower |
| Skin pool | Minigame_Master/SKB_Master/PKB_Master/EasyObby_Master | MonsterTower: Normal+Brainrot+Transfomer+VIP; SKB: Normal+VIP; EasyObby: Normal+VIP; Paint: Normal, VIP blocked; Camo/Snake: VIP blocked |
| Keyboard press duration override | `Minigame_Master` | optional 0.3s down / 0.4s up |
| Result popup type | `Factory_Result.ShowReviveCheckpoint` | SKB shows ReviveStage; others ReviveCheckpoint |
Static state is reset by `GameStatic.Reset()` (RagdollDuration 2.5s, AIAttackRangeMultiplier 0.5) on enter and on Home return. VERIFIED.

Exit: only via Settings popup Home button (see flow) or event-win popup; GameManager listens `Event_Home_Return`. Master `OnDestroy` undoes per-mode overrides (Keyboard press override, Item availability, Gameplay_UI.ForceHide, Keyboard_Static.MODE, DevicePolicy.RestorePaintKeyboardRenderPolicy). VERIFIED.

## 4. Per-minigame rules with real numbers

| Mode | Win | Lose / fail | Score / progress | Timer | Evidence |
|---|---|---|---|---|---|
| Climb Snake / Camo / Monster Tower (`Tower_Manager`) | Player enters `Tower_WinDetector` trigger -> once per session flag + analytics; no popup | Fall/kill -> `Result_Revive_Checkpoint` rewarded-ad revive (VIP: free revive via `Subscription_VIP.CanUseFreeRevive`); respawn at `Data_Checkpoint[type]` | Checkpoint index, per type, only increases (`_index > saved`), toast "New checkpoint reached!" | none | `Tower_Checkpoint.cs`, `Tower_WinDetector.cs`, `Result_Revive_Killed.cs` |
| Monster Tower AI | - | AI falls: FALL_THRESHOLD 15, DEEP_FALL 30, FALL_REVIVE_GUARD 2 s | - | - | `Monster_Tower_AI.cs` L20-22 |
| FNAF/Snake tower hazard | - | Snake FSM Patrol/Chase/HideToSafeZone; `FNAF_SafeZone` | events Snake_Appear/Leave | - | `Logic/Minigame/Climb FNAF Tower/` |
| Easy Obby (in `Assets/_Parkour3d`, namespace `Obby`) | last stage | revive at `Obby_Checkpoint` | stage list built from `_stagePrefabs[]` + `Turn{index,direction}[]` | none | `EasyObby_StageManager.cs` |
| Speed Keyboard (SKB) | endless; progression `level`, worlds | no death revive stage popup (ShowReviveStage with stage = checkpoint+1) | points to next level = `100 * 1.15^level` (`_levelBasePoint 100`, `_levelPointMultiplier 1.15`, plus `LevelPointCurve[]` overrides); earn tick every 0.25 s moving and on treadmill; rebirth allowed from level 15 (`_levelNeededToBeAllowedRebirth {15}`), rebirth multiplier steps {2,3,4}; tutorial auto-skipped when Level > 20 | tick 0.25 s | `Factory_SpeedKeyboard.cs` L22-65, `SKB_Master.cs` TUTORIAL_SKIP_LEVEL=20 |
| SKB timed event (KingBlox boss / CryoPanther orbs, own scene) | kill boss -> `SKB_MinigameEvent_WinPopup`; player presses Continue -> ReturnToLobby | - | boss HP phases at 0.66 / 0.33; boss level 10; reward = trophy x multiplier of deepest unlocked world | event cooldown first session 30-60 s, interval 180-300 s, duration 180 s, gate open 180 s; bot spawn 5-10 s, max 5 per stand, bot level 10; boss spawn 5-10 s x3 (0.1 s apart), mini-boss life 10 s; bot explosion 2 s; speed multiplier x2 | `SKB_MinigameEvent_Config.cs` L15-158, `SKB_MinigameEvent_SceneManager.cs` |
| Paint Keyboard (PKB) | none; tycoon loop (paint keys -> money -> buy paint / workers / land / upgrade -> rebirth) | none (no death) | money; tutorial thresholds 300 / 500 / 1000 money, money boost x3 during tutorial | none | `PKB_Master.cs`, `PKB_Tutorial.cs` |
| ME WukongEscape / MonkeyObby | endless levels + checkpoint stages (`StageManager` chains Stage prefabs) | revive popups | `Data_MonkeyEscape.Level/LevelPoint` | none | `MonkeyEscape_Master.cs`, `Stage*.cs` |
Not found in either project: time-limited rounds, lives, star ratings, scoreboards per run (Ranking factory exists, not analysed). INFERRED from absence in searched files.

## 5. Level / zone structure and authoring

| Authoring style | Used by | How | Evidence |
|---|---|---|---|
| Hand-built scene with prefab instances | Towers, Paint, SKB | scene is mostly PrefabInstances (Snake 34 PrefabInstances + 56 GameObjects, 5.5 MB; Paint 29 PI + 13 GO; Home 8 PI + 14 GO) | scene greps |
| Checkpoint array on a manager | Towers | `Tower_Manager._checkpoints[]` (Awake sets `Checkpoint_Static.CheckpointCount`, Start assigns index, renames `Checkpoint-N` in Editor); `_floors[]`, `Turn{Index,Angle}[]`, BoxCollider bounds with cache | `Tower_Manager.cs` |
| Procedural stage chain from prefab pool | EasyObby, ME Obby | `StageManager`/`EasyObby_StageManager`: `_stagePrefabs[]`, `Turn[]`, `_checkpointPrefab`, Odin button "Load Stages from Folder", Generate links start/end offsets (`Stage._startPointOffset/_endPointOffset`, default checkpoint size 8x1x8), stages run -Z -> +Z in local space | `Stage.cs`, `StageManager.cs` |
| Keyboard grid baked at load | SKB, PKB, ME | `Keyboard_*` (13 files KT, 19 ME): chunk planner, culling manager, vertex baking; `LoadingScreen.RegisterLoadTask` shows progress | `Logic/Keyboard/` |
| Zones | PKB fields | `PKB_Field.All` (unlock applied in `PKB_Master.Start`), `PKB_Field_PatrolZones`; SKB worlds = `SKB_World_Asset` list in `Factory_SpeedKeyboard._worlds` (each has SceneName, WorldID); teleport gates + `SKB_World_Popup` world picker | files |
| Optimized variants | SKB W1-W3 | `*_Optimized.unity` replace raw scenes in build; `Scene_Optimizer.cs`, `Keyboard_Chunk_Culling_Manager`, `MeshSceneCombiner`-style baking (see world-batching-culling skill). Raw scene kept as editable source (INFERRED: build uses only `_Optimized`). | EditorBuildSettings |
Worlds: SKB enters the LAST world the player stood in (`Data_SpeedKeyboard.LastWorldID`, written in `SKB_Master.Awake`, not OnDestroy, because OnApplicationQuit saves first) via `Minigame_Selection_Asset.ResolveSceneName`. ME has `ForceWorldID` static and `DetectAndSetWorld` by scene name, same pattern. VERIFIED.

Scene conventions (VERIFIED from YAML):
- Names: `Minigame_<Mode>[_<World>][_Optimized]`; events `SpeedKeyboard_<Boss>_Event`; test scenes `Test*`. Inconsistent casing `MiniGame_` vs `Minigame_`.
- Home roots: Main Camera, Buttons, Content_Grid, Background/Shape, MinigameSelection, BGM, Directional Light, Canvas (Viewport, ScrollRect, Content_Odd, SafeArea). Minigame scenes: 4-6 root GOs (Plane/PaintZone/Directional Light/BGM/`PaintKeyboard_Master`/`PKB_Tutorial`) - gameplay objects are prefab instances.
- Tags: only Untagged / MainCamera used in scenes sampled; custom tags in TagManager: Kill, Missile, Target (+"Decoration" used by EasyObby_Stage). Layers (24 slots): Default, TransparentFX, Ignore Raycast, Player, Water, UI, Character, Character_Ragdoll, Character_Invisible, Ladder, Item, Character_Only, Outline, Ignore Pathfinding, Decoration, Gacha, Ignore_CameraCollision, Ignore Wall, Raycast. Scene sampling: Snake 54/56 GO on layer 0. `ProjectSettings/TagManager.asset`.
- Scene masters are tiny MonoBehaviours (SKB_Master 158 loc, PKB_Master 92, Minigame_Master 87) that mostly flip global policy statics.

## 6. Canvas structure (in depth)

### 6.1 Inventory with counts
| Canvas | Where | Mode | Sort | Scaler | Role |
|---|---|---|---|---|---|
| `Canvas` (child of GameSingleton) | `Prefabs/GameSingleton.prefab` | ScreenSpaceOverlay (m_RenderMode 0), camera null | 2506 | ScaleWithScreenSize (UiScaleMode 1), ref 1920x1080, ScreenMatchMode 1 (Expand), Match 0, RefPixelsPerUnit 100 | HOST of `ViewContainer` + `UISafeArea` (GUI Views pushed by `Minigame_GUI_Loader`/`EasyObby_Master`) |
| `Canvas_Popup` (GameSingleton) | same prefab | Overlay | 12506 | same settings (ref 1920x1080, Expand, 0) | HOST of `PopupRootSetter` -> becomes `PopupManager.Root`; all popups parent here |
| Home `Canvas` | `Scenes/Home.unity` (1 canvas, `^Canvas:` count 1) | Overlay, camera null | 0 | ScaleWithScreenSize 1920x1080, Match 0 | selection ScrollRect + `SafeArea` child |
| Minigame scenes | PaintKeyboard, Snake, SKB W1 Optimized | 0 canvases in scene file | - | - | all UI comes from GameSingleton or Addressable views (grep `^Canvas:` = 0) |
| `Player_GUI.prefab` | `Prefabs/Player` | Overlay | 0 | 1 scaler, 1 raycaster | player HUD (1 canvas) |
| GUI view prefabs (`Minigame_GUI_View`, `PaintKeyboard_GUI_View`, `SpeedKeyboard_GUI_View`, `TowerOfHell_GUI_View`) | `Prefabs/Minigame/**` | 0 own canvases (grep) | inherit 2506 | inherit | views have `CanvasGroup` (View requires it), Minigame_GUI_View and TowerOfHell view carry a `UISafeArea` |
| `UI_MinigameEvent_CryoPanther.prefab` | SKB event | Overlay | 1000 | 1 scaler | event HUD standalone canvas |
| `Character.prefab`, `WouldYouRather.prefab` | world-space (m_RenderMode 2) | WorldSpace | 0 / 5-10 | scaler present | name tags/health bars over characters; WYR 2 canvases (sort 5, 10) |
| SDK canvases | BounceSdk/Plugins | Overlay | Transition Plus 20000 / Transitions Plus 100 / Interstitial 999 / Rewarded 999 / BannerTop 500 / BannerBottom 500 / Graphy 30000 / ADAPTIVE 32767 | - | ad and debug layers always above game UI |
Prefabs containing a Canvas: 29 in KT (incl. ~16 SDK ad/consent size variants). Prefabs with `m_OverrideSorting: 1` (nested canvases for rebuild isolation): 0 in KT `_Game` and SDK prefab search. VERIFIED (grep), so NO nested-canvas isolation pattern exists in KT; isolation is instead by separate root canvases + `Gameplay_UI.ForceHide`. Prefab scalers in sample: 5 ScaleWithScreenSize 1920x1080/Match 0, 3 ConstantPixelSize 800x600 default (SDK/tools). ME: GameSingleton has the same two canvases with identical numbers (12506 / 2506, 1920x1080, Expand, Match 0); ME Home 1 canvas; 4 prefabs with Canvas. VERIFIED.

### 6.2 Boot and relationships
- Not created by code. `GameSingleton.prefab` (a persistent prefab instance placed in EVERY scene that needs UI: Home + each minigame; 9 KT scenes grep) carries EventSystem, ViewContainer, UISafeArea, popup root, internet popup (`UI_Internet_Popup`), `IAP_Minigame_Entry_Guard`, etc. `GameSingleton : MonoSingleton` with PersistAcrossScenes = true so duplicates self-destroy when returning to Home. VERIFIED (GameSingleton.cs, prefab names).
- Order: Splash (SDK) -> Home loads GameSingleton from scene; `GameMasterInit` (`RuntimeInitializeOnLoadMethod AfterSceneLoad`) applies target FPS (min(refresh,60), vSync 0), `DevicePolicy.ApplyRenderPolicy/PhysicsPolicy`, audio/vibration settings, SRDebug. VERIFIED.
- Popup vs HUD: `PopupManager.Root` finds the first ScreenSpaceOverlay canvas with `PopupRootSetter` (highest sort wins) via `FindObjectsOfType<Canvas>` once, caches; `PopupRootSetter.Start` calls `SetRoot`. Popups are NOT own canvases: `PopupManager.Create(prefab)` instantiates under Root and `SetAsLastSibling`. So HUD view canvas (2506) is always below popup canvas (12506); popup stack hides the previous top (`SetEnabled(false)`). Alternative `PopupManager.Create(prefab, specifiedRoot)`. VERIFIED `Runtime/Popup/PopupManager.cs`.
- Why the gap numbers (INFERRED): 2506 / 12506 leave slots under 500 (banner placeholders) ... above 999 (ad prefabs), and below 20000 (scene transition) so transitions cover popups; Graphy 30000 and ADAPTIVE 32767 debug overlays on top.
- Static vs dynamic split (INFERRED): static container canvases (2 in GameSingleton) vs content swapped via ViewContainer; world-space canvases only on characters. No explicit static/dynamic canvas pair inside a screen.
- Safe area: `UISafeArea` (CodeSketch `Runtime/Utilities/UI/UISafeArea.cs`) conformX/Y, optional refreshOnUpdate, applies `Screen.safeArea` anchors; on the ViewContainer host object in GameSingleton (and Minigame_GUI_View, TowerOfHell view) and on Home `SafeArea`. Popups: Canvas_Popup has no safe-area component found (popup overlays are full-screen). VERIFIED partially (guid count 2 in GameSingleton).
- Banner clearance: banner is shown via `AdsHelper.ShowBanner()` (MAX SDK native overlay, called in GameManager.Start, on selection, home return, after death/revive, in `Tower_Master.Start`); no code in `_Game` reserves layout height for it (grep BannerBottom only in BounceConfig). Clearance is by HUD layout design, not code. INFERRED.
- Camera: all game canvases are Overlay (camera null) so no UI camera; world-space canvases use `rootCanvas.worldCamera` only in a few helper scripts (Gacha info, PKB buttons check `renderMode`). VERIFIED (grep of Gacha_Box_UI_Information, PKB_Field_Expand_Button).
- Raycast: each canvas root has 1 GraphicRaycaster (BlockingObjects 0, IgnoreReversedGraphics 1) in GameSingleton; per-element Raycast Target hygiene not audited.
- Hide/show: `Gameplay_UI.ForceHide = true` and `Event_Gameplay_UI_SetActive` hide the shared HUD for keyboard/obby modes; cutscenes (`Tower_Master`) `SetActive(false)` the ViewContainer GameObject during `Event_CutScene_Start`. VERIFIED.

## 7. Tutorial / guide system

| Aspect | KT (SKB, PKB) | ME |
|---|---|---|
| Driver | `SKB_Tutorial` (165 loc) / `PKB_Tutorial` (510 loc): phase constants, world arrow `QuestTargetArrowGuide`, `Quest_Focus_Pointer` (finger icon + message) | `MonkeyEscape_Guide_Manager` MonoSingleton + `MonkeyEscape_Guide_Phase` subclasses (ReturnZone, Shop, Treadmill, WallJump) |
| Persistence | `Data_SpeedKeyboard.IsTutorialCompleted/TutorialPhase`, `Data_PaintKeyboard.TutorialPhase` | `Data_Tutorial.Completed/Phase` |
| Registry | `*_Tutorial_Phase` registers location markers (PKB: 6 `LOCATION_*` constants, 8 steps) | `[Button] CollectPhasesFromScene` sorts phases by `Phase` int; `CompleteCurrentPhase` -> Phase+1, no next => Completed |
| Skips | level > 20 auto-completes (SKB); step analytics `LogHelper.LogTutorialStep(phase-1)` | `_ignoreTutorial` marketing bool |
| After finish | Data_Shop.EnsureBoostRestocked, after 1 s `Factory_IAP.ShowVipThenPackAll` | after 1 s `Factory_IAP.ShowPackAll`, RatingHelper.Show |
PKB step thresholds 300 / 500 / 1000 money; popup dismissed without buying re-shows arrow loop. VERIFIED (files above).

## 8. Shared vs copy-pasted code (pipeline opportunity)

Cross-project (KT vs ME), same-named classes after prefix normalisation (`SKB_`/`MonkeyEscape_` -> X_), diff-lines out of file lines:
| Pair | Lines KT/ME | Differing lines | Verdict |
|---|---|---|---|
| Teleport_Gate | 39/41 | 6 | near-identical copy |
| World_Popup | 53/53 | 26 | near copy |
| Teleport_Popup | 113/121 | 30 | near copy |
| Entrophy_Multiplier | 33/30 | 19 | copy |
| UI_Button_EntrophyX2 | 51/52 | 35 | copy |
| Return_Stage | 99/83 | 70 | diverged |
| Rebirth_Popup | 218/170 | 100 | diverged |
| Step_Stand | 350/408 | 106 | diverged |
| Entrophy_X2 | 79/48 | 71 | diverged |
| Master | 158/92 | 152 | diverged (different content) |
| GUI | 319/247 | 356 | diverged |
SceneLoaderPlus, LoadingScreen, Minigame_Selection_Asset, Minigame_Type helpers, Keyboard_* (13 vs 19 files), Treadmill (ME 5 files vs SKB_Treadmill 4), Result_Revive_* are copied between repos (not a package). VERIFIED by file presence/diff.
Within KT: three keyboard minigames (SKB 95 files / 11,232 loc, PKB 49 / 6,047, Obby 15 / 1,141, FNAF 17, Selection 4 / 301 loc) each re-implement Master + Static + GUI + Tutorial + World/Teleport popups with `SKB_`/`PKB_` prefixes. Generic parts already shared: Minigame_Master/Static/Type, Data_Checkpoint, Checkpoint_Manager, Result_*, Tower_* (706 loc), Factory_Minigame. Per-mode `Factory_X` + `Data_X` (SpeedKeyboard, PaintKeyboard, FNAFTower, Tower). VERIFIED.

## 9. Minimal vertical slice for a NEW Roblox-style minigame (checklist)

Smallest working slice (checkpoint obby mode), reusing existing infra:
1. `Minigame_Type` enum entry + `Minigame_Helper` strings (1 line).
2. Scene `Minigame_<Name>.unity`: GameSingleton prefab, `Minigame_Master`(type) or `Tower_Manager`, player spawn, N `Tower_Checkpoint` (ICharacterCollidable via OptCollisionRegister), `Tower_Fall_Detector`, `Tower_WinDetector` trigger, BGM object, NavMesh/AI waypoints if bots.
3. `Minigame_Selection_Asset` in `Configs/Minigame/` (title, thumbnail, scene, LoadType, AI_Spawn_Config per tier) + add to `Factory_Minigame._minigames` + Add-to-Build-Settings button.
4. GUI: `Minigame_GUI_Loader` with Addressable GUI View (copy `Minigame_GUI_View`), safe-area child.
5. Policy switches (weapons/skins/trails) in `Minigame_Static`/`Minigame_Master` if non-default.
6. Result: reuse `Factory_Result.ShowReviveCheckpoint`; win = trigger + `Data_Minigame.CompletedThisSession` (+ reward popup if wanted).
7. Verify: Splash->Home->card->scene->death->revive->Home loop in Play Mode, Console clean, GUI view appears, checkpoint persists via `Data_Checkpoint`.
Estimated new code: ~0 lines for tower-style mode, ~300-500 lines (Master, Static, GUI, Tutorial) for a bespoke economy mode. INFERRED from file sizes.

## 10. Proposed classification

| Candidate | Class | Proposed name | Must contain (3-6 items) |
|---|---|---|---|
| Minigame registration chain | RECIPE | `minigame-registration` | enum+helper strings; Selection_Asset fields (Type, Title, Thumbnail, LoadType, scene, AI tiers); Factory list + dictionary init + duplicate warning; build-settings button; Type set in scene master Awake; remote sort order |
| Scene loading flow | SKILL | `scene-flow-loading` | SceneLoaderPlus vs LoadingScreen choice rule (bake > 1s => LoadingScreen); `RegisterLoadTask` pattern; busy guard + card disable; persistent singletons list; Home return event cleanup; avoid buildIndex==1 hardcode |
| Per-mode policy switches | RULE | `minigame-policy-data` | no `switch(type)` scattered; move weapons/skins/trails/revive/checkpoint-reset into `Minigame_Selection_Asset` fields; masters only apply and revert in OnDestroy |
| Persistent GameSingleton + 2 canvases | SKILL | `canvas-structure` | GameSingleton prefab holds view canvas 2506 + popup canvas 12506 + EventSystem; Overlay, scaler 1920x1080 Expand Match 0 RPPU 100; PopupRootSetter; SDK sort bands (banner 500, ads 999, transition 20000, debug 30000+); world-space only for character tags |
| Safe area and banner clearance | RULE | `ui-safe-area-banner` | UISafeArea on view root not background; popup canvas full-screen; banner is native overlay so reserve bottom margin in HUD layout; nested canvas isolation missing (add `OverrideSorting` sub-canvases for animated HUD) |
| Checkpoint tower/obby level | RECIPE | `checkpoint-climb-level` | Tower_Manager checkpoints[] + index assign; OptCollisionRegister checkpoint/fall/win triggers; Data_Checkpoint per type; revive popup; cutscene camera path |
| Procedural stage chain | RECIPE | `stage-chain-obby` | Stage prefab with start/end offsets and checkpoint size 8x1x8; Turn list; folder-load + Generate editor button; AI waypoints per stage |
| Revive / result popups | SKILL | `revive-result-flow` | rewarded revive, VIP free revive, give-up path, close=give-up, control disable/enable events, analytics key strings per type |
| Tutorial phase system | RECIPE | `tutorial-phase-system` | phase int persisted in DataBlock; phase registry collected by Odin button; arrow + focus pointer; auto-skip by level; post-tutorial hooks (IAP, rating) |
| Timed event mode | RECIPE | `timed-event-minigame` | config SO with cooldown/interval/duration/gate windows; boss HP phase thresholds; bot spawner; win popup Continue returns to lobby; unix end-time Data |
| Keyboard/idle economy mode | RECIPE | `economy-mode-skeleton` | Master+Static+Data+Factory+GUI+Tutorial skeleton, level curve `base*mult^lv`, rebirth gating, treadmill tick 0.25 s |
| Duplicated prefixed modes | TOOL | `minigame-scaffold` | editor generator creating enum, SO asset, Factory entry, scene with GameSingleton + master, GUI view prefab, build-settings add; de-duplicate Teleport/World/Rebirth/Entrophy popups into one generic set |
| Minigame catalog + numbers | DATA | `minigame-catalog` | table of 6 KT / 2 ME modes with policy values, rule numbers, scene names, canvas sort constants (above) |
| Scene naming/layers | RULE | `scene-naming-conventions` | `Minigame_<Mode>_<World>[_Optimized]`; roots limited; custom layers list; tags Kill/Missile/Target/Decoration; keep Test scenes out of build |
