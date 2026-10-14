# 08 - Tooling, project settings and SDK stack (reverse-engineering catalog)

Scope: read-only study of `knife-tower-troll-unity` (KT) and `monkey-escape-unity` (ME), 2026-10-14.
Legend: **V** = VERIFIED (file cited), **I** = INFERRED. Paths are relative to each project root. No secrets are printed; for secret-bearing files only the path is named.

## 1. Executive findings

| # | Finding | Tag |
|---|---|---|
| 1 | Both projects are the same studio template (Bounce / CodeSketch): same SDK stack, same Debug layer, Splash scene first, same defines. ME is the younger, leaner copy (417 vs 713 `_Game` .cs files). | V `ProjectSettings/ProjectSettings.asset`, `EditorBuildSettings.asset` |
| 2 | Unity 6000.0.78f1 (KT, URP 17.0.4) vs 6000.3.22f1 (ME, URP 17.3.0). The rest of the manifest is near-identical. | V `ProjectSettings/ProjectVersion.txt`, `Packages/manifest.json` |
| 3 | **0 first-party asmdefs.** All `_Game` code compiles into `Assembly-CSharp` + `Assembly-CSharp-Editor`. KT `Assembly-CSharp.dll` is only 1.8 MB and Hot Reload is installed, so compile time is mitigated, not solved. | V `find Assets -name *.asmdef`, `Library/ScriptAssemblies` |
| 4 | SDK glue is a **vendored "Bounce SDK"** (not UPM) in `Assets/BounceSdk`, `BounceCommon`, `BounceDev`. Game code never calls MAX/Adjust directly: it goes through `AdsHelper` -> `BounceAdsSdk` and `BounceSdk.LogEvent`. | V `BounceSdk.cs`, `Scripts/Logic/Monitize/AdsHelper.cs` |
| 5 | **Anti-patterns not to copy**: keystores (`Upstore/*.keystore`), `google-services.json` and `Resources/BounceSdk/Bounce.BounceConfig.asset` (ad unit ids, Adjust tokens) are tracked in git; a default MAX SDK key literal is hard-coded in `BounceConfig.cs`; `ProjectVersion.txt` is gitignored. | V `git ls-files`, `.gitignore` |
| 6 | Firebase packages are installed but `USE_FIREBASE` is **not defined** in either project, so `FirebaseManager` compiles to no-ops. Analytics = Adjust + Bounce server log (`log_evt`, `log_ads`). | V defines in `ProjectSettings.asset`, `FirebaseManager.cs` |
| 7 | 17 first-party editor tools in KT, 5 in ME. Most are one-off helpers (Vietnamese comments); about 7 are reusable patterns (section 2). | V |

## 2. Editor scripts (first-party)

KT: `Assets/_Game/Scripts/Editor/` (+1 feature-local). ME: same folder plus `Assets/_Game/Editor/`. Conventions seen: `MenuItem` under `CodeSketch/Tools/...` or `Tools/...`; newer tools are Odin `OdinEditorWindow` with `[Button]`, older ones plain `EditorWindow`; `EditorPrefs` for last paths; mostly no `Undo`, no caps, no result file.

