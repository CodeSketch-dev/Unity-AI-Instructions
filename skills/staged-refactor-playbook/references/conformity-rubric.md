# Conformity rubric (generic, copy per project)

Pass/fail checklist for a refactor toward the studio architecture. Weights: blocker 5, major 3, minor 1. Scoring and the gate verdict are in `../SKILL.md` section 4. Each project keeps its own copy with two extra columns, Status (P/F/U) and an evidence note per item; U (unknown) counts as fail until its verify command was run.
Commands are file-only (grep/find/python) unless marked Editor. Budget 0 means the count must be 0.


## 1. Folders and layout

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| F01 | Assets/_Game holds first-party content only; imported sub-projects and vendor packs live outside it (Packages Fx / Packages Required / Plugins). | list _Game top folders; any folder with its own Scenes/Prefabs/TextMesh Pro copy = fail | major |
| F02 | _Game top level limited to Audios, Configs, Fonts, Localization, Materials, Prefabs, Resources, Scenes, Scripts (+ Textures, Settings, Tests if real content). | `ls Assets/_Game` compared with the list | major |
| F03 | Feature content is under Prefabs/<Feature>, Configs/<Feature>, Audios/<BGM|Sfx>/<Feature>, never at the _Game root. | `ls Assets/_Game` shows no feature-named folder | major |
| F04 | Exactly one source-art root `_Art/{2D,3D,Fx,Shader,Skyboxes}`; no `_ARTs`, `_Game/_Art`, `Skybox` spelling drift. | `ls Assets | grep -i art`; `ls Assets/_Game | grep -i art` | minor |
| F05 | Scripts buckets are only Core, Data, Editor, Event, Factory, Logic (+ Utilities if used). | `ls Assets/_Game/Scripts` | minor |
| F06 | Every feature has one folder `Logic/<Feature>/` and every minigame one `Logic/Minigame/<Name>/` (3-letter prefix), including the Home hub; no feature scattered over 5+ unrelated folders. | `ls Assets/_Game/Scripts/Logic`; count folders touching one game | major |
| F07 | No near-duplicate code trees: two feature folders with >= 30% same-name files at >= 90% line similarity are merged into one base + config. | `python -I` script: same-name files across Logic/* with difflib ratio; budget 0 pairs | blocker |
| F08 | Resources contains only framework singleton assets and SDK config (no prefabs). | `find Assets -path '*Resources*' -name '*.prefab'` must be empty | major |
| F09 | No duplicate folder spellings (Audio/Audios, Material/Materials, __Resource/Resources). | `ls Assets/_Game` diff names case-insensitive/plural | minor |
| F10 | No scratch/tool folders in Assets (_Tmp*, _AiQa, Backup~, Assets/ProjectSettings, Readme.asset, stray screenshots). | `ls Assets`; `find Assets -name 'Backup~'` | minor |

## 2. Asmdefs, namespaces, naming

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| N01 | First-party code compiles in the default assemblies, a custom runtime asmdef only carries a real references list; editor code sits in Editor folders; EditMode and PlayMode test asmdefs exist (a runtime asmdef only with a real references list; editor code in Editor folders; test asmdefs required). | `find Assets/_Game -name '*.asmdef' | wc -l`; share of .cs files covered | major |
| N02 | No asmdef cycles; compile of all asmdefs is clean. | Unity Console after refresh; `tests-run` compile | blocker |
| N03 | First-party namespace is `Game` for >= 95% of runtime files; no per-game namespaces. | `grep -rl '^namespace Game'` count vs total; list others | minor |
| N04 | File name == primary type name for every .cs. | script: first type name vs file stem; budget 0 | major |
| N05 | One top-level type per file (tiny event/enum classes included). | script: top-level types per file; budget 0 | major |
| N06 | Uniform prefixes: `Data_`, `Factory_`, `Event_<Feature>_<Noun>_<Verb>`, `<Feature>_Asset`, `_Static`, `_Type`, `_Component`; no `Evt_`, project-initial variants or `_Factory` suffix. | `grep -rl 'class Evt_\|class .*Kt_\|class .*_Factory'` budget 0 | major |
| N07 | Private methods carry no `private` keyword; private fields `_camelCase`; constants UPPER_SNAKE. | grep `private` methods, budget < 2% | minor |
| N08 | All comments, identifiers and docs in English. | grep non-ASCII letters in `*.cs` comments | minor |
| N09 | No `using UnityEditor` in runtime code outside `#if UNITY_EDITOR`. | grep `using UnityEditor` in runtime folders, check guard | major |
| N10 | SketchEngine namespaces/APIs only (no `CodeSketch.*`, no re-implemented DataBlock/StaticBus/Mono base). | `grep -rl 'using CodeSketch'` budget 0; manifest has com.sketchengine | major |
| N11 | Exactly one tween library (PrimeTween) and one async lib (UniTask). | `grep -rl 'using DG.Tweening'` budget 0 | minor |
| N12 | Partial classes only for generated code; no `Type.Part.cs` sprawl in gameplay. | `find -name '*.*.cs'` review | minor |

## 3. Scene roots and GameSingleton

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| S01 | One `GameSingleton` prefab (MonoSingleton, persists across scenes, no logic) placed in the boot scene and every gameplay scene. | grep prefab GUID in each text `.unity`; open binary scenes in Editor | major |
| S02 | GameSingleton children are only cross-scene services (EventSystem, pools/IAP/fps manager, HUD canvas, popup canvas, loading, internet, native slot, transition); no camera, listener or world content. | prefab YAML grep `!u!20`, `!u!81`, `!u!82` = 0 | major |
| S03 | Secondary persistent UI singletons (focus, toast, popups) are spawned once from a prefab reference in the registry factory (or placed in the persistent root) under the global canvas, never `new GameObject`. | grep the creators of persistent overlays; each loads a prefab from the registry | major |
| S04 | Scene roots <= 20, each a prefab instance or a named container; no tool-marker roots (`_MapNarrowApplied` etc.). | `python -I` YAML root count; names starting `_` flagged | major |
| S05 | No runtime creation of managers, world pieces or UI pages: `new GameObject`/`AddComponent`/`Resources.Load` total in Logic <= 10, all whitelisted (combiners, pooled FX). | `grep -rc 'new GameObject\|AddComponent<\|Resources.Load' Assets/_Game/Scripts/Logic` | blocker |
| S06 | Scenes are Force Text serialized. | `head -c 20 file.unity` starts `%YAML` | major |
| S07 | Each scene <= 5 MB (geometry lives in prefabs/baked assets). | `find Assets -name '*.unity' -size +5M` | major |
| S08 | 0 missing scripts in every scene (no `m_Script: {fileID: 0}`). | `grep -c 'm_Script: {fileID: 0}'` on scenes; Editor reopen | blocker |
| S09 | Only Build Settings scenes exist; no backup/test/unreferenced scenes in the repo. | list `*.unity` not in EditorBuildSettings | minor |
| S10 | Every scene plays alone (duplicate GameSingleton self-destroys; boot order Splash->Home documented). | Play each scene, Console empty | minor |
| S11 | MonoBehaviour density <= 2 per GameObject in scenes; per-GO helpers folded into prefab roots or baked. | `python -I` scene stats | minor |
| S12 | Every static cache/registry has a `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` reset. | grep `static .*(Dictionary|List|HashSet)` vs attribute in same file | minor |

## 4. Map / level as prefab

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| M01 | Every map, level, chunk, biome is a prefab placed in the scene under a named container; nothing is spawned from a path string. | grep `resourcePath`, `Resources.Load`, `LoadAsync` in map code = 0 | blocker |
| M02 | Map data assets hold prefab references, not path strings. | grep `string .*[Pp]ath` in `*MapLayout*` | major |
| M03 | Baked/generated meshes are binary or FBX (not YAML text) and mesh-compressed. | `head -c 12` of mesh `.asset` must not start `%YAML` | major |
| M04 | No generated mesh > 20 MB or > 200k vertices; large cells are split. | `find Assets/_Game -name '*.asset' -size +20M` | major |
| M05 | Every generated mesh/asset is referenced (0 orphans after a bake; builders delete stale output). | GUID scan: unreferenced files under Meshes | major |
| M06 | Static decor is combined at edit time per material by a combiner prefab; dynamic/animated excluded (Tag_SkipMeshSceneCombiner). | combiner prefab present in scene; renderer count per scene | minor |
| M07 | Map prefab roots carry the per-zone far-clip/culling component; prefab nesting depth <= 8. | `python -I` prefab stats script | minor |
| M08 | Editor builders are idempotent and write prefabs (not scene-only objects); a second run yields 0 diffs. | run builder twice, `git status` clean | major |

## 5. Prefab organisation

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| P01 | 0 missing scripts in every prefab. | `grep -rl 'm_Script: {fileID: 0}' Assets/_Game --include=*.prefab` | blocker |
| P02 | 0 broken GUID references (scenes, prefabs, assets, materials). | GUID scan (`lean-asset-audit` guid index) lists refs to missing GUIDs | blocker |
| P03 | No duplicate prefabs: same name+size or >= 99% identical copies become variants/nested prefabs of one source. | `find -name '*.prefab' -printf '%f %s\n' | sort | uniq -d` | major |
| P04 | Prefab root name == file name; prefix by feature. | script: root m_Name vs file stem | minor |
| P05 | Scene instances carry no unintended overrides (overrides report empty or documented). | Editor `PrefabUtility.GetObjectOverrides` over scene roots | minor |
| P06 | No first-party prefab > 2 MB. | `find Assets/_Game -name '*.prefab' -size +2M` | minor |
| P07 | Managers/systems are prefabs in Prefabs/<Feature>/ placed in scene; no scene-only manager GOs with scripts directly. | root GOs with MonoBehaviour and no prefab link | major |

## 6. Camera

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| C01 | Exactly one CinemachineBrain in game content, inside the player camera prefab. | grep Brain script GUID over `.unity` and `.prefab` (count 1 outside vendor) | major |
| C02 | Camera rig (Camera, Brain, FreeLook, FollowTransform, Shaker) is one prefab nested in the player prefab. | prefab YAML tree | major |
| C03 | One AudioListener and one MainCamera-tagged camera at runtime. | Play: `FindObjectsByType<AudioListener>` count 1 | major |
| C04 | Camera shake and flyover go through the single camera manager/shaker; no per-game camera copies. | grep `class .*Camera.*Shak` budget 1 | minor |
| C05 | Overlay cameras for preview/gacha use the URP camera stack, no second Brain. | Camera component list | minor |
| C06 | One Cinemachine API generation in the project (v2 or v3) matching the package. | manifest version vs `using Cinemachine` / `Unity.Cinemachine` | minor |

## 7. UI page, item, popup

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| U01 | UI pages and popups are prefabs registered in the prefab registry factory / popup manager; scenes hold no hand-built pages and code builds no Canvas. | grep `new GameObject(.*Canvas` and `AddComponent<Canvas>` in Logic = 0 | blocker |
| U02 | List/grid rows are item prefabs spawned (pooled) into a ScrollRect. | review ScrollRect content creation | major |
| U03 | One shared shop prefab; per-game differences are data sources only. | `find -name '<Shop prefab>*.prefab'` count 1 | blocker |
| U04 | One shared currency-bar prefab, icon overhangs the frame; no hand-built bars. | prefab count 1; UI audit currency-bar rule reports 0 | major |
| U05 | Persistent canvases have fixed sort orders (HUD, popup above HUD, transition top). | prefab canvas sortingOrder | minor |
| U06 | Every TMP text has UI_TextAutoFit, outline, no ellipsis; layout audit reports 0 violations. | `Game.UiAuditBatch.Run()` totals | major |
| U07 | Every button has the press animation; reward buttons the pulse. | `Qa_PressAnim` | minor |
| U08 | Raycast Target off on non-interactive graphics; static and dynamic UI on separate canvases. | audit script over UI prefabs | minor |
| U09 | No hard-coded user-visible strings; keys in Localization tables. | grep `.text = "` in Logic | major |
| U10 | UI naming follows Root/Board/Frame/Btn_/Text_/Icon_. | prefab name regex audit | minor |
| U11 | One TMP default font/atlas; no duplicate font assets; no atlas > 8 MB. | `find -name '*SDF*.asset' -size +8M`; duplicate names | minor |
| U12 | UI is authored in Edit Mode on the source prefab; runtime only shows/hides/fills data. | grep runtime `.sprite =` / sizeDelta restyle in UI code | major |

## 8. Data, factory, event, state, pool, collision, async

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| D01 | Persistent state is `Data_*: DataBlock<>` with `DataValue<>`; no PlayerPrefs or parallel JSON save. | `grep -rl PlayerPrefs` budget 0 (SDK excluded) | major |
| D02 | Data classes live in Scripts/Data and hold no scene objects. | Data files with UnityEngine.Object fields | minor |
| D03 | Each `Factory_X` singleton class has exactly one asset and vice versa. | script: class list vs asset list (`comm`) | major |
| D04 | Factories expose static read-only properties; lookup dictionaries built in OnInitialize; ids validated. | review Factory files | minor |
| D05 | Authored entries are `<Feature>_Asset` ScriptableObjects under Configs/<Feature>/. | asset folder listing | minor |
| D06 | Cross-feature notifications use `Event_<Feature>_<Noun>_<Verb> : IEvent` in Scripts/Event/<Feature>/ via StaticBus; one class per file. | `grep -rL 'IEvent' Scripts/Event`; classes per file | major |
| D07 | Subscribe/Unsubscribe balanced per class and matching lifetime. | script lists unbalanced files | major |
| D08 | No second event system beside StaticBus (C# static events, SO channels) except one-to-one owned. | grep `static event` in Logic | minor |
| D09 | Runtime modes use StateMachine<TEnum>; states in State/; transitions via one owner method. | state folders; grep bool-flag modes | minor |
| D10 | Repeated spawns use PoolPrefabGlobal + PoolPrefabConfig; raw Instantiate in <= 20 files, none in Update paths. | `grep -rc 'Instantiate(' Logic` | major |
| D11 | Collisions via OptCollisionRegister/sensor; raw OnTrigger/OnCollision only on the sensor owner; no GetComponent in callbacks. | `grep -rn 'void OnTrigger\|void OnCollision'` review | major |
| D12 | Async uses UniTask with cancellation; `async void` 0; new `StartCoroutine` 0. | greps, budget 0 | major |
| D13 | FindObjectOfType / GameObject.Find in runtime <= 3 files, none per-frame. | `grep -rl 'FindObjectOfType\|GameObject.Find\|FindFirstObjectByType'` | minor |
| D14 | Update/FixedUpdate only in managers or few-instance classes; large populations tick through one manager. | count files with Update; Profiler script stats | minor |
| D15 | No LINQ, string building or Camera.main in per-frame code. | grep in Update bodies | minor |
| D16 | Physics: autoSyncTransforms off, reuseCollisionCallbacks on, tight layer matrix, NonAlloc queries. | read DynamicsManager.asset; grep `Physics.*All(` | minor |

## 9. Services

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| V01 | Internet check: remote flag, two fallback endpoints, GET not HEAD, minimum retry feedback, bypass for no-ads/VIP; popup is a cover not a state flag. | review + Play with network off | major |
| V02 | Ads go through one facade (AdsHelper); gates: internet, no-ads/VIP, tutorial, SDK-owned cooldown; no direct SDK calls from gameplay. | `grep -rl 'MaxSdk\.\|Admob'` outside Ads folder budget 0 | major |
| V03 | One global banner service (15 s refresh, re-show after native/scene load). | review Ads_Banner | minor |
| V04 | Rewarded reward is granted only in the completion callback; failure path shows a toast. | review + Play with mock ad | major |
| V05 | IAP: one IAPManager + catalog json; restore works; purchase success logged once; parental gate in front of money. | review; Play with test product | major |
| V06 | Analytics only through one LogHelper facade with a documented event taxonomy. | grep direct Firebase/Adjust calls outside facade | minor |
| V07 | Rating popup: after N sessions/wins, once per version, native review API. | review + data flag | minor |
| V08 | Settings (sound, music, haptics, language) live in one DataSettings-style block and persist. | Play: change, restart, value kept | major |
| V09 | One loading/transition service for all scene loads; no direct `SceneManager.LoadScene` in gameplay. | `grep -rl 'SceneManager.LoadScene'` only in loader | major |
| V10 | DevicePolicy tiers at runtime: one Quality level, Mobile and PC URP assets, low-end switches (render scale, shadows, far clip). | QualitySettings count 1; policy file | major |
| V11 | Frame rate set once (min(refresh,60)); vSync 0. | grep `targetFrameRate` count 1 | minor |
| V12 | Save safety: atomic write, version/migration, old save loads in a test. | EditMode migration test | major |
| V13 | Debug/cheat menu excluded from release builds (define or Development only). | grep DebugPopup build gate | major |
| V14 | Consent/privacy (UMP/ATT) runs in boot before ads init; privacy link in Settings. | Play boot on fresh install | major |
| V15 | Toast/warning and haptics each have one facade. | grep duplicate toast classes | minor |
| V16 | Offline/free-cash/reward popups queue through the popup manager and are claimable by tap for QA. | Play check | minor |

## 10. Tutorial focus

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| T01 | Focus Msg and Focus Pointer exist once as prefabs (placed under the popup canvas of the persistent root, or referenced from the registry factory), each a persistent singleton, shown and filled with data at runtime. | `find -name '*Focus*.prefab'` count 2; callers use the one shared API | major |
| T02 | Tutorial steps are data-driven (phase/step assets), never hard-coded UI paths. | step lists live in assets | major |
| T03 | Focus hole = 4 dim panels around a target rect tweened 0.35 s OutSine; outside blocks input, target click-through only when configured. | Play step through, raycast check | minor |
| T04 | Tutorial completion is persisted in a Data_* block; every step skippable and restart-safe. | fresh vs finished save Play | major |
| T05 | Banner/native overlays never cover the focus message. | Play screenshot at 1920x1080 | minor |
| T06 | One hand sprite and one pulse tween helper shared by all hints; no per-game tutorial prefab copies. | `find -name 'Hand*.png'`; tutorial prefab dup check | minor |

## 11. Tests and QA gates

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| TS01 | Full EditMode suite green; PASS and SKIP counts recorded before and after each refactor batch. | `tests-run` EditMode, compare counts | blocker |
| TS02 | Static-check tests: no missing scripts, factory<->asset 1:1, file==class, no tracked generated folders. | tests exist under Tests/ with those names | major |
| TS03 | Play smoke per scene: 5 s, empty Console, no exceptions. | Play + `console-get-logs` | major |
| TS04 | Repeated scene-flow test (Home->game->Home x N) shows no leaks or duplicate singletons. | soak test | major |
| TS05 | Studio QA gate and UI audit reports exist and are fresh for the batch. | `docs/reports/qa-latest.*` newer than last change | minor |
| TS06 | Perf claims backed by profiler numbers (draw calls, GC, frame time) or marked not measured. | report contains numbers | minor |

## 12. Lean and junk rules

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| L01 | No derived/generated folder tracked or imported inside Assets (graph indexes, caches). | `git ls-files Assets | grep -i graphify | wc -l` = 0 | blocker |
| L02 | Unreferenced first-party assets <= 1% of Assets bytes (GUID closure scan, vendor excluded). | `lean-asset-audit/scripts/dead_assets_proof.py` | blocker |
| L03 | First-party Assets (excluding vendor packs) <= 800 MB. | `du -sm Assets/_Game Assets/_Art` | major |
| L04 | No first-party asset > 20 MB. | `find Assets/_Game Assets/_Art -size +20M` | major |
| L05 | Duplicates (same name and size > 10 KB) = 0 outside vendor. | `find ... -printf '%f %s\n' | sort | uniq -d` | major |
| L06 | Every manifest package is used (code or prefab GUID) or removed; no default module bloat. | package-usage script (namespaces and script GUIDs) | major |
| L07 | One nav stack, one tween lib; no transitive Entities chain unless used. | manifest and embedded packages review | minor |
| L08 | Vendor FX packs limited to the used closure (Packages Fx <= 200 MB). | closure scan of prefab/material GUIDs | major |
| L09 | Texture import: maxTextureSize set per folder (UI/FX <= 1024), Android ASTC override audited. | `.meta` scan; Editor platform overrides | major |
| L10 | Audio import: SFX CompressedInMemory and mono where possible; music streamed. | `.meta` loadType scan | minor |
| L11 | Git pack <= 1 GB; large generated data not stored as YAML text. | `git count-objects -vH` | major |
| L12 | `.gitignore` verified with `git check-ignore -v` for every new generated folder; metas tracked. | run per new folder | minor |
| L13 | Editor one-off tools pruned (each with a live menu use). | menu usage review | minor |
| L14 | No dead runtime classes or scripts (zero references). | class reference scan | minor |
| L15 | No stray root files or folders in Assets (images, Readme.asset, Assets/ProjectSettings). | `ls Assets` | minor |

## 13. Human maintainability

| ID | Rule | How to verify | Sev |
|---|---|---|---|
| H01 | Every feature has ONE obvious folder (`Logic/<Feature>/`, `Prefabs/<Feature>/`, `Configs/<Feature>/`) and one entry class named after it (`<Feature>` or `<Feature>_Master`); a newcomer finds it by name. | pick 10 features at random: folder found by name in < 1 min, entry class exists | major |
| H02 | No source file > 400 lines unless listed in a documented exception. | `find Assets/_Game/Scripts -name '*.cs' | xargs wc -l | sort -n | tail`; count > 400 | major |
| H03 | No copy-pasted feature trees or forked minigames; shared base + config instead (extends F07). | see F07 | blocker |
| H04 | Generated or baked code/assets carry a header (`// GENERATED by <Editor tool>, do not edit`) and the Editor tool that regenerates them exists and is idempotent. | grep generated folders for header; run tool twice, diff 0 | major |
| H05 | No hidden runtime magic: runtime-created managers/UI, string-based lookups (`Find("name")`, `Resources.Load(path)`, `SendMessage`), reflection, `Type.GetType` only in a documented whitelist (`docs/ONBOARDING.md` section Exceptions). | grep counts of those APIs vs whitelist | major |
| H06 | Each minigame/feature folder has a short README.md (what it is, entry points, prefabs, events, configs), <= 40 lines. | `find Assets/_Game/Scripts/Logic -mindepth 2 -maxdepth 2 -type d` each has README.md | major |
| H07 | `docs/ONBOARDING.md` exists and in 10 minutes answers: main/boot scene, boot flow, where GameSingleton lives, how to add a minigame, a popup, a shop item, a config, an event; each answer links to a real file. | new-dev dry run: follow doc, add a dummy popup in <= 10 min | major |
| H08 | Assets named predictably: prefabs `<Feature>_<Part>`, configs `<Feature>_<Name>`, folders as the standard layout (F02-F04); no `New`, `Copy`, `Final`, `_old`, `Backup`, `test`, `tmp` in names. | `find Assets/_Game -iname '*copy*' -o -iname '*backup*' -o -iname '*_old*' -o -iname '*final*' -o -iname 'New *'` | minor |
| H09 | Dead code and dead assets = 0 (L02, L14 hold) and one-off Editor fixers are deleted after use. | see L02, L14, L13 | blocker |
| H10 | Scenes readable: <= 20 named roots, containers named `=== X ===` or by feature, no tool-marker roots (S04). | see S04 | major |
| H11 | Single path per concern: one shop, one popup system, one currency bar, one pool, one tween lib (no per-game variants of the same concept). | see U03, U04, N06, N11 | major |
| H12 | Every public manager/singleton has a one-line header comment naming its owner prefab and scene location. | grep singleton classes without `// Lives in` header | minor |
