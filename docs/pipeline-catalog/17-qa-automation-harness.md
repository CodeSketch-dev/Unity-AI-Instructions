# 17. QA automation harness: machine-checked Unity work and the fix-retest loop

Design report, 2026-10-15. Read-only research; nothing here was built or run in Unity. Tags: V = verified (read in a file or ran a command this session), I = inferred (design decision or knowledge of Unity/ivanmurzak behaviour, not confirmed here).

## 0. Goal and findings

Goal: an agent proves its own work with machines, loops fix -> retest without human nudging, UI comes out exact from one prompt, and compile errors, missing refs, broken wiring, console errors and perf regressions are caught by scripts, not by the user.

Verified facts that shape the design:
- V: The Unity MCP server `ai-game-developer` (ivanmurzak) FAILED to connect in this session (`ECONNREFUSED`), and ToolSearch for "unity" found no deferred tools. No real tool names could be listed. Section 1 therefore lists the tool families ivanmurzak documents (I) and a mandatory "discover, never invent" step. The same ECONNREFUSED forced a queued-work list in thunder-break-egg (11, N:443), so the harness MUST work file-first and degrade, not stall.
- V: Machine has Python 3.14.7 (`py -V`) and Unity editors `2022.3.62f3`, `6000.0.78f1`, `6000.3.22f1` under `C:\Program Files\Unity\Hub\Editor` (`Unity.exe` present for 6000.3.22f1). Batchmode is possible. Projects (knife-tower, monkey-escape, thunder-break-egg, ...) live under `C:\Unity\GitProject`. Which editor each project pins is I: read `ProjectSettings/ProjectVersion.txt` first.
- V: `~/.claude/settings.json` has no `hooks` block today (grep count 0). All hook wiring below is new.
- V: Existing reusable pieces: `unity-log-triage/scripts/summarize_unity_log.py` (124 lines), `ui-popup-from-demo/dump_prefab.py` (81, prefab RectTransform tree, no Unity), `multi-agent-coexistence/scripts/workspace_guard.py` (198), `project-context-map/scripts/unity_project_scan.py` (254), `economy-progression-design/scripts/simulate_economy.py` (54, pacing table), `ui-scroll-board/scripts/grid_fit.py` (58), `asset-transfer-closure/scripts/resolve_closure.py` (251, GUID closure). Skills `playmode-script-testing`, `done-means-wired`, `unity-qa-playtest`, `unity-mcp-workflow`, `mobile-perf-audit`, `unity-ui`, `ui-clone` describe checks in prose with no automation.
- V (11): thunder-break-egg already ships Editor diagnostics `Dev_SceneCapture`, `Dev_UiCapture`, Scan Missing Scripts, `Build_DataBlockRegistryGuard` (build gate), Full Game Audit / Progression / Route / Upgrade Loop simulations, and EditMode asmdefs (Audio, BotLogic, CarryPose, GameplayHud, ShopSkin, Treadmill); six unrelated Bot/HUD tests were red on 2026-10-13. Good seeds, not portable as-is.
- V (11): documented QA false negatives: `timeScale=60` (pet lifetime 0.7 s real), polluted save (false completion times), provisional constants in audits, temp constant `MAX_MOVE_SPEED=203` left live, "done" without Console/Play evidence. The harness encodes these as validity gates (section 8).
- V (08): KT has 0 first-party asmdefs (~900 files in Assembly-CSharp), so EditMode tests need a test asmdef referencing `Assembly-CSharp` indirectly; I: for projects with no asmdef, tests assembly can reference only asmdefs, so the harness needs either the safe split (08 section 8) or reflection-based tests. This is the main portability risk.
- V (skills): the current skills say "screenshot at 3 aspect ratios", "no overlap", "Raycast Target off" but give no thresholds or tool; the user's "UI must be exact from one prompt" currently depends on human review. Section 5 turns those rules into numeric checks.

## 1. Editor bridge: what the MCP can do (I) and how to degrade

Tool families the ivanmurzak Unity-MCP is documented to expose (I, from knowledge; names change by version, so the agent must list tools first, per `unity-mcp-workflow`):

| Capability | Typical tool family | Used by harness for |
|---|---|---|
| Refresh/recompile assets, compile status | assets refresh / script update-or-create | stage S1 compile gate |
| Console read (logs, filtered by type) | console get-logs | S1, S5, log triage |
| Scene/hierarchy query, component + serialized field read | scene get-data, gameobject find/get, component get | S3 wiring read-back |
| Create/modify GameObject, component, asset, prefab | gameobject/component/asset modify, prefab open/save | fixes |
| Execute arbitrary C# (`Script.Main`) | script execute | the universal probe: run validators in-Editor, reflection clicks, ProfilerRecorder reads |
| Run EditMode/PlayMode tests | tests run | S2/S4 (I: may time out; see 5.3 fallback) |
| Screenshot (Game view / Scene view / camera) | screenshot-* | S6 visual diff |
| Editor state (play/compile/dirty) | editor state / package / selection | gate before each mutation |

Rules (V from `unity-mcp-workflow`): list tools, confirm project+scene, read Console baseline, one short idempotent call each, save after each stage.

Degradation ladder (the harness must pick the highest rung that works and print it in the qa-report header):
1. MCP connected: all stages.
2. MCP down, Editor closed, Unity installed: headless batchmode (section 6): compile, EditMode tests, static scans, custom `-executeMethod` validators, `-batchmode` without `-nographics` for screenshot (I: needs a GPU context; `-nographics` gives no rendering).
3. No Unity at all: static-only (YAML scans, grep, python validators). Report "S1 compile NOT verified", never PASS.
A run that reaches only rung 3 can never mark a feature "done"; it yields `STATIC-PASS` (see 3.3).

## 2. Test pyramid for AI-built Unity games

Cheapest and most frequent at the bottom. Each layer has a cost class: C0 (<2 s, python, no Unity), C1 (<30 s, Editor/MCP or batch compile), C2 (1-5 min, Play Mode), C3 (5+ min, full smoke/perf).

```
                  L7 perf budget capture (C3)          -> numbers vs tier budgets
               L6 screenshot + image diff (C2)         -> aspect ratios vs reference
            L5 PlayMode smoke + input bot (C3)         -> boot..modes..exit, 0 exceptions
         L4 UI validator, rect math (C0 yaml / C1 runtime)
      L3 EditMode data/factory/economy tests (C1)      -> ids, assets, ranges, sims
   L2 static: missing refs by YAML, naming/folders, banned APIs, asmdef rules (C0)
 L1 C# compile via Unity + Console clean (C1)          -> the gate for everything above
```