| Tool (file, project) | Problem solved | How it works | Reusable? |
|---|---|---|---|
| `AudioConfigGeneratorWindow` (KT) `CodeSketch/Tools/Audio Config Generator` | Hand-making one `AudioConfig` SO per clip | Drop AudioClips -> creates `Sfx_<clip>` `CodeSketch.Audio.AudioConfig` in `Assets/_Game/Configs/Audio/Sfx`; prefix/folder in `EditorPrefs`; `EnsureFolderExists` | **YES** generic clip->config bulk creator (adapter per audio framework). V |
| `PrefabReplaceWindow` (KT) | Swap many scene children (greybox/imported) for authored prefabs | Name-match children by `ReplacementPrefix` ("M_") or mesh name; instantiate prefab; disable old with `[OLD_REPLACED]` prefix; remove missing scripts | **YES** greybox->prefab pass. V |
| `MaterialCollectorWindow` (KT) | Materials scattered in imported packs | Scan parents' Renderers -> move (GUID-safe) or copy into one folder | **YES** asset hygiene. V |
| `Material_Match_Finder_Window` (KT) | "Who uses this material?" | Scene scan of renderer materials, prints hierarchy path | small, reusable. V |
| `ColliderExtractorWindow` (KT) | MeshCollider on combined mesh tunnels at speed | Clones non-trigger BoxColliders into child "Collider" root, skips `Tag_SkipMeshSceneCombiner` subtrees; prefab asset and scene aware | **YES**, pair with mesh combine (`world-batching-culling`). V |
| `Localize_GlyphPreloader` (KT) `Tools/Localize/Force Load All Glyphs Into Atlas` Ctrl+U, `Export Required Characters Per Font` | Dynamic TMP atlases bake lazily; need static atlases for 9 locales | Reflects every `LocalizeKey` const, loads per-`Locale` table text, Arabic fixed via RTLTMPro, forces glyphs into the `Factory_Localize_Font` font; human flips atlas Dynamic->Static | **YES** any multi-script TMP game. V |
| `NavAstarLinkEditor`, `NavTraversalLinkEditor` (KT; ME only Traversal) | Placing off-mesh links by hand | Scene-view click start/end; creates A* `NodeLink2` or `NavMeshLink` + wrapper component; remap, one-way flip, preview | reusable for navmesh games (A* variant needs A* Pro). V |
| `Character_Component_Copy_Tool` (KT) | Copy colliders/joints/rigidbodies between two rigs | Map nodes by path; **two passes** (create all, then resolve joint links) | **YES** rig transfer. V |
| `UnityToBlender_Format` (both) | Round-trip layout to Blender | 1) delete inactive children + uniquify names, 2) export CSV (name, pos, path, colour) | niche; "export layout to DCC" pattern. V |
| `KB_KeyboardPrefabExtractorWindow` (659 L), `SKB_Keyboard_Window`, `PKB_Field_UUID_Window` (KT); `Keyboard_Window` (ME) | Genre-specific stage authoring | `LoadPrefabContents` read-only extraction, prebake chunks, rebuild UUIDs | genre-specific; pattern reusable, code not. V |
| `AnimationSequenceFinderWindow` (KT) | Find `AnimationSequence` by `ActionOnEnable` flag | Odin window + reflection filter | CodeSketch-specific. V |
| `AttachCharacterFxTool` (KT) | One-shot wiring of FX prefabs into Character prefab | Nested-prefab aware field wiring | one-off. V |
| `Add_VIP_Jackpot_Benefit` (KT) | One-shot prefab patch | `[InitializeOnLoadMethod]` -> `LoadPrefabContents` **on every domain reload** | **anti-pattern**. V |
| `DebugVertexColors` (KT) | Inspect vertex colours | Distinct colours + counts of selected mesh | tiny. V |
| `ParticleGrassField` (ME, lives in `Scripts/Editor/` but is a runtime MonoBehaviour) | Interactive grass cut by one ParticleSystem | Array health/hit-test, no GameObjects or colliders | mis-placed (would not ship from an Editor folder); recipe worth keeping. V |
| `AndroidHardwareAccelerationPostprocessor` (ME `Assets/_Game/Editor/`) | Unity 6 writes `hardwareAccelerated="false"`; native GMA video needs true | `IPostGenerateGradleAndroidProject`, `callbackOrder=int.MaxValue`, edits generated manifest for `UnityPlayerActivity` and `UnityPlayerGameActivity`, throws if node missing | **YES** postprocess template. V |
| `BounceConfigEditor` (SDK) | Toggle define symbols from a checklist | Writes `USE_ADMOB/USE_MAX/USE_IRONSOURCE/USE_ADJUST/USE_SOLAR/MAX_USE_ADMOB`; validates tokens present | pattern reusable. V `Assets/BounceSdk/BounceSdk/Editor/BounceConfigEditor.cs` |
| Third-party tools | Asset Cleaner, BuildReport, Graphy, MAX IntegrationManager, EDM4U (`Assets/Packages Required/*`) | - | house dependencies. V |

Notes for the pipeline:
- Studio tools are **not** idempotent/chunked/guarded like `editor-tool-authoring` demands (no caps, mostly no Undo, no file log): the skill is stricter than practice. I
- Tools are Odin-first (`[Button]`, `[FolderPath]`, `[InfoBox]`); a project without Odin needs plain `EditorWindow`. I
- `MenuItem` roots are inconsistent (`CodeSketch/Tools`, `Tools/CodeSketch`, `Tools/<Feature>`, `CodeSketch/EasyObby`). Proposal: one root `Tools/Game/<Feature>/<Name>`. I

## 3. Debug layer (`Assets/_Game/Scripts/Logic/Debug`, about 25 files each)

| Piece | Behaviour | Tag |
|---|---|---|
| `DebugButton : UIButtonBase` | Empty base; one `Button_OnClick()` override per action. Buttons sit in a debug popup (`Factory_Prefab.DebugPopup`) shown from the SRDebugger panel: `GameMasterInit.InitSRDebug()` hooks `PanelVisibilityChanged`. | V `GameMasterInit.cs`; popup contents I |
| `DebugToggle : DebugButton` | virtual `bool isOn`; click flips and tints green/red. Subclasses bind persisted `DataMaster.*` flags: `DebugToggleAdBannerSkip`, `...AdInterSkip`, `...AdRewardSkip`, `DebugToggleUIHidden` | V |
| Currency/progress | `DebugButtonCurrency`, `DebugCurrencyGem`, `DebugCurrenyCup` (sic), `DebugButtonLevel`/`DebugButtonSKBLevel`, `DebugCheckpointNext/Prev/GoTo`, `DebugButtonJackpotFreeSpins`, `DebugUnlockAll{Skin,Trail,Weapon,Key,Assistant}` | V |
| Save | `DebugButtonClearData`: `DataFileHandler.DeleteAllInDevice(); Application.Quit();` (no confirmation) | V |
| IAP | `Debug_FakeIAP`: builds a `ConfirmedOrder` from a **real fetched Product** + fake receipt and calls `IAPManager.DebugSimulateOrderConfirmed`, so the real handler and revenue log run; product via Odin `ValueDropdown` on `IAPCatalog`. `Debug_FakeSubscription` | V |
| `DebugSubscriptionHotkeys` | `#if UNITY_EDITOR`; auto-spawns `AfterSceneLoad`; Ctrl+1..9 = free trial, paid, cancel (entitlement kept), trial->paid, renew, resubscribe, natural expiry, refund revoke, wipe | V |
| `SRDebuggerGraphyAutoToggle` (ME) | Editor-only; enables Graphy overlay when SRDebugger is enabled on Splash | V |
| Engines | SRDebugger/SROptions ship inside `com.codesketch` (`Plugins/StompyRobot`); Graphy at `Assets/Graphy - Ultimate Stats Monitor` (KT); SDK `BounceDebugPanel` auto-created in Editor/dev/standalone with Remove-Ads and Show Inter/Rewarded/Banner/AppOpen/Native buttons | V `Library/PackageCache/com.codesketch*`, `BounceDebugPanel.cs` |

Gaps vs `debug-cheats-menu` skill: studio files are **not** individually `#if`-gated (release safety depends on the popup/SRDebugger not being reachable) - I; no "cheated" session flag or reset confirmation. Ideas worth adding: persisted ad-skip toggles, fake IAP through the real handler, subscription hotkey matrix.

## 4. Packages (manifest comparison)