### L1 Compile (C1)
- Trigger refresh through MCP (`assets refresh`) or batchmode `-quit -batchmode -projectPath P -logFile out.log`. Wait for domain reload; then read errors via Console or by running `summarize_unity_log.py` on the log (V, reuse: it already emits COMPILE-ERR first).
- Pass: zero `CSxxxx` errors; zero new warnings in files touched by the diff (I: compare to baseline saved at session start in `docs/qa/baseline-console.txt`).
- Cheap pre-check (I, C0): `dotnet build` is NOT reliable for Unity projects; skip. Optional: Roslyn syntax-only parse is not worth it; the PostToolUse hook uses a debounced refresh instead (section 7).

### L2 Static checks (C0, python, no Unity)
All read YAML/text under `Assets/`. Output JSON lines `{rule, severity, file, line, msg}` + exit code.
1. Missing script / missing reference scan (`qa_scan_refs.py`):
   - Parse every `.unity`, `.prefab`, `.asset` (text-serialized; V that bike-obby scenes are binary, so skip with a warning). Build GUID -> path map from `.meta` files (reuse `resolve_closure.py` / `reference-index` logic).
   - Missing script: a `MonoBehaviour` document whose `m_Script: {fileID: 11500000, guid: G}` has G absent from the map, or whose script meta exists but the `.cs` declares no class with that file name (I: Unity uses file-name == class-name).
   - Missing reference: any `{fileID: N, guid: G}` with G not in the map (ignore `guid: 0000000000000000e000000000000000` and `...f000...` builtin). For same-file refs (`{fileID: N}` with no guid) verify `&N` anchor exists in the document set. `m_CorrespondingSourceObject`/`m_PrefabInstance` nulls are ignored.
   - Null serialized field: C0 cannot know which fields are required. Use an opt-in attribute (I): `[RequireRef]` on fields, emitted into a generated `Library`-free sidecar by an Editor reflection pass (L3). In C0 only flag `{fileID: 0}` on fields listed in `qa/required-refs.json` (name patterns: `_button`, `_canvas`, `_config`).
   - Prefab-instance overrides pointing to removed objects: `m_Modifications` entries whose `target` fileID is not in the source prefab (I: needs prefab parse; severity warn).
2. Naming/folder lint (`qa_lint_layout.py`), rules from CLAUDE.md house style (V): new first-party content only under `Assets/_Game` or `Assets/_Art`; namespace `Game`; file name equals primary type; `Data_*` in `Scripts/Data`, `Factory_*` in `Scripts/Factory`, `Event_*` in `Scripts/Event/<Feature>`; private fields `_camelCase`; constants `UPPER_SNAKE`; no `.meta`-less new files; no files in `Assets/` root. Severity: error for folder/namespace, warn for name style.
3. Banned API grep (`qa_banned_api.py`), regex over `Assets/_Game/**/*.cs`, excluding `Editor/` and `Tests/` where noted:
   - hot-path: `FindObjectOfType`, `FindObjectsOfType`, `GameObject.Find(`, `Camera.main` (outside Awake/Start: I, needs light brace tracking, else warn-only), `.GetComponent<` inside `Update|FixedUpdate|LateUpdate|OnTrigger*|OnCollision*` bodies, `new WaitForSeconds`, `Physics.*(` without `NonAlloc` (Raycast single is OK), `Instantiate(`/`Destroy(` inside Update bodies, LINQ `using System.Linq` in files containing Update.
   - architecture: `PlayerPrefs.` (V rule: no persistence layer beside DataBlock), `async void` (allow list for event handlers), `Task.Run`, `SendMessage(`, `Resources.Load` outside factory, `?.`/`??` on `UnityEngine.Object` fields (V from 11: destroyed-object trap; flag `\b_\w+\?\.` on fields whose type derives from Component: I, needs type table, so warn-only list).
   - leftovers: `Debug.Log` in per-frame methods, `TODO QA`, `TEMP`, constants tagged `// REVERT` (V from 11: `MAX_MOVE_SPEED=203` class), `Time.timeScale =` outside `Editor`/`Dev`/`Debug` folders.
   - Suppression: `// qa-allow: <rule> <reason>` on the line; reason required.
4. asmdef rules (`qa_asmdef.py`): every asmdef parses; no cycles; Editor asmdef has `includePlatforms: [Editor]`; runtime asmdef does not reference `UnityEditor`; SDK asmdef does not reference Game (V constraint from 08); no `Assembly-CSharp` code containing `using UnityEditor` outside `#if UNITY_EDITOR` or an `Editor` folder (the classic build breaker); test asmdefs have `defineConstraints: UNITY_INCLUDE_TESTS` and `optionalUnityReferences`/references to `UnityEngine.TestRunner`.
5. Config sanity without Unity (I): `.asset` YAML numeric ranges for known ScriptableObjects are L3, not here.
Cost: all of L2 over a 900-file project should take <3 s in one python process (I, text regex; read each file once).