| Dependency | KT | ME | Class |
|---|---|---|---|
| Unity Editor | 6000.0.78f1 | 6000.3.22f1 | project choice |
| URP / ShaderGraph | 17.0.4 / 17.0.4 | 17.3.0 / - | house |
| UGUI | 2.0.0 | 2.0.0 | house |
| Input System | 1.19.0 | 1.20.0 | house; activeInputHandler=2 (Both), code still uses legacy `Input` |
| Cinemachine | 2.10.7 | 2.10.7 | house (2.x, not 3) |
| Addressables | 2.9.1 | 2.9.1 | house (groups are localization only) |
| Localization | 1.5.12 | 1.5.12 | house |
| AI Navigation | 2.0.13 | 2.0.14 | house |
| Timeline / Splines | 1.8.12 / 2.8.4 | 1.8.12 / - | Splines KT-only |
| Unity Purchasing | 5.4.1 | 5.4.2 | house |
| Recorder / FBX / Newtonsoft | 5.1.6 / 5.1.6 / 3.2.2 | 5.1.7 / 5.1.6 / 3.2.2 | house tools |
| ProBuilder, Memory Profiler, Android Logcat, Device Simulator | yes | no | KT extras |
| `com.codesketch` + installer | git `#main` | git `#main` | **house framework**, floating branch |
| UniTask | git (Cysharp) | git | house |
| PrimeTween | local tgz | local tgz | house tween; DOTween also present (`DOTWEEN` define) for legacy |
| Vertx debugging (OpenUPM scope) | 3.0.2 | 3.0.3 | house, optional |
| Firebase app/analytics/remote-config, EDM4U | 13.6.0, EDM 1.2.186 | 13.15.0, EDM 1.2.188 | installed, **disabled** by define |
| Google Play core/review/common | 1.8.6 / 1.8.4 / 1.9.2 | same | house (in-app review) |
| `com.coffee.ui-particle`, RTLTMPro, NuGetForUnity | yes | yes | house |
| `com.piti6.spike-trap` | yes | no | KT extra |
| A* Pathfinding Pro | embedded `Packages/com.arongranberg.astar` 5.4.5 | absent | KT one-off |
| ProjectDawn Navigation, Hot Reload | embedded in `Packages/` | embedded | house-ish |
| Odin Inspector + OdinSerializer | `Assets/Plugins/Sirenix`, `Assets/OdinSerializer` | same | house (`ODIN_INSPECTOR_3_x`, `CODESKETCH_ODINSERIALIZER`) |
| Spine | `Assets/Spine` runtime 3.8 | absent | KT one-off (old runtime) |
| OmniShade | v1.9.5 | in Assets | house shader pack |
| Kamgam UGUIWorldImage | yes | yes | house (`KAMGAM_UGUI_WORLD_IMAGE`) |
| MeshCombiner | not in manifest; `MeshSceneCombiner` is first-party/CodeSketch | same | I |
| Febucci TextAnimator, DOTween (Demigiant), Joystick Pack, KinematicCharacterController, HighlightPlus, TransitionsPlus, FogShader, BuildReport, AssetCleaner, BestHTTP Pro | `Assets/Plugins`, `Assets/Packages Required` | same set | house kit |
| Dreamteck Splines, Simple Scroll-Snap, Voxel Labs | yes | no | KT extras |

"House" = present in both with the same role. Version drift follows the Unity version; the only floating pin is `com.codesketch#main`.

## 5. SDK stack and wiring

### 5.1 Components (both projects)
| SDK | Location | Enabled by | Tag |
|---|---|---|---|
| AppLovin MAX | `Assets/MaxSdk` (asmdef), `ProjectSettings/AppLovinInternalSettings.json` | `USE_MAX` | V |
| AdMob (GMA) | `Assets/GoogleMobileAds`, `GoogleMobileAdsPlugin.androidlib` | `MAX_USE_ADMOB` = AdMob bridge under MAX (`AdsMaxUseAdmob`: banner/collapsible/app-open/native); `USE_ADMOB` standalone (not defined) | V |
| IronSource | `AdsIronSource.cs` | `USE_IRONSOURCE` (not defined) | V |
| Adjust | `Assets/Adjust` (asmdef), `Resources/AdjustSettings.asset` | `USE_ADJUST` | V |
| Solar Engine | `SolarManager.cs` | `USE_SOLAR` (not defined) | V |
| Firebase | UPM tgz, `FirebaseManager.cs` | `USE_FIREBASE` (not defined) | V |
| BestHTTP Pro | `Assets/Best HTTP (Pro)` | Bounce server log/socket | I |
| Bounce SDK | `Assets/BounceSdk` (73 .cs), `BounceCommon` (art only), `BounceDev` (3 `*.Dev.cs` partial-class hooks) | `USE_BOUNCE_SDK` (ME) | V |
| Unity IAP 5.x | `IAPManager`, `IAPCatalog`, `Resources/IAPProductCatalog.json`, `BillingMode.json` | always | V |

### 5.2 Initialisation order (V `BounceSdk.cs`, `SplashScene.cs`, `SplashScene.Dev.cs`)
1. Build index 0 = `Assets/BounceSdk/BounceSdk/Scene/Splash.unity`: studio logo (2 s) then loading bar (5 s).
2. `PopupPrivacy.CheckNeedShow()`: first launch shows the privacy popup; **after accept** `GameInit()` -> `BounceSdk.InitOnStartup()` (also `[RuntimeInitializeOnLoadMethod(AfterSceneLoad)]`, idempotent via `isInitialized`).
3. `InitOnStartup`: PlayerPrefs session counters -> `BounceConfig.Init` (iOS id swap, dev test ad ids, trims all strings) -> `RemoteConfig.Init` -> `BounceLog.Init` -> `AdjustManager.Init` (throws when token empty, Production env) -> `SolarManager.Init` -> `FirebaseManager.Init` -> `BounceAdsSdk.InitAds` (selects `AdsIronSource`/`AdsMax`/`AdsAdmob` by define, creates `BounceAppOpen` object) -> `BounceDebugPanel.Create()` in Editor/dev builds.
4. Next scene via `SplashScene.Dev.cs.InitSplashCompleteAndChangeToNextScene()` (default `LoadSceneAsync(1)`); game-side `GameMasterInit` then runs `InitSettings`, `InitSRDebug`.
5. MAX: `MaxSdk.InitializeSdk()`; formats (interstitial, rewarded, banner, app-open, MREC, AdMob bridge) initialise inside `OnSdkInitializedEvent`. Manual `SetHasUserConsent/SetDoNotSell` are commented out; consent is delegated to **MAX Consent Flow** (`consentFlowEnabled: true`, GDPR terms/privacy alert on, localized ATT strings on, in `AppLovinInternalSettings.json`). The standalone AdMob path has its own UMP flow and Adjust ATT request on iOS (`AdsAdmob.cs`). V settings; runtime behaviour I.