### L3 EditMode tests and data validation (C1)
Run via MCP `tests run` or `-runTests -testPlatform EditMode`. Implement as one generic, project-agnostic validator assembly plus per-project fixtures (I):
- `Qa_Registry_Tests`: for every `Factory_*` / `*Factory` singleton found by reflection (`ScriptableObjectSingleton<>` subclasses): load, call `OnInitialize`, assert no null entries, no duplicate ids (reflect `Id|ID|Key|Name` string field), every `UnityEngine.Object` field non-null (use `[RequireRef]` plus convention list), every Addressable/Resources path resolves. V from 11: thunder-break-egg `Build_DataBlockRegistryGuard` is the same idea as a build gate.
- `Qa_Config_Ranges`: attribute-driven (`[QaRange(min,max)]`, `[QaNonZero]`, `[QaId]`) on config fields, scanned by reflection over every `ScriptableObject` asset under `Assets/_Game/Configs`. AI agents add the attribute when they add the field (rule in skill). Catches 0 cooldown, negative price, cost growth < 1.
- `Qa_Prefab_Wiring`: for every prefab in `Assets/_Game/Prefabs`: no missing scripts (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount`), every `[SerializeField]` non-null unless `[Optional]`/`[CanBeNull]`-style marker (I: needs an agreed marker; default rule: all `[SerializeField]` Object refs are required), every `Button` has onClick listeners or a known handler component, every `Collider` on a layer in the physics matrix (V rule from done-means-wired: "missing tap collider on world-space buttons").
- `Qa_Scene_Wiring`: open each scene in `Assets/_Game/Scenes` additively in EditMode, same scan, plus: EventSystem exists in UI scenes, exactly one AudioListener, Canvas count matches rule (V unity-ui: one root canvas), no duplicate `[DisallowMultipleComponent]` singletons.
- `Qa_Economy_Sim` (section 4).
- DataBlock registry: all `DataBlock<T>` subclasses registered (V 11 guard) and serializable (round-trip JSON via the framework serializer, then equals).
- Test asmdef portability: if the project has no asmdef (V KT), the harness ships `Assets/_Game/Tests/EditMode/Game.Tests.EditMode.asmdef` with `"overrideReferences": false` and reflection-only access to game types by name via `AppDomain.CurrentDomain.GetAssemblies()` (I: Assembly-CSharp cannot be referenced, but reflection works).
Pass: all tests green; known-red list in `qa/known-red.json` is allowed only if each entry has owner+date (V from 11: six red unrelated tests were being ignored informally; make that explicit and expiring).

### L4 UI validator: see section 5.

### L5 PlayMode smoke (C3)
Spec for `Qa_Smoke` (I; mirrors `playmode-script-testing` but automated):
1. Boot: load boot scene index 0 (or `qa/smoke.json:bootScene`), wait until `Game ready` signal (poll up to 30 s unscaled; signal = `SceneManager` active scene is Home OR event `Event_Game_Ready`; project provides `Qa_Hooks` partial class returning ready state, default: first frame after loading screen object destroyed).
2. Fresh save: delete persistent data through the project's DataBlock path (compute from `PlayerSettings.companyName/productName`; V rule from unity-qa-playtest) and verify defaults; run again with a saved-profile fixture (`qa/profiles/mid.json`) for the second pass.
3. Home -> enter each mode listed in `qa/smoke.json:modes` (id, entry-method, expectedScene, playSeconds): entry via reflection `onClick.Invoke()` on a named Button path (V pattern from playmode-script-testing), not via screen coordinates.
4. Input bot for N seconds (default 20 game-seconds per mode, `timeScale=1`): bot component `Qa_InputBot` drives the project's input abstraction (joystick vector, tap, hold) with a seeded random walk plus scripted goals (move to nearest `IQaGoal`, press contextual button). Games implement `IQaGoal` on pickups/targets/zones (a 10-line interface); without it the bot random-walks and the run only proves "no exceptions", which is recorded as such.
5. Assertions every frame (Application.logMessageReceived): any `LogType.Exception` or `Error` not in `qa/log-allow.txt` fails and captures the stack + a screenshot; `NullReference` counts once per unique stack. Also fail on: Missing script warning, `EventSystem` absent, FPS < floor for >2 s (L7), no input-driven state change (progress counter unchanged after bot N s = "bot stuck" warning, not fail).
6. Exit: quit mode (back button via `Keyboard`/`Application.Quit` simulated through the project's back handler), return to Home, verify no leaked objects (`FindObjectsByType<Object>` count delta < tolerance after 3 enter/exit cycles; leaked listeners via StaticBus subscriber count if exposed), then stop Play and read Console again (errors on exit are real, V).
7. Validity gate (V from 11): the run is invalid and reported INCONCLUSIVE if `timeScale != 1`, the save was not fresh/known, or another agent holds the Play lock (`workspace_guard.py claim Editor:Play`).
Fast-forward variant `qa-ffwd` (allowed only for economy/progression, never for pass/fail of feel): timeScale up to 10, report labelled `FFWD`, and any timer-based pass at ffwd must be re-run at 1x for the specific failing case before being called a bug or a pass.

### L6 Screenshot and diff: section 5.4.
### L7 Perf capture: section 5.5.

## 3. Fix-retest loop protocol

### 3.1 Stages (ordered, fail-fast; a stage runs only if all before passed)

| Stage | Name | Checks | Cost | Needs |
|---|---|---|---|---|
| S0 | preflight | tool discovery, project+scene confirm, Editor state (not playing/compiling), workspace_guard check, baseline Console saved | C0/C1 | MCP or files |
| S1 | compile | L1 | C1 | Unity |
| S2 | static | L2 (refs, layout, banned API, asmdef) on diff-scoped files | C0 | none |
| S3 | data | L3 EditMode tests, registry/config validators | C1 | Unity |
| S4 | wiring | prefab/scene read-back + `done-means-wired` automated items | C1 | Unity |
| S5 | ui | L4 validator + L6 screenshots at 4 ratios | C1-C2 | Unity (+ YAML-only subset) |
| S6 | play | L5 smoke for modes touched by the diff (all modes at milestone) | C3 | Unity Play |
| S7 | perf | L7 capture vs tier budget, only if diff touches rendering/gameplay hot paths or milestone | C3 | Unity Play |
| S8 | log | `summarize_unity_log.py` on the whole run; zero unexplained rows | C0 | none |

Scope selection (I): `git diff --name-only` plus untracked picks stages: `.cs` -> S1,S2,S3(affected asmdef), `.prefab/.unity` -> S2,S4,S5,S6, `Configs/*.asset` -> S3,S6, `Materials/Shaders/Textures` -> S5,S7. Milestone/`--full` runs everything.

### 3.2 Loop
```
iteration = 1
while iteration <= MAX_ITER (default 5, 3 for UI-only):
    run stages in order, stop at first failing stage
    write run record to docs/qa/reports/<date>-<task>.md (append iteration block)
    if all pass: break -> PASS
    classify each failure: REAL | TEST-BUG | ENV | FLAKY
    REAL: fix root cause (systematic-debugging), never weaken test, never delete asset to silence (V rule), re-run from the FAILED stage (not S0), then once more from S1 when the fix touched code
    TEST-BUG: fix the validator with a note in qa-report; needs an explicit "why" line; max 1 per iteration
    ENV: connection/compile-lock/other agent Play: retry <=2 with backoff 20/60 s, then escalate
    FLAKY: re-run the single failing check 3x; 3/3 pass -> mark FLAKY, record; else REAL
    no-progress rule: same failure signature (rule+file+msg hash) in 2 consecutive iterations -> change strategy (read the code path with the failing evidence, widen the hypothesis); in 3 -> escalate
    iteration += 1
```

### 3.3 What counts as pass
- `PASS`: S1..S8 all green on the highest rung (Editor connected), zero unexplained Console rows, no known-red entry created in this task.
- `PASS-WITH-NOTES`: soft rules violated with an explicit reason in the report (UI soft ratios, section 5), perf within 10% of budget.
- `STATIC-PASS`: only S2 (and S8 on an old log) ran because Editor/Unity unavailable. Never wording "done"; wording: "not verified: compile, wiring, play".
- `INCONCLUSIVE`: validity gate failed (timeScale, dirty save, shared Editor). Counts as not run.
- `FAIL`: any hard rule red after MAX_ITER, or escalation.
Hard vs soft: compile errors, exceptions, missing script/ref, overlap of interactive rects, out-of-safe-area interactive, text overflow, perf above budget by >10%, any `Qa_*` test red = hard. Soft = icon/label ratios, spacing evenness, visual diff within the warn band.

### 3.4 qa-report (file `docs/qa/reports/YYYY-MM-DD-<task>.md`, <= 80 lines, append-only per iteration)
Header: project, Unity version, commit/dirty hash, rung (MCP/batch/static), tool list used, `timeScale`, save state (fresh/fixture), baseline Console rows. Per iteration: stage table (stage, result, duration, evidence path), failures with signature, root cause, fix commit-less diff summary. Footer: verdict (PASS/PASS-WITH-NOTES/STATIC-PASS/INCONCLUSIVE/FAIL), "NOT verified" list (real ads, store, device perf, other aspect ratios not captured), next human action. Machine-readable twin `docs/qa/reports/<same>.json` (stage results + failure signatures) so hooks and the Stop gate read pass/fail without parsing prose. Artifacts (screenshots, diffs, perf CSV) in `docs/qa/artifacts/<run-id>/`, git-ignored except the report. Bugs found and not fixed go to `docs/qa/bugs.md` (V format from unity-qa-playtest). Durable user feedback keeps going to `docs/feedback-notes.md` (V standing rule), not into the report.

### 3.5 Escalation to human (stop looping, write a one-screen summary)
- MAX_ITER reached, or same signature 3x.
- Needs a decision (design/API/economy intent), a missing asset the reference lacks, a destructive action (V rules), or data loss risk.
- ENV blocked > 2 retries (MCP down and no Unity, another agent owns Play/scene claim).
- A test must be weakened, or a baseline accepted (known-red entry, new perf budget).
- Only a device can answer (real ads/IAP/thermal/touch feel): output the device checklist (V format from unity-qa-playtest section 3) and mark everything else done.
Message format: verdict, the single blocking item, what was tried (iteration list), the smallest decision needed, evidence paths. No raw logs (V rule from unity-log-triage).

## 4. EditMode economy and progression sim checks (L3 detail)
Reuse `simulate_economy.py` (V, 54 lines; model `income = base + step*level`, `cost = base*growth^level`, prints waits and flags above target). Harden for harness:
- Source of truth: tool `qa_econ_dump` (Editor, ~120 lines C#) serializes the real config assets (upgrade tables, income, costs, egg HP, boss, ads) to `docs/qa/artifacts/econ.json` so the sim reads real numbers, not a copy (V lesson from 11: "first audit used a provisional hit cadence, 0.22 s vs 0.378 s measured": constants must be measured from assets/clips by the dump, e.g. `AnimationClip.length`).
- Checks (hard unless noted): no wait above `target_wait` between consecutive purchases (config in `qa/econ-targets.json`: per-stage max wait, total time to first zone unlock, to last zone); cost monotonic increasing; growth in `[1.05, 1.6]` (soft); no soft-lock (a state where affordable purchases = 0 and income = 0); sinks exist for every currency inflow (soft); ad/IAP packs return value within `[0.5x, 3x]` of equivalent play time (soft, reason required).
- Whole-loop requirement (V from unity-qa-playtest): collect -> carry -> place -> income -> upgrades -> boss -> zone progression must be one simulation, not isolated segments.
- Validity gate: run at game-time 1x semantics (sim is analytic, so it avoids timeScale false negatives, V from 11) and from default fresh-save values read via the DataBlock default constructor.
- In-game verification: a PlayMode `Qa_Route` bot executes a short scripted route and compares real income per 60 s to the sim within +/-20% (I tolerance); a larger gap means the sim or the wiring is wrong.

## 5. UI validator, screenshots, image diff, perf

### 5.1 Why "exact from one prompt" needs numbers
The agent must not iterate with the human on sizes. The loop is: spec -> build -> L4 numeric check -> L6 image diff vs reference -> fix until green. Reference is either a mockup image or a source prefab (V: `reference-port`, `ui-popup-from-demo` use `dump_prefab.py`). Rule precedence stays (V ui-clone): reference/spec > user message > `ui-style-rules` > `mobile-hud-layout`.

### 5.2 Two validator implementations, same rule IDs
A) `qa_ui_yaml.py` (C0, from prefab YAML; works with Editor closed; ~350 lines; extends `dump_prefab.py` logic): resolves anchors/pivots/offsets/sizeDelta for every RectTransform to a rect in reference resolution (default 1920x1080 from `project-config.yaml ui.referenceResolution`) and re-evaluates at 3 more aspects by Expand match mode: scale = min(w/refW, h/refH), canvas size = (w/scale, h/scale). Cannot evaluate Layout Groups/ContentSizeFitter/TMP preferred size exactly (I): those elements are marked `unknown-size` and deferred to B.
B) `Qa_UiValidator` (C1, runtime in Editor via MCP script execute or EditMode; ~400 lines C#): instantiates the prefab under a scaled test canvas at each resolution, calls `Canvas.ForceUpdateCanvases()` + `LayoutRebuilder.ForceRebuildLayoutImmediate`, reads `RectTransform.GetWorldCorners`, `TMP_Text.preferredWidth/Height`, `CanvasScaler`, `Screen.safeArea` simulated (see 5.3), and emits the same JSON findings. Runtime B is authoritative; A is the fast pre-check and local batch runner-without-Editor subset.

Resolutions (hard): 1920x1080 (ref), 2400x1080 (20:9), 1600x1200 (4:3), 1080x2400 and 1080x1920 when the game is portrait (V `unity-ui` lists the first three; add notch cases). Safe area test insets (I): left/right 132 px, top 0, bottom 63 px on 2400x1080, simulating a notch + gesture bar.

### 5.3 Rules (rule id, kind, formula, threshold, reason)
Hard (fail loop):
- `UI-OVERLAP`: for every pair of visible, interactive (Selectable or raycast target with handler) rects not in a parent/child chain: intersection area > 0 after 4 px shrink. Includes conditional elements: validator enables every inactive child flagged `[QaState]` or all inactive objects in `conditional` list from the spec (V rule: conditional buttons like Pick up must not overlap). Reason: mis-taps.
- `UI-SAFE`: interactive and text elements fully inside the safe area rect inset by `edgeMargin` (default 24 px at ref res, project-config key; V rule "no element touches an edge"). Full-screen backgrounds/dims exempt via name/`[QaBackground]`.
- `UI-BANNER`: gameplay UI bottom >= `ui.banner.reservedHeight` (default 200 px, V) above the bottom of the safe area.
- `UI-OVERFLOW`: text preferred size at current font size must fit its rect; if autosize is on, min font size must still fit (preferred at `fontSizeMin` <= rect), and min >= 18 px at ref res (I, readability on phones). Truncation/ellipsis is a failure unless `[QaAllowEllipsis]`. Reason: clipped prices/names.
- `UI-CHILD-EQ-PARENT`: a child (non-Root, non-background) whose world rect equals its parent's within 1 px while parent has a sprite/frame = suspicious double frame/stretch bug (the "child==parent size" trap); fails unless it is the single `Root` child (V unity-ui: exactly one stretch `Root`) or flagged.
- `UI-RAYCAST`: every Graphic with no Selectable/handler in its chain and not masked-for-scroll must have `raycastTarget=false` (V rule). Inverse: every Button must have a Graphic with raycastTarget=true. Also a full-screen invisible blocker over interactive UI = fail.
- `UI-STRUCT`: V unity-ui structure: one root Canvas Overlay, scale mode ScaleWithScreenSize, match mode Expand, sort order in range; hierarchy `GameSingleton>Canvas>Root>{SafeArea,ViewContainer,PopupRoot}`; popup prefab has exactly one `Root` child, stretch full, zero offsets, no Graphic.
- `UI-9SLICE`: every Image with a sprite whose importer border != 0 must be `Image.Type.Sliced` (V ui-clone lesson), and its rect must be >= border sum in both axes.
- `UI-MIRROR`: world-space UI text: scale sign of x positive when facing camera (dot of forward and camera forward < 0) (V ui-clone lesson).
- `UI-MISSING`: missing sprite/font/TMP asset, `Missing` script (shares L2 scan).
- `UI-REF-MATCH` (only when a reference prefab/spec exists): per matched element (by path or `qa/ui-map.json`), anchors, sizeDelta, sprite guid, color within tolerance: position +/- 2 px at ref res, size +/- 2 px, color delta (sRGB each channel) <= 6/255, font size equal. V rule: "port, don't approximate".
Soft (warn; fail only if no reason line is written in the report; reason text is mandatory per soft rule):
- `UI-SPACING`: gaps between siblings in a group differ by <= 15% or 8 px (whichever larger); left/right symmetry for HUD edge groups within 4 px of mirrored position (V "balanced, symmetric").
- `UI-TOUCH`: interactive min size 88x88 px at ref res 1920x1080 (about 44 pt, I from platform guidance); gaps between interactive rects >= 44 px (V from ui-clone "keep >= ~44 px gaps").
- `UI-ICON-LABEL`: icon height / label cap height in `[1.2, 2.2]` (I: soft heuristic to catch a 12 px icon beside 40 px text); icon+label pair vertically centered within 3 px; currency icon height within `[0.9, 1.4]` of text line height. Reason is stylistic; exception allowed when the reference differs (then `UI-REF-MATCH` wins).
- `UI-CONTRAST`: text vs nearest opaque background luminance contrast >= 3:1 (I, from screenshot sampling, not rect math).
- `UI-CENTER-FREE`: central 40% x 40% of gameplay view has no HUD element (V rule "center of gameplay view stays free"); not for popups.
Exceptions only via `qa/ui-exceptions.json` entries `{rule, path, reason, owner}`.

### 5.4 Screenshot capture and image diff
Tool choice (decision table):
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| MCP screenshot tool (Game view) (I) | no code, exact Game view, works while Editor open | resolution tied to Game view window; needs the right Game view size set per aspect; returns image into agent context (token cost); not scriptable in local batch runner | use for agent loop eyeballing and as the fallback |
| In-Editor capture script (`ScreenCapture.CaptureScreenshot` / `RenderTexture` + `ReadPixels` of the UI camera, run via script-execute) | exact pixel size per aspect (set `Screen` via GameViewSize reflection or render the canvas camera to RT), writes PNG to `docs/qa/artifacts`, no tokens, deterministic | needs Play Mode or ScreenSpaceCamera canvas for Overlay (Overlay canvases render only in Game view; use `Canvas.renderMode = ScreenSpaceCamera` on a clone for the capture) | **primary** (`Qa_Capture`, mirrors V `Dev_SceneCapture`/`Dev_UiCapture` from thunder-break-egg) |
| Batchmode capture (`-batchmode` without `-nographics`, `-executeMethod Qa.CaptureAll`) | headless local batch runner on a machine with a GPU | slower start (~30-90 s), I: Overlay canvases still need the camera trick | use for local batch runner/nightly |
| Headless render with `-nographics` | works anywhere | no pixels | not usable for diff |
Pipeline: for each (screen, aspect in 1920x1080, 2400x1080, 1600x1200, 1080x2400): instantiate prefab/open scene, set fixed seed + `timeScale 1`, wait 2 frames + all entrance animations done (poll `DOTween/PrimeTween` count == 0 or wait fixed 1.0 s unscaled), force fixed fonts, disable particles/animated backgrounds via `QaFreeze` (I), capture PNG lossless. Reference image (`qa/ref/<screen>.png`) is captured at 1920x1080 only; other aspects are checked by rules (5.3) and by self-regression (golden = the first approved capture per aspect, stored under `qa/golden/<aspect>/`).
Diff (`qa_image_diff.py`, Pillow+numpy, ~150 lines; V Python 3.14.7 exists, packages I: need `pip install pillow numpy`, check import first):
1. Resize-free: images must be identical resolution else fail with note. 2. Mask dynamic regions (`qa/masks/<screen>.json` rectangles: timers, random rewards). 3. Per-pixel delta in linear sRGB; pixel "differs" if max channel delta > 12/255 (tolerates AA/compression). 4. Structural: SSIM on grayscale (window 7). 5. Edge map comparison (Sobel) to catch shifted frames when colors are similar.
Thresholds (initial, I, to tune on 5 real screens before enforcing): vs mockup/reference (a pre-composed render): PASS if differing pixels <= 1.5% and SSIM >= 0.97; WARN 1.5-4% or SSIM 0.93-0.97; FAIL beyond. Vs own golden (regression): PASS <= 0.2%, FAIL > 1%. Output: `diff.png` (red overlay) + a 10-line text summary with bounding boxes of the top 5 differing regions mapped to element names via the L4 rect table, so the agent can fix exact elements ("element ShopPopup/Header: 14 px lower than reference"), not eyeball.
Agent viewing: never paste full-res images repeatedly; view only diff crops of the top 2 regions (V token-efficient rule).

### 5.5 Perf capture (L7)
Mechanism (I): script-execute or a `Qa_PerfProbe` MonoBehaviour using `ProfilerRecorder` (Unity.Profiling) with `ProfilerCategory.Render` "SetPass Calls Count", "Draw Calls Count", "Batches Count", "Triangles Count", `ProfilerCategory.Memory` "GC Allocated In Frame", "System Used Memory", "Total Used Memory", `ProfilerCategory.Internal` "Main Thread" frame time, `ProfilerCategory.Physics`: "Physics.Processed" counts. `ProfilerRecorder` works in Editor and development builds; release builds need `Debug.isDebugBuild` (I). Frame time from `Time.unscaledDeltaTime` ring buffer (p50, p95, p99, max). GC alloc/frame average and max over measurement window excluding first 60 frames (warm-up). Capture only at `timeScale 1`, window 20 s per scenario (home idle, each mode active with the bot, popup open, heaviest zone), VSync as the project sets, target frame rate recorded.
Validity (V from mobile-perf-audit and CLAUDE.md): Editor numbers are indicative; budgets are enforced as ratios against a stored baseline for regression (`qa/perf-baseline.json`, per scenario) and as absolute caps from tier table only for relative-structural counts (draw calls, set-pass, GC, memory), because Editor ms is not device ms.
Budgets (I, defaults to be overridden by project; ASSUME low-end Android is the default target per user rule):
| Metric | Low tier (2 GB RAM, weak SoC) | Mid tier | High tier / PC |
|---|---|---|---|
| Target fps | 30 (frame 33.3 ms) | 60 (16.7 ms) | 60-120 |
| Editor main-thread p95 ms (indicative only) | <= 12 | <= 8 | <= 6 |
| Batches (draw calls) in gameplay | <= 150 | <= 300 | <= 800 |
| SetPass calls | <= 40 | <= 80 | <= 200 |
| Triangles | <= 150k | <= 400k | <= 1.5M |
| GC alloc per frame (steady state) | 0 B target, <= 1 KB hard | <= 2 KB | <= 4 KB |
| GC collections in 20 s window | 0 | <= 1 | <= 2 |
| Total memory in scene (Editor, indicative) | <= 600 MB | <= 1 GB | n/a; device RSS budget 700 MB low |
| Texture memory | <= 150 MB | <= 300 MB | n/a |
| Active Update-bearing MonoBehaviours | <= 300 | <= 800 | n/a |
Regression rule: fail if batches or set-pass grow > 10% over baseline, GC/frame > baseline + 256 B, p95 frame > baseline * 1.15, memory > baseline * 1.10 (noise margin recorded from 3 baseline runs: baseline = median, allowed = max(spread*2, rule)). Exceeding absolute budget by <= 10% = PASS-WITH-NOTES with a reason. Always label the report "Editor-measured, not low-end device" (V rule). Real-device capture stays human or an adb-driven script (`adb shell dumpsys gfxinfo <pkg>`; I, rung 4, not in v1).
Static prefilter (C0): `qa_banned_api.py` (2.3) is the cheap proxy for the hot-path list in `mobile-perf-audit`; it never claims perf, only flags likely causes.

### 5.6 Log triage (S8)
V `summarize_unity_log.py`: default Editor.log since last reload, rows COMPILE-ERR/EXCEPTION/ERROR with counts and first `Assets/` location. Extensions (I): `--json` output, `--since-marker` (the harness writes a unique `[QA-RUN <id>]` Debug.Log line at stage start via script execute, then summarize from that marker, fixing the "log belongs to whichever instance wrote it last" caveat by also checking the `-projectPath`/`Project:` header line), `--allow qa/log-allow.txt` (regex, each with reason), exit code 1 if any non-allowed row. Per-frame error rows (count >= 30) get severity "perf+bug".

## 6. Headless local batch runner vs open Editor

| Check | Headless `Unity -batchmode` | Needs open Editor / MCP | Notes |
|---|---|---|---|
| L2 static (all) | yes (python only; no Unity) | no | fastest; runs anywhere |
| L1 compile | yes: `-batchmode -quit -projectPath P -logFile` | no | exit code 1 on compile error (I); cannot run while the same project is open in an Editor (project lock) |
| L3 EditMode tests | yes: `-runTests -testPlatform EditMode -testResults r.xml -batchmode` | optional | no `-quit` with `-runTests`; parse NUnit XML; `-testFilter "Qa_"` |
| L3 asset/prefab wiring | yes via EditMode tests | optional | scenes opened additively in test |
| L5 PlayMode smoke | yes: `-runTests -testPlatform PlayMode` with `[UnityTest]` coroutine, no `-nographics` if rendering needed | yes for live debug | PlayMode tests in batch need the PlayMode asmdef; slower; hits real framework init (ads SDK mocks required, V 08 "Editor mock path for every SDK") |
| L4B runtime UI validator | yes (EditMode or `-executeMethod Qa.UiValidate`) | optional | needs UI camera setup; fonts must be imported |
| L6 screenshots/diff | capture: batchmode with GPU (I), diff: python anywhere | MCP screenshot as fallback | on local batch runner without GPU: skip capture and mark `NOT VERIFIED visual` |
| L7 perf | no for fidelity (needs real render + GPU); regression of counters yes | yes for authoritative Editor numbers | device numbers always human/adb |
| MCP-only interactions (hierarchy tweak, live reflection click) | no | yes | not needed in local batch runner |
CLI skeleton (I): `"C:\Program Files\Unity\Hub\Editor\<ver from ProjectVersion.txt>\Editor\Unity.exe" -batchmode -projectPath <P> -runTests -testPlatform EditMode -testResults <out.xml> -logFile <out.log>` then `qa_run.py` parses XML + runs `summarize_unity_log.py` on the log. The wrapper must refuse if an Editor already holds the project (check `Temp/UnityLockfile`, V lock behaviour I) and fall back to MCP.
Editor version choice: read `ProjectVersion.txt`; V machine has 2022.3.62f3, 6000.0.78f1, 6000.3.22f1; if the pinned version is not installed, stop (S0 fail, escalate), do not open the project with a different Editor (it triggers a project upgrade; V rule: ask before major upgrades).
Concurrency (V from multi-agent-coexistence): headless run and open Editor must not use the same project directory; for local batch runner use a copy (`git worktree`) or run only when the Editor is closed. Guard with `workspace_guard.py claim Editor`.

## 7. Hooks: calling checks cheaply

Principle: hooks must be fast (<2 s sync), deterministic, quiet on success, and only block with a short actionable reason. Heavy checks run async or at Stop. All hooks live in the project's `.claude/settings.json` (V: user-level has none today; project-level files are version-controlled and shared; I).

### PostToolUse after Edit/Write on `*.cs` (and `.prefab/.unity/.asset`)
- Matcher `Edit|Write|MultiEdit`; command `python -I tools/qa/hook_post_edit.py` (reads the tool JSON on stdin, I: gets `tool_input.file_path`).
- Does only C0 work (<1 s): L2 subset on that file only (banned API in changed hunks, naming, namespace, `UnityEditor` leak, YAML missing-ref scan for yaml files). Findings printed as JSON `{"decision":"block","reason":"..."}` for hard rules (I: PostToolUse feedback surfaces to the model as context; exit code 2 + stderr feeds it back), warnings otherwise suppressed to save tokens (V token rule).
- Also touches a marker `qa/.dirty-cs` (timestamp + file list) so the Stop gate and MCP refresh know a compile is owed. Does NOT trigger Unity compile itself (compile loops during multi-file edits waste time and hit domain reload races; V pitfall from 11: another agent in Play blocked compile three times).
- Debounced compile option (I, off by default): `hook_post_edit.py` writes marker; the agent's next MCP step `assets refresh` is the compile gate; a skill rule tells the agent to refresh after a batch of edits, not after each.
- Hook also calls `workspace_guard.py check` for the edited file (V script): blocks if the file changed on disk since snapshot (parallel-agent rule).

### Stop gate
- Event `Stop`; command `python -I tools/qa/hook_stop_gate.py`. Logic (I):
  1. If `git status` shows no changes under `Assets/`, `Packages/`, `ProjectSettings/` since the last green report: allow stop.
  2. Else read newest `docs/qa/reports/*.json`: allow only if its `verdict` in {PASS, PASS-WITH-NOTES, STATIC-PASS with explicit "not verified" list, ESCALATED} AND its `fingerprint` (hash of changed Assets files) equals the current one AND `rung` matches claims.
  3. Else block with reason: "Stop blocked: changed files <n>, last QA <verdict/none>. Run qa_run (stages S1-S8) or write ESCALATED report." Loop protection: honour `stop_hook_active` input (I) so it blocks once per turn, and allow after the second attempt with the verdict forced to INCONCLUSIVE written to the report (prevents deadlock when Unity is unavailable).
- Cost: reading JSON + `git status --porcelain` + hash of changed files: <300 ms.

### SessionStart hook (optional)
Print `docs/agent-handoff.md` tail, `git status`, known-red list, MCP connection check (python pings the MCP port from `.mcp.json` or Editor `Library` project info; I) so ECONNREFUSED is known on turn 1 and the agent picks rung 2/3 immediately (V: it cost thunder-break-egg queued work).

### PreToolUse (optional guard)
Deny `Edit` on files in other agents' claims (V `workspace_guard.py claim`) and deny `Write` to `Library/`, `Temp/`, `.meta`, `ProjectSettings` without a flag (V rule: do not hand-author `.meta`).

## 8. Validity gates (QA false-negative prevention, from 11 and unity-qa-playtest)
Every run records these and refuses PASS when violated:
1. `timeScale == 1` for all verdicts except explicit `FFWD` econ checks (V rule `rule-qa-validity`).
2. Save state known: fresh (deleted through exact persistent path) or named fixture; record hash of save before and after; restore after test (V playmode-script-testing step 7).
3. Constants measured not assumed: a harness check lists every numeric constant used by the audit with its source (asset field, clip length). Unsourced constant -> warn.
4. Temporary test constants: `qa_banned_api.py` greps `// REVERT`, `TEMP`; Stop gate fails if any remain in the diff (V 11: `MAX_MOVE_SPEED=203`).
5. Editor not owned by another agent (Play Mode claim); Console baseline taken before the run; after the run Editor returned to Edit Mode and scene not dirty from play.
6. Compile state: a stage that runs C# must start with `EditorApplication.isCompiling == false` (V "stale compile created duplicate objects").
7. Generated content: if a builder produced the output, the check must run the builder again and diff (V "generator-owned content"): `qa_builder_idempotent` = run builder twice, assert second run produces no diff.
8. Destroyed-object trap: banned-API rule for `?.` on Unity objects (V 11, `Pet_Carrier.Steal`).

## 9. Concrete tool/script inventory

Exist now (reuse, V):
| Name | Lang | Lines | Role in harness |
|---|---|---|---|
| `skills/unity-log-triage/scripts/summarize_unity_log.py` | py | 124 | S8, S1 error parse; extend with `--json`, `--since-marker`, `--allow` (+~60) |
| `skills/ui-popup-from-demo/dump_prefab.py` | py | 81 | base for `qa_ui_yaml.py` rect resolution |
| `skills/multi-agent-coexistence/scripts/workspace_guard.py` | py | 198 | snapshot/check/claim in hooks and S0 |
| `skills/project-context-map/scripts/unity_project_scan.py` | py | 254 | find asmdefs, scenes, singletons for the validators |
| `skills/asset-transfer-closure/scripts/resolve_closure.py` | py | 251 | GUID map / dependency closure (refs scan) |
| `skills/economy-progression-design/scripts/simulate_economy.py` | py | 54 | pacing sim; extend to read `econ.json` |
| `skills/ui-scroll-board/scripts/grid_fit.py` | py | 58 | grid math reference |
| `Dev_SceneCapture`, `Dev_UiCapture`, Scan Missing Scripts, `Build_DataBlockRegistryGuard`, audit sims (thunder-break-egg, Editor C#) | C# | n/a | patterns to port generically, not copy blindly |

To build (new; placed in a new skill folder `skills/qa-harness/scripts/` and a C# package `skills/qa-harness/unity/Qa/` copied into `Assets/_Game/Scripts/Editor/Qa` and `Tests/` by a bootstrap step; sizes are estimates, I):
| # | Name | Lang | Inputs | Outputs | Lines |
|---|---|---|---|---|---|
| 1 | `qa_run.py` | py | project path, `--stages`, `--scope diff|full`, `--rung auto` | run JSON + md report, exit code; orchestrates all, picks rung | 350 |
| 2 | `qa_scan_refs.py` | py | `Assets/` path, required-refs.json | findings JSONL (missing script/guid/fileID) | 220 |
| 3 | `qa_lint_layout.py` | py | project path, house-style config | findings (folder/namespace/naming) | 180 |
| 4 | `qa_banned_api.py` | py | `.cs` files or diff, rules.json | findings with allow-comments honoured | 200 |
| 5 | `qa_asmdef.py` | py | `**/*.asmdef` + `.cs` using lines | findings (cycles, Editor leaks, SDK->Game) | 120 |
| 6 | `qa_ui_yaml.py` | py | prefab(s), `project-config.yaml`, ui-exceptions.json | UI findings at 4 aspects, rect table JSON | 350 |
| 7 | `qa_image_diff.py` | py (pillow, numpy) | ref.png, shot.png, mask json | diff.png, summary, verdict by thresholds | 150 |
| 8 | `qa_perf_compare.py` | py | perf CSV/JSON, baseline, tier | pass/fail table | 100 |
| 9 | `qa_econ_check.py` | py | `econ.json`, targets | pacing + soft-lock checks (wraps simulate_economy) | 150 |
| 10 | `hook_post_edit.py`, `hook_stop_gate.py` | py | hook stdin JSON, reports | block/allow decision | 90 + 110 |
| 11 | `qa_unity_batch.py` | py | project, test platform, filter | runs `Unity.exe -runTests`, parses NUnit XML, lock check | 140 |
| 12 | `Qa_Registry_Tests`, `Qa_Config_Ranges`, `Qa_Prefab_Wiring`, `Qa_Scene_Wiring` + attributes `[RequireRef] [QaRange] [QaId]` | C# EditMode | project assets | NUnit results | 450 |
| 13 | `Qa_UiValidator` (+ `Qa_Capture`) | C# Editor | prefab list, resolutions | UI findings JSON, PNGs | 450 |
| 14 | `Qa_Smoke`, `Qa_InputBot`, `IQaGoal`, `Qa_PerfProbe` | C# PlayMode | `qa/smoke.json` | smoke result + perf JSON | 500 |
| 15 | `qa_econ_dump` | C# Editor | config assets | `econ.json` | 120 |
Total about 3,900 lines; python part about 2,300, built and tested without Unity first (python layers L2 + L4A + diff give most value, about 1,500 lines, build order 1).
Per-project data (not code): `qa/smoke.json`, `qa/required-refs.json`, `qa/log-allow.txt`, `qa/ui-exceptions.json`, `qa/econ-targets.json`, `qa/perf-baseline.json`, `qa/known-red.json`, `qa/ref/`, `qa/golden/`.

Build order (value/effort): (1) hooks + `qa_banned_api` + `qa_scan_refs` + log triage extension, (2) `qa_run` orchestrator + report format + Stop gate, (3) EditMode registry/prefab/scene tests, (4) UI yaml validator + image diff, (5) runtime UI validator + capture, (6) smoke bot + perf probe, (7) batch/local batch runner wrapper.

## 10. Open risks (I)
- MCP test-run and script-execute may time out and retry (V skill warns retries re-run scripts): validators must be idempotent, results written to files, call kept short.
- Projects without asmdefs limit test assembly access; reflection-based tests work but are more fragile.
- Overlay canvases cannot be captured via camera; the capture helper needs the camera-mode clone, which can differ subtly from Overlay rendering (post effects, scaling). Mitigate by also keeping one real Game-view MCP screenshot per screen in the report.
- Image diff thresholds are guesses until calibrated on 5 real screens (including AA differences between Editor and device).
- Bots only prove "no crash"; goal-directed progress requires per-game `IQaGoal`, a cost that must be a rule in new-feature skills (small interface, 10 lines).
- Perf in Editor is not device perf; budgets are structural counters, not ms. Device validation remains human or an `adb` script.
- Stop-gate deadlocks when Unity cannot start: handled by the `stop_hook_active` fallback and ESCALATED verdict.
- Hook API details (stdin JSON shape, exit-code semantics, `stop_hook_active`) are from knowledge; confirm with the `update-config` skill before wiring.

## 11. Proposed classification

| Item | Class | Proposed name | Content |
|---|---|---|---|
| Verdict definitions, validity gates, pass wording, "never say done without S1-S6 evidence" | RULE | `rule-qa-verdicts-and-validity` | PASS/PASS-WITH-NOTES/STATIC-PASS/INCONCLUSIVE/FAIL; timeScale 1, known save, measured constants, no leftover temp constants; STATIC-PASS never "done" |
| Fix-retest loop (stages, MAX_ITER 5/3, failure classes, same-signature rule, escalation list, report format) | SKILL | `qa-fix-retest-loop` | S0-S8, scope selection by diff, report path/JSON, human escalation message |
| UI numeric rules (hard/soft, thresholds, reasons, exceptions file, 4 aspects + safe-area insets, ref-match tolerances) | DATA | `ui-validation-rules` | rule table 5.3 as JSON consumed by validators; referenced by `unity-ui`/`ui-clone` |
| UI exact-from-prompt build loop (spec -> build -> L4 -> image diff -> fix) | RECIPE | `ui-build-verify-loop` | inside `ui-clone`; element-level diff messages; capture pipeline |
| Static check scripts (refs, layout, banned API, asmdef) + hooks | TOOL | `qa-static-checks` + `qa-hooks` | `qa_scan_refs.py`, `qa_lint_layout.py`, `qa_banned_api.py`, `qa_asmdef.py`, `hook_post_edit.py`, `hook_stop_gate.py`, settings.json snippet |
| EditMode validators + attributes `[RequireRef] [QaRange] [QaId]` | TOOL | `qa-editmode-validators` | C# package, bootstrap into project, known-red policy |
| PlayMode smoke + input bot + `IQaGoal` + perf probe + budgets table | TOOL + DATA | `qa-playmode-smoke`, `perf-budgets-by-tier` | `smoke.json` schema, tier budgets table, baseline regression rules |
| Headless/local batch runner and degradation ladder | RECIPE | `qa-batch-and-fallbacks` | `Unity.exe -runTests` skeleton, lock checks, rung selection, ECONNREFUSED path |

Must-haves (in order):
1. `qa-fix-retest-loop` skill + `rule-qa-verdicts-and-validity` (stops "done" claims without evidence; works even with MCP down).
2. `qa-static-checks` (`qa_scan_refs.py`, `qa_banned_api.py`, `qa_lint_layout.py`) wired by `qa-hooks` PostToolUse + Stop gate: cheapest, catches missing refs and banned APIs with no Unity.
3. `qa-editmode-validators` (registry/config/prefab/scene wiring) + `qa_unity_batch.py`: catches broken wiring and data errors headlessly.
4. `ui-validation-rules` + `qa_ui_yaml.py` + `qa_image_diff.py` (+ `ui-build-verify-loop`): the "UI exact from one prompt" gate with numbers instead of human nudges.
5. `qa-playmode-smoke` with `Qa_InputBot`, console-exception gate and `IQaGoal` convention: catches runtime exceptions in every mode.
6. `perf-budgets-by-tier` + `Qa_PerfProbe` + `qa_perf_compare.py`: structural perf regression catch (draw calls, set-pass, GC), clearly labelled Editor-measured.