### 5.3 Keys handling
| Item | Where | Risk |
|---|---|---|
| Ad unit ids, Adjust tokens, IronSource/Solar keys | `Assets/Resources/BounceSdk/Bounce.BounceConfig.asset` **tracked** | ids are public-by-design but pipeline should load production ids from an ignored config. V |
| MAX SDK key default | string literal in `BounceConfig.cs` | hard-coded secret-like value. V |
| Keystores | `Upstore/*.keystore` tracked (ME 1, KT 2); `androidUseCustomKeystore: 1` | breaks `mobile-build-release`. V |
| Firebase config | `StreamingAssets/google-services*.json`, `FirebaseApp.androidlib` tracked | normal, but unused (define off). V |

### 5.4 Analytics events (V `LogHelper.cs`, `BounceSdk.cs`, `AdsHelper.cs`, `AdsPlacement.cs`)
| Layer | API | Notes |
|---|---|---|
| Transport | `BounceSdk.LogEvent(name, k, v, ...)` -> `BounceLog.Log("log_evt", ..., "eventName", name)`; `LogAds(type, state, placement)` -> `log_ads` (0.3 s spam debounce); `LogAdsRevenue`, `LogIAPSuccess` | gated by `isInitialized` and `RemoteConfig.CONFIG.logEnable`; interstitial show / rewarded show+complete also fire Firebase `ad_*` names (no-op here) |
| Game wrapper | `LogHelper`, `AdsHelper.LogEvent` | Editor: coloured `CodeSketchDebug.Log` only; device: real call (`#if !UNITY_EDITOR && USE_BOUNCE_SDK`) |
| Events seen | `{minigame}_{world}_Checkpoint` (`Checkpoint_Index`, `world`, `minigame_title`; fired once per world per higher index using a persisted max), `payment_start/done/fail` (`iap`), `trail_purchase`, `aura_purchase`, IAP success with mode/world/checkpoint params | 12 call sites in ME |
| Placement taxonomy | `AdsPlacement` int enum, `Feature_Screen_Action[_Rewarded/Close/Skip]`, ranges per feature (100s revive, 300-600 shop, 1000s per genre) | numeric ids stable for server logs |
| Naming | mixed snake_case events, PascalCase params; no central taxonomy file | I |

`AdsHelper` policy: `IsAdsRemoved = NoAdsPurchased || Subscription_VIP.RemoveAds`; `MinimumInterstitialLevel = 10`; enum and string placement overloads; `Action<bool>` reward callback; Editor grants reward instantly; debug skip flags honoured. `AdsBreak_Static` shows a No-Ads popup after every 3 completed interstitials (counters reset on `SubsystemRegistration`). V

## 6. ProjectSettings and build configuration

| Setting | KT | ME | Tag |
|---|---|---|---|
| Bundle id, version | `com.Speed.Keyboard.Parkour.Escape`, 1.16 / code 16 | `com.Monkey.Obby.Master.Escape`, 1.9 / code 9 | V (bumped by hand, commit "Build vX") |
| Min / target SDK | 24 / 36 | 25 / 36 | V |
| Backend / arch | IL2CPP, ARM64 only (`AndroidTargetArchitectures: 2`), no APK split | same | V |
| Stripping | High (4) on Android | default | V |
| R8 minify | release + debug on | same | V |
| API compat | .NET Standard 2.1 | same | V |
| Android entry | Activity | GameActivity (explains ME hardware-accel postprocessor) | V/I |
| Custom templates | main manifest, `mainTemplate.gradle`, `baseProjectTemplate.gradle`, `settingsTemplate.gradle`, `gradleTemplate.properties`, `proguard-user.txt` | same + `ThunderAdsNative.java` | V |
| Android defines | `ODIN_INSPECTOR*`, `CODESKETCH_ODINSERIALIZER`, `KAMGAM_UGUI_WORLD_IMAGE`, `USE_MAX`, `MAX_USE_ADMOB`, `USE_ADJUST`, `DOTWEEN`, `DREAMTECK_SPLINES`, `AGENTS_NAVIGATION_LOG_NONE`, `CODESKETCH_APPSTORE` | same minus Dreamteck, plus `USE_BOUNCE_SDK` | V |
| Quality | level "Mobile": URP asset, 2 pixel lights, shadow distance 40, MSAA off, vSync 0 (only the first level was read) | same URP asset guid | V |
| Scenes in build | 48-line `EditorBuildSettings.asset`: Splash (SDK), Home, minigame world scenes (`..._Optimized` variants), one in `_Parkour3d/Scenes` | 30 lines: Splash, Home, `Minigame_WukongEscape[_2.._4]` | V |
| Scene variants | `Minigame_*_W1` source vs `*_Optimized` baked/combined (build uses Optimized) | `Test`, `Test_Portal` kept in repo | V |
| Unity 6 Build Profiles | not checked | not checked | I (unverified) |
| Build automation | none seen: no BuildPipeline script, `.github/` is ignored; human builds in Editor | same | V (no builder in Editor folders) / I |
| Addressables | groups: Default Local, Built In Data (KT), Localization-Assets-Shared, Localization-Locales, 9 string-table groups; no remote content | same minus Built In | V |

## 7. Git, folders, naming

- **Remote**: Bitbucket `bounce2020/knife-tower`, `bounce2020/monkey-escape`. Branches: `main`; KT `game/speed-keyboard-escape` (active), `game/keyboard-escape-craft`, `art/speed-keyboard`, `art/craft-keyboard`, `keyboard-ios`, `speed-keyboard-event`, personal `hieu`; ME `control-testing`, `ios`, `Heavenly-Steed`, personal `hainx`. Pattern `game/<x>`, `art/<x>`, platform branch, personal. V
- **Commits** (KT 1839, ME 364): terse prefixes `*` fix/tweak (422 KT), `+` add (354), `Build vX.Y`, `UPDATE:`, `TWEAK:`, `add:`; about 1050 KT messages are empty or ".". Merge commits from pulls. Version bump is its own commit. V
- **.gitignore** (same in both): Unity standard, `.github/ .kiro/ .gemini/ GEMINI.md`, `*.csproj/*.sln`, Addressables `*.bin*` + `StreamingAssets/aa`, `Assets/Plugins/Android/*.jar|*.aar` (EDM4U rebuilds), vendor demos, **`ProjectSettings/ProjectVersion.txt`**. No `.gitattributes`, no Git LFS. V
- **Folders**: `Assets/_Game` = Audios, Configs, Fonts, Localization, Material, Materials, Prefabs, Resources, Scenes, Scripts, `_Meshes` (KT) / `_Meshs` (ME), `__Resource` (KT) / `__Resources` (ME), `_Optimized` (KT). Art roots `_Art` (2D/3D/Fx/Shader/Skyboxes), legacy `_ARTs`, KT-only `_Game_Extensions`, `_Parkour3d`, `_Escape3d`, `_ROOT`. Both `Material` and `Materials` exist in both projects. Rule: keep each project's own spelling. V
- **Scripts**: `Core, Data, Editor, Event, Factory, Logic/<Feature>` (+ `Utilities` KT, `Device` ME). `namespace Game` is also used outside `_Game` (`_Game_Extensions`, `_ARTs/Scripts`, `_Art/**/RopeLoopAnimation.cs`). V
- **Resources**: `Assets/Resources` = SDK/system assets only (BounceSdk config, DOTweenSettings, IAP catalog, GDK); CodeSketch singletons in `_Game/Resources/CodeSketch/ScriptableObjectSingletons`. V
- **Localization**: 9 locales (ar-EG, ar-SA, en, es-MX, ja-JP, ko-KR, tr, uk-UA, vi-VN); one table `LOCALIZE` + shared data in `_Game/Localization/Tables`; each locale table is an Addressables group; code side `LocalizeKey` (const strings), `Factory_Localize`, `Factory_Localize_Font`, `Factory_Localize_Number`, `Data_Localize`, `Localize_TMP_Text(_Format)`, `Localize_TMP_Font`; RTL via RTLTMPro. V
- **Input actions**: `Assets/InputSystem_Actions.inputactions` is the stock Unity template in both (Move/Look/Attack/Interact/Crouch/Jump/Sprint...); mobile control = joystick pack + legacy `Input`. V/I

## 8. Assembly definitions and compile time

- Facts: 0 first-party asmdefs. KT has 713 `_Game` + about 180 other first-party .cs (`_Game_Extensions`, `_ARTs`, `_Parkour3d`, `_Escape3d`) in `Assembly-CSharp`. Third parties are already isolated (MaxSdk, Adjust, BestHTTP, Graphy, A*, Dreamteck, ProjectDawn, OmniShade, Odin modules); `com.codesketch` ships its own asmdefs (`CodeSketch`, `.Audio`, `.Data`, `.Patterns`, `.Editor`, SRDebugger). V
- Compile cost: any `_Game` edit recompiles all first-party code (about 900 files in KT). The DLL is small (1.8 MB); Hot Reload is installed in both. No timings measured. I: the real cost is domain reload with Odin + IL2CPP plugins, not C# compile; not a blocker below about 300 files.
- Constraints on a split (I, from code): (1) off-folder code uses `namespace Game` and game types, so it must join the same assembly; (2) `Assembly-CSharp` cannot be referenced by asmdefs, and `BounceDev`/`SplashScene.Dev.cs` call into `Game`, so a Bounce asmdef must not reference Game (use a callback registered by Game); (3) Odin-serialized or `[SerializeReference]` data stores assembly-qualified type names, so moving types between assemblies later can break saved assets; (4) `[RuntimeInitializeOnLoadMethod]` keeps working.
- Safe split (do at project start, never mid-production):
  1. `Game.Core` (Core, Utilities, Data, Event, Factory): refs CodeSketch/SketchEngine, UniTask, PrimeTween, TMP, Addressables.
  2. `Game.Logic` (Logic/**): refs Game.Core + MaxSdk/Adjust asmdefs; SDK wrapper in its own asmdef without a Game reference.
  3. `Game.Editor` (editor-only platform): refs Game.Logic + `Sirenix.OdinInspector.Editor`.
  4. `Game.Tests.EditMode` / `PlayMode`.
  Keep `autoReferenced: true`, use `versionDefines` for optional SDKs, measure compile before/after.

## 9. Risks the pipeline should avoid

| Risk | Evidence | Tag |
|---|---|---|
| Secrets/signing material in git | keystores, BounceConfig asset, MAX key literal | V |
| `ProjectVersion.txt` ignored (editor mismatch) | `.gitignore` | V |
| Floating `com.codesketch#main` | manifest | V |
| Migration code left in `InitializeOnLoadMethod` | `Add_VIP_Jackpot_Benefit` | V |
| Runtime script inside an Editor folder | `ParticleGrassField` | V |
| No LFS, no local batch runner, manual `Build vX` commits | repo | V |
| Firebase installed but disabled; `LogEventFirebase` body commented | `AdsHelper.cs` | V |
| Debug code not individually `#if`-gated | Debug folder | V/I |
| Typos baked into names (`DebugCurrenyCup`, `Monitize`) | filenames | V |

## 10. Proposed classification

| Candidate | Type | Proposed name | Must-haves |
|---|---|---|---|
| Splash + SDK init order (privacy -> config -> remote cfg -> log -> Adjust -> ads) | RECIPE | `sdk-init-pipeline` | Splash scene index 0; consent gate before SDK init; idempotent `isInitialized`; partial-class `*.Dev.cs` hook for game init and next scene; define-symbol checklist (`USE_MAX`, `USE_ADJUST`); Editor mock path for every SDK |
| `AdsHelper` facade + `AdsPlacement` int enum | SKILL (extend) | `monetization-integration` | single static facade, gameplay never touches SDK; placement enum `Feature_Screen_Action` with per-feature number ranges; Editor fallback = instant reward + log; `IsAdsRemoved` = IAP OR VIP; interstitial min-level, cooldown, No-Ads popup after N |
| Analytics wrapper (log-only in Editor) | RULE | `analytics-events-taxonomy` | snake_case events and params; persisted-max once-per-milestone pattern; `#if !UNITY_EDITOR && USE_x` real call + Editor log; `docs/analytics-events.md` as single source; IAP/ad events carry mode + world + checkpoint |
| Consent/ATT/GDPR via MAX Consent Flow (+UMP for AdMob) | RULE | `consent-compliance` | enable MAX consent flow and localized ATT strings; first-launch privacy popup before init; never hard-code consent true; privacy URL set; kids audience changes SDK choice (human decides) |
| Secrets and signing hygiene | RULE | `secrets-signing-hygiene` | keystores outside repo; production ids from ignored config or local batch runner; no key literals in source; track `ProjectVersion.txt`; secret scan before commit |
| Debug layer (DebugButton/DebugToggle, skip flags, fake IAP, subscription hotkeys) | SKILL (extend) | `debug-cheats-menu` | Data-bound toggle base; persisted ad-skip flags; fake IAP through real handler; whole layer `#if DEVELOPMENT_BUILD \|\| UNITY_EDITOR`; reset-save with confirm + "cheated" flag; hotkeys Editor-only |
| Subscription lifecycle test matrix | RECIPE | `iap-subscription-testing` (in `unity-iap-port`) | 9 states (trial, paid, cancel, trial->paid, renew, resubscribe, expire, refund, wipe); Editor-only APIs; assert entitlement after each |
| Editor tool conventions | SKILL (extend) | `editor-tool-authoring` | one menu root `Tools/Game/<Feature>`; dry-run + counts + Undo; never `[InitializeOnLoadMethod]` for migrations; no runtime code in `Editor/`; Odin optional; `EditorPrefs` for last paths |
| AudioConfigGenerator | TOOL | `tool-audio-config-generator` | clips -> one config SO each; prefix/folder prefs; skip existing; output `Configs/Audio/Sfx`; adapter for installed audio framework |
| PrefabReplace + MaterialCollector + material finder | TOOL | `tool-greybox-to-prefab` | name-prefix match; keep prefab link; marker on old objects; move materials by GUID; strip missing scripts; report counts |
| ColliderExtractor | TOOL | `tool-collider-extractor` | clone non-trigger BoxColliders into child "Collider"; honour skip-combine tag; prefab asset and scene; run before mesh combine |
| Localize_GlyphPreloader | TOOL | `tool-tmp-glyph-preloader` | keys x locales loop; per-locale font factory; Arabic shaping; export required chars; flip atlas to Static and save |
| Nav link creators | TOOL | `tool-nav-link-creator` | scene-view click start/end; wrapper component; one-way flag; remap; preview |
| Character_Component_Copy_Tool | TOOL | `tool-rig-component-copy` | node-path mapping; two-pass create then resolve joints; serialized-property copy |
| Hardware-accel manifest postprocessor | RECIPE | `android-gradle-postprocess` (in `mobile-build-release`) | `IPostGenerateGradleAndroidProject`; `callbackOrder = int.MaxValue`; throw if node missing; Activity vs GameActivity; document reason |
| Android build baseline | DATA | `android-baseline-settings` | IL2CPP ARM64; target SDK 36; min 24-25; R8 on; custom manifest + gradle templates; High stripping only after `link.xml` test; define checklist |
| Package baseline | DATA | `package-baseline` | Unity 6000.0/6000.3; URP 17.x; UGUI 2.0.0; Addressables 2.9.1; Localization 1.5.12; Cinemachine 2.10.7; Input System 1.19-1.20; IAP 5.4.x; UniTask + PrimeTween + Odin + CodeSketch/SketchEngine pinned by hash |
| Git conventions | RULE | `git-conventions` | branches `game/<x>`, `art/<x>`, `main`; prefixes `+`, `*`, `Build vX.Y` with real messages; track `ProjectVersion.txt`; LFS for binaries; no keystores/secrets; version bump separate |
| asmdef split | RECIPE | `asmdef-split` (in `unity-project-bootstrap`) | decide at project start; `Game.Core/Logic/Editor/Tests`; SDK asmdef never references Game; pull off-folder `namespace Game` code in first; beware Odin/SerializeReference type names; measure before/after |
| Localization setup | RECIPE | `localization-setup` | single table `LOCALIZE`; `LocalizeKey` const class; font factory per locale; RTLTMPro for Arabic; glyph preload before build; Addressables group per locale table |
| Scene variants (`X` source vs `X_Optimized` baked) | RULE | `scene-variant-convention` | source scene stays authoring; only `_Optimized` in Build Settings; bake via tool; never hand-edit baked scene |
