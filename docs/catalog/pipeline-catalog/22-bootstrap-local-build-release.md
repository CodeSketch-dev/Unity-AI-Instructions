# 22 - Bootstrap, batch build, local batch runner, store release (design)

Scope: design for "new game from template in about 1 day". Read-only study 2026-10-15.
Tags: **V** = VERIFIED on this machine / in files, **I** = INFERRED or proposed. No secrets printed.

## 0. Verified facts that shape the design

| Fact | Tag |
|---|---|
| Editors installed: 2022.3.62f3, 6000.0.78f1 (KT), 6000.3.22f1 (ME) under `C:\Program Files\Unity\Hub\Editor`. All have `AndroidPlayer`; only 6000.3.22f1 has `iOSSupport`. | V |
| Android toolchain is the Unity-bundled one: `...\PlaybackEngines\AndroidPlayer\{SDK,NDK,OpenJDK}`. No system `java`, no `gh` on PATH. `git`, `py` and `claude` 2.1.296 exist. | V |
| No `.ulf` license file found under `C:\ProgramData\Unity` (only `config\`); license is probably a Hub personal/pro sign-in, not a serial. | V (absence), I (meaning) |
| KT/ME: IL2CPP (`scriptingBackend Android: 1`), `AndroidTargetArchitectures: 2` (ARM64 only), minSdk 24 (KT) / 25 (ME), targetSdk 36, strip engine code on, KT managed stripping level 4 (High). ME has `AndroidAllowedArchitectures: -13`. | V `ProjectSettings/ProjectSettings.asset` |
| Manifest: `com.codesketch` (git `#main`, unpinned), `com.codesketch.installer`, UniTask (git), PrimeTween (local tgz), Addressables 2.9.1, test-framework 1.6.0. Newer game `thunder-break-egg` uses `com.sketchengine` (git, no tag). | V `Packages/manifest.json` |
| Android templates in `Assets/Plugins/Android`: `AndroidManifest.xml`, `baseProjectTemplate.gradle`, `mainTemplate.gradle`, `settingsTemplate.gradle`, `gradleTemplate.properties`, `proguard-user.txt`, `FirebaseApp.androidlib`, `GoogleMobileAdsPlugin.androidlib`, `googlemobileads-unity.aar`. | V |
| `Upstore/` holds `*.keystore` files in both repos (catalog 08 says they are tracked in git: an anti-pattern). `.gitignore` ignores `*.apk`, `*.aab` only. No `.github/` workflows in either project. | V |
| Studio SDK = vendored "Bounce SDK" (`Assets/BounceSdk`, `BounceCommon`), Splash scene first, define symbols `USE_MAX/USE_ADJUST/...`, `BounceConfig` asset holds ad unit ids/tokens. | V (catalog 08) |
| 0 first-party asmdefs in KT/ME. | V (catalog 08) |
| Existing skills: `mobile-build-release` (38 lines, checklist only, no commands), `unity-project-bootstrap` (26 lines, steps only, no script), `mobile-perf-audit`. No build script, local batch runner file, or template repo exists. | V |

## 1. Project bootstrap: the template

### 1.1 Form: template repo (not a UPM package)

A UPM package cannot carry ProjectSettings, Assets layout or Android gradle templates. Use **one GitHub template repo `game-template-unity`** (private) plus the framework as a UPM git dependency. I

Structure of the template repo:

```text
game-template-unity/
├─ .gitignore  .gitattributes (LFS)  .editorconfig  AGENTS.md  CLAUDE.md
├─ .github/workflows/{local-build.ps1,release.yml}      (section 4)
├─ ci/                                         (run by local batch runner AND by local runner)
│  ├─ build.ps1  test.ps1  size-report.py  startup-check.py  gates.json
│  └─ secrets.example.json                     (placeholders only)
├─ tools/new-game.ps1                          (section 1.3)
├─ docs/{feedback-notes.md,agent-handoff.md,project-setup.md,store/}
├─ Packages/manifest.json                      (pinned git URLs, section 1.2)
├─ ProjectSettings/                            (baseline, section 1.4)
├─ UserSettings/ (ignored)
└─ Assets/
   ├─ _Art/  _Game/{Audios,Configs,Fonts,Localization,Materials,Prefabs,Resources,Scenes,Scripts/{Core,Data,Editor,Event,Factory,Logic}}
   ├─ _Game/Scenes/Boot.unity  Home.unity  Game.unity   (Boot first in build)
   ├─ _Game/Scripts/Editor/Build/{BuildCli.cs,BuildSettingsApplier.cs,PostBuildReport.cs}
   ├─ Plugins/Android/                         (templates, section 2.4)
   └─ Tests/{EditMode,PlayMode}/               (asmdefs)
```

Only folders with content are kept; use `.gitkeep`-free policy: the template ships Boot/Home/Game scenes and a sample feature so folders are real. I

### 1.2 Dependencies (pinned, reproducible)

- Framework: `"com.sketchengine": "https://github.com/CodeSketch-dev/SketchEngine.git#<tag-or-sha>"` for new games; `com.codesketch` + `com.codesketch.installer` only for legacy clones. **Pin a tag or commit SHA**, never `#main`/no ref (KT/ME are unpinned: a build next month may differ). V for current state, I for the fix.
- Also: UniTask (git path with `#2.5.10`-style tag), PrimeTween (one tween lib), URP matching editor, Input System only if used, Addressables only if content is remote or > ~150 MB, `com.unity.test-framework`, `com.unity.mobile.android-logcat` (dev).
- `Packages/packages-lock.json` is **committed** (lock = reproducible). I
- Unity MCP bridge (ivanmurzak) is a dev-only dependency: wrap in a define or leave out of release manifests via `qa/prepare-release-manifest.py` (removes `com.ivanmurzak.*` before the local batch runner build). I

### 1.3 SDK stack skeleton (thin, swappable)

Rule: game code never calls SDK classes directly. Template ships interfaces + a no-op implementation so the game compiles and runs with zero SDK:

| Slot | Template content | Real impl (per game, behind define) |
|---|---|---|
| Ads | `IAdsService` (Banner/Inter/Rewarded/AppOpen, `OnPaid`), `NullAds` returning success in Editor | MAX (`USE_MAX`), as in `AdsHelper` -> `BounceAdsSdk` (V catalog 08) |
| Analytics | `IAnalytics.Log(name, params)`, `NullAnalytics` | Adjust/Firebase (`USE_ADJUST`, `USE_FIREBASE`) |
| Consent | `IConsent` (UMP/GDPR/ATT state, `CanShowPersonalizedAds`) + Boot step that **blocks ad init until resolved** | Google UMP via MAX/AdMob; ATT on iOS |
| Boot | `Boot.unity`: init order = Data load -> Consent -> Analytics -> Ads init (async, non-blocking) -> Home | - |
| Config | `GameIds.example.asset` / `SdkKeys.example.json` with `REPLACE_ME` | real file untracked (section 5) |
| Debug | cheats panel behind `DEVELOPMENT_BUILD || UNITY_EDITOR` | existing skill `debug-cheats-menu` |

Boot must not wait on ad SDK init to show Home (see startup budget, section 6). I

### 1.4 ProjectSettings baseline (apply by script, not by hand) I

`BuildSettingsApplier.Apply()` (editor script, idempotent, logs every change) sets:

- Android: IL2CPP, ARM64 only (`AndroidTargetArchitectures = ARM64`), Mono excluded, `buildAppBundle` for release, minSdk 24 (25 if the ads SDK demands), targetSdk **latest installed that Play requires** (verify policy; KT/ME use 36), ASTC texture compression, `Optimized Frame Pacing` on, managed stripping Medium (High only after a device smoke test, KT uses High), `Strip Engine Code` on, graphics API Vulkan+GLES3 or GLES3 only (decide per game, see 6), orientation locked.
- Scripting define symbols per build profile: `RELEASE`, `USE_MAX;USE_ADJUST` etc. managed through `BuildSettingsApplier`, not manually.
- Quality: 3 levels (Low/Mid/High), Mobile URP asset on Android levels, PC URP asset only on Editor/Standalone levels. URP mobile: SRP Batcher, 1 cascade, 512-1024 shadow map, no soft shadows, MSAA off/2x, HDR off, depth/opaque off.
- Physics: `autoSyncTransforms` off, `reuseCollisionCallbacks` on, default solver iterations, tight layer matrix (template ships a layer/tag list: `Default, UI, Player, Enemy, Pickup, Trigger, Ground, Ignore`).
- Time: `Application.targetFrameRate=60`, `vSyncCount=0`, `Screen.sleepTimeout=NeverSleep`.
- Player: `Incremental GC` on, `Use incremental IL2CPP` off for release builds (local batch runner), company/product/bundle id from `project.config.json` (1.5).
- Input: one choice per template (new Input System or legacy), fixed, not both.
- Asmdefs: `Game.Runtime` (all `Scripts` except Editor), `Game.Editor` (Editor-only, refs Runtime), `Game.Tests.EditMode`, `Game.Tests.PlayMode`. Framework packages already have asmdefs; first-party code today has none (V), so asmdefs are a template-level improvement with a rename cost for legacy projects. I
- `.gitattributes` LFS: `*.fbx *.psd *.png(over size) *.wav *.mp3 *.mp4 *.ogg *.tga *.exr *.unitypackage *.aar *.so`. `.gitignore`: standard Unity + `Library Temp obj Logs UserSettings Builds/ *.apk *.aab *.symbols.zip Upstore/ secrets.local.json *.keystore *.jks google-services.json(if per-app, see 5)`. Do NOT ignore `ProjectVersion.txt` (KT does: V anti-pattern).

### 1.5 New-game creation (agent procedure) I

One command, run by an agent or human, never by hand-editing YAML:

```powershell
# 1) create repo from template (gh is NOT installed here: install gh, or use git)
git clone <template-url> <NewGame>; cd <NewGame>
Remove-Item -Recurse -Force .git; git init -b main
# 2) fill project.config.json (tracked, no secrets)
#    { "company":"CodeSketch", "product":"My Game", "bundleId":"com.codesketch.mygame",
#      "version":"0.1.0", "unity":"6000.3.22f1", "orientation":"portrait" }
# 3) rename
py tools/new-game.py --config project.config.json   # sets namespace root, asmdef names, product, bundle id, scene names
# 4) bootstrap inside Unity (batch)
& $env:UNITY -batchmode -nographics -quit -projectPath . -logFile Logs/bootstrap.log `
  -executeMethod Game.EditorTools.BuildCli.Bootstrap
# 5) compile + tests
./qa/test.ps1 EditMode
```

`new-game.py` does only text replacement on known files (ProjectSettings values go through `BuildSettingsApplier`, not text edit) and refuses to run if `.git` of the template still has the template remote. It writes:
- `docs/project-setup.md` (decisions), `docs/clone-plan.md` stub, empty `docs/feedback-notes.md`.
- Placeholder icon (512 and adaptive 432 layers), placeholder splash, `Upstore/` NOT created (keystore generated locally, section 5).
- Prints a **TODO list for the human**: provide SDK keys file, generate keystore, replace icon, create store listing.

Agent safety: first step is `git status` + read `AGENTS.md`; never run on a dirty tree; no commit/push unless the user asks (house rule). V (AGENTS.md).

## 2. Unity batch-mode automation

### 2.1 Editor and license (Windows, this machine)

```powershell
$env:UNITY = "C:\Program Files\Unity\Hub\Editor\6000.3.22f1\Editor\Unity.exe"   # V path exists
```
- Batch mode needs an activated license on the machine. Hub personal sign-in works for a logged-in interactive user; unattended/service runs can fail with "no valid license". Test once: `& $env:UNITY -batchmode -nographics -quit -projectPath <p> -logFile -` and check for `Licensing`/`entitlement` errors. I
- Only one Unity instance per project: batch builds cannot open a project that the interactive Editor/MCP session has open. Use a **separate clone/worktree for local batch runner builds** (`git worktree add ../_ci_build`), or close the Editor. V rule of Unity, I application.
- Pin Unity per project via `ProjectVersion.txt`; local batch runner script resolves the exe from it:
  `$v=(Select-String m_EditorVersion ProjectSettings\ProjectVersion.txt).Line.Split(' ')[1]` -> `C:\Program Files\Unity\Hub\Editor\$v\Editor\Unity.exe`.

### 2.2 Build entry point `Game.EditorTools.BuildCli` (static class in `Assets/_Game/Scripts/Editor/Build/`) I

| Method | Purpose |
|---|---|
| `Bootstrap()` | applies `BuildSettingsApplier`, creates folders/scenes if missing |
| `BuildAndroidAab()` / `BuildAndroidApk()` | release AAB (store) / dev APK (device tests) |
| `RunPreflight()` | the gates in 2.5, exit code != 0 on failure |

Command-line args parsed from `Environment.GetCommandLineArgs()`: `-buildVersion 1.2.0 -buildNumber 57 -outputDir Builds/ -development -scenes Boot,Home,Game`. Secrets are read from env vars (`KEYSTORE_PATH`, `KEYSTORE_PASS`, `KEY_ALIAS`, `KEY_PASS`), set into `PlayerSettings.Android.keystoreName/keystorePass/keyaliasName/keyaliasPass` in memory only, **never logged**. Exit with `EditorApplication.Exit(0|1)`; wrap in try/catch so a build failure returns 1, not a hung editor.

Core of the method (shape, not full code):

```csharp
var opts = new BuildPlayerOptions {
  scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
  locationPathName = Path.Combine(outDir, $"{product}-{ver}-{num}.aab"),
  target = BuildTarget.Android,
  options = development ? BuildOptions.Development : BuildOptions.None };
EditorUserBuildSettings.buildAppBundle = !apk;
EditorUserBuildSettings.androidCreateSymbols = AndroidCreateSymbols.Public; // symbols zip beside the aab (not inside)
PlayerSettings.bundleVersion = ver; PlayerSettings.Android.bundleVersionCode = num;
var report = BuildPipeline.BuildPlayer(opts);
File.WriteAllText(outDir+"/build-report.json", JsonUtility.ToJson(Summarize(report)));
EditorApplication.Exit(report.summary.result == BuildResult.Succeeded ? 0 : 1);
```

### 2.3 Invocation

```powershell
& $env:UNITY -batchmode -nographics -quit -projectPath $proj -buildTarget Android `
  -logFile Logs\build.log -executeMethod Game.EditorTools.BuildCli.BuildAndroidAab `
  -buildVersion 1.2.0 -buildNumber 57 -outputDir Builds
# $LASTEXITCODE: 0 ok, 1 build error, other = Unity crash/license -> inspect Logs\build.log
```
Do not pass `-quit` together with async work that spans frames; keep builds synchronous inside one method. Do not use `-nographics` for tests that need rendering (PlayMode with cameras: omit it). I

### 2.4 Versioning (single source) I

- Source of truth: `project.config.json` `version` (semver, human edits on release) + build number from local batch runner (`local build counter`, or local counter file `qa/.buildnumber` that is git-tracked and incremented only by `release.ps1`).
- `versionCode` must be strictly increasing per Play app. Derive: `major*1_000_000 + minor*10_000 + patch*100 + hotfix` OR plain monotonically increasing integer; pick one in the template and never mix. Tag git with `v1.2.0+57` after a successful release build (only when the user asks to commit/tag).

### 2.5 Android templates and size-relevant settings (`Assets/Plugins/Android`)

Keep the templates from the studio set (V names above): `mainTemplate.gradle`, `baseProjectTemplate.gradle`, `gradleTemplate.properties`, `proguard-user.txt`, `AndroidManifest.xml`. Template baseline I:
- `gradleTemplate.properties`: `android.useAndroidX=true`, `android.enableJetifier=false` unless a legacy SDK forces it (verify), `org.gradle.jvmargs=-Xmx4096M`, `unityStreamingAssets=`.
- `mainTemplate.gradle`: `minifyEnabled` true for release only when keep rules for ads/analytics SDKs are in `proguard-user.txt`; `ndk { debugSymbolLevel 'SYMBOL_TABLE' }` (or FULL for crash tools).
- Manifest: remove unused permissions with `tools:node="remove"` (e.g. `READ_PHONE_STATE`, `AD_ID` only if ads need it declared, keep `com.google.android.gms.permission.AD_ID` when ads/analytics used), keep the `hardwareAccelerated` post-processor from ME (V `AndroidHardwareAccelerationPostprocessor`) only if native video ads need it.
- Play 16 KB page-size: Unity 6000.x+ engine builds are compatible; third-party `.so`/`.aar` (e.g. `googlemobileads-unity.aar`, Adjust, Firebase) must be 16 KB aligned: verify with `zipalign -c -P 16 -v 4 app.aab-extracted.apk` / Play Console pre-launch warnings. Verify latest policy at release time. I

### 2.6 Tests

```powershell
& $env:UNITY -batchmode -projectPath $proj -runTests -testPlatform EditMode `
  -testResults Logs\editmode.xml -logFile Logs\test-edit.log
& $env:UNITY -batchmode -projectPath $proj -runTests -testPlatform PlayMode `
  -testResults Logs\playmode.xml -logFile Logs\test-play.log
```
`-runTests` does not combine with `-quit`. Exit code 2 = tests failed, 0 = ok. Parse NUnit XML in `qa/test.ps1` into a one-line summary. Template tests (must exist from day 1): compile-clean smoke, "Boot scene loads", `Factory_*` singletons have no duplicate/missing IDs, UI validator (from `unity-ui`) over all prefabs, collision registry sanity. I

### 2.7 Addressables (only if used)

Content build before the player build, in the same Editor session: `AddressableAssetSettings.BuildPlayerContent()` called from `BuildCli` before `BuildPipeline.BuildPlayer`; `ProfileSettings` select the release profile; remote catalog URL from config (not hardcoded). Skip entirely for games under the size budget (6.1): small games use scenes + Resources-free direct references. I

### 2.8 Symbols and size report

- Symbols: `androidCreateSymbols = Public` produces `*.symbols.zip` next to the AAB; upload it to Play Console (native crash deobfuscation) and keep a copy in artifacts. Keep the IL2CPP `mapping`/`proguard mapping.txt` (when minify on) beside the AAB. I
- Size report `qa/size-report.py`: (a) AAB zip size; (b) **estimated download size** = sum of base split for arm64 (use `bundletool build-apks --mode=universal` is the upper bound; `bundletool get-size total` for device-spec estimate; bundletool is a Java jar and needs Java: use the Unity-bundled `OpenJDK\bin\java.exe`, V path); (c) top-30 assets from `BuildReport` (`report.packedAssets`) written to `build-report.json`; (d) compare with `qa/gates.json` budget and with the previous release's JSON, fail on > +5% or over budget. I

## 3. Preflight gates (single command `qa/preflight`)

Fail-fast order, each prints one line, all exit-code based:

1. Git clean (except `Builds/`), lock file present, framework dependency pinned (no `#main` / no ref). I
2. Unity compile clean, zero Console errors (batch log scan for `error CS`, `Missing script`, `The referenced script`).
3. EditMode tests; PlayMode smoke (Boot -> Home -> Game starts, 10 s no exceptions).
4. Static checks: no `Debug.Log` flood in Update, `DEVELOPMENT_BUILD` cheats excluded in release, `Resources` folder size, no `*.keystore`/`google-services.json` staged (gitleaks-style grep, section 5).
5. UI validator (`unity-ui` skill) all screens at 3 aspect ratios.
6. Build -> size budget -> symbols present.
7. Device smoke (manual or ADB: see 3.1).

### 3.1 ADB smoke (optional, device connected) I

```powershell
$adb="C:\Program Files\Unity\Hub\Editor\6000.3.22f1\Editor\Data\PlaybackEngines\AndroidPlayer\SDK\platform-tools\adb.exe"  # V dir exists
& $adb install -r Builds\game.apk
& $adb shell am start -W -n com.company.game/com.unity3d.player.UnityPlayerGameActivity   # prints TotalTime = cold start ms
& $adb shell dumpsys meminfo com.company.game | Select-String "TOTAL PSS"
& $adb logcat -d -s Unity AndroidRuntime | Select-String "FATAL|Exception"
```
`am start -W` TotalTime is the cold-start number used in the startup budget (6.2). Activity class depends on the Unity version (V: ME post-processor handles both `UnityPlayerActivity` and `UnityPlayerGameActivity`).

## 4. local batch runner

### 4.1 Decision: self-hosted Windows runner first, local unattended run optional

| Option | For | Against | Verdict |
|---|---|---|---|
| **Self-hosted runner on this PC** (remote workflow service runner service, or plain local `qa/*.ps1`) | Uses installed editors, Android SDK/NDK/JDK bundled (V), no license activation dance, warm `Library/` cache = fast incremental builds, free | PC must be on; license must work for the service account; one runner = serial builds; trust: only run on private repos / protected branches | **Default** |
| local unattended run (`local unattended run/unity-builder` + `unity-test-runner` on `ubuntu`/hosted runners) | Reproducible container, no machine dependency | Requires activation via `UNITY_LICENSE` (.ulf, Personal needs manual license request flow) or `UNITY_EMAIL/PASSWORD/SERIAL` (**Plus/Pro/serial only**; cannot assume this studio's license type: no `.ulf` found here), cold `Library` each run unless cached, hosted runner minutes + large images (>10 GB with Android), IL2CPP Android builds are slow | Only if a serial/Pro seat exists; verify license type first |
| Local runner without GitHub (`qa/build.ps1` triggered by hand or by Task Scheduler) | Zero infra | No PR gating | Fallback, same scripts |

Whichever is chosen the **logic lives in `qa/*.ps1` + `BuildCli`**; the workflow YAML only calls them. That keeps one implementation for local, self-hosted and local unattended run. I

### 4.2 Workflow sketch (`.github/workflows/local-build.ps1`, self-hosted)

```yaml
name: ci
on: { pull_request: {}, push: { branches: [main] } }
concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }
jobs:
  verify:
    runs-on: [self-hosted, windows, unity]
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true, clean: false }     # clean:false keeps Library/ cache
      - run: ./qa/test.ps1 EditMode
      - run: ./qa/test.ps1 PlayMode
      - run: ./qa/preflight.ps1
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: logs, path: "Logs/*.xml\nLogs/*.log", retention-days: 7 }
  release:                                    # release.yml: workflow_dispatch / tag v*
    # needs: verify; env from runner-local secrets file or GH Secrets (section 5)
    # steps: ./qa/build.ps1 -Aab -Version $v -Number ${{ local build counter }} ; size gate ; upload aab + symbols + build-report.json
```
Caching: self-hosted keeps `Library/` in the workspace (set `clean:false`, never `git clean -x`); local unattended run would use `actions/cache` on `Library/` keyed by `hashFiles('Packages/packages-lock.json','ProjectSettings/ProjectVersion.txt')`. Gradle cache = `%USERPROFILE%\.gradle` persists on self-hosted. I
Safety: local machine runner executes PR code: restrict to `pull_request` from the same repo, no forks, repo private. I

### 4.3 Quality gates (configurable in `qa/gates.json`)

| Gate | Default threshold | Source |
|---|---|---|
| Compile + EditMode + PlayMode smoke | all pass | 2.6 |
| UI validator | 0 errors (warnings listed) | skill `unity-ui` |
| AAB size | <= budget (6.1), regression <= +5% | 2.8 |
| Startup (device ADB) | cold start <= budget (6.2), only if device present | 3.1 |
| Perf budget (batches/SetPass/GC per frame in a scripted PlayMode run on Game scene) | see 6.3; measured in Editor = indicative, flag as such | `mobile-perf-audit` |
| Secret scan | 0 hits | section 5 |

Perf numbers measured in Editor are not device numbers: mark them "indicative" in the report (house rule: no perf claims without evidence). I

### 4.4 Unattended Claude headless steps (`claude -p`) I

`claude` 2.1.296 is installed (V). Use it for *judgement tasks only*, never for deterministic steps (build, test, upload are scripts).

```powershell
claude -p "Read Logs/test-edit.log and Logs/build.log. Fix only compile errors caused by files changed in this branch. Do not touch ProjectSettings, scenes, prefabs or keystores. Do not commit." `
  --allowedTools "Read,Edit,Grep,Glob,Bash(git diff:*),Bash(git status:*)" `
  --max-turns 12 --output-format json > Logs/claude-fix-1.json
```
Loop contract in `qa/fix-loop.ps1`:
- **Iteration cap 3** (compile-fix loop) and **cap 2** (test-fix loop); each iteration = claude fix -> rerun the failing gate. After the cap: stop, upload logs, mark job failed. No infinite retries.
- Per-call `--max-turns` 8-15 and a wall-clock `timeout-minutes` on the step; budget cap via `--max-budget-usd` if available in the installed version (check `claude --help`; not verified here).
- Fixes go to a **new branch / working tree diff**, never auto-merged; the PR needs human review. Never `--dangerously-skip-permissions`; restrict tools by allow-list (above).
- Other good headless uses: release notes from `git log`, store listing text drafts, log triage (`unity-log-triage`), diff review before release. Not for: signing, upload, publishing, changing ProjectSettings.
- Parallel-agent rule: local batch runner works in its own worktree; agents re-read before editing (AGENTS.md "never overwrite newer work"). V

## 5. Secrets: process (short)

1. **Every app has its own keystore and keys.** Never reuse a keystore across apps; never share one Play signing identity. Prefer **Play App Signing** (Google holds the app signing key; you keep only an *upload key*, resettable if lost).
2. **Template contains only placeholders**: `qa/secrets.example.json`, `SdkKeys.example`, `REPLACE_ME`. Real values live in `secrets.local.json` (untracked, in `.gitignore`) or env vars; on local batch runner in local environment variables / runner-local env. Keystore file stored **outside the repo** (e.g. `C:\Keys\<app>\upload.jks`) + a copy in the studio's password manager.
3. `Upstore/` and `*.keystore/*.jks` are ignored from day one; KT/ME track them today (V): rotate to Play App Signing upload keys and `git rm --cached` is a separate, user-approved task (never done by an agent unasked).
4. Generation is **human-run**: `keytool` is available in the bundled JDK (V `OpenJDK\bin`); the agent prepares the command, the human enters passwords. Agents never read, print or paste keystore/passwords/tokens; build logs are scanned for the password strings.
5. SDK ids (MAX key, Adjust token, ad unit ids, `google-services.json`) are *app identifiers, not strong secrets*, but still per-app and not template defaults; KT hard-codes a default MAX key literal in `BounceConfig.cs` (V): remove in the template.
6. Pre-commit/local batch runner secret scan: grep for `*.keystore`, `storePassword`, `keystorePass`, `google-services.json` in staged files and for high-entropy strings. Fails the gate.
7. Lost keystore (non-Play-App-Signing) = cannot update the app. Back it up before first upload.

## 6. Budgets for low-end Android

Baseline device class (I): 3 GB RAM or less, Cortex-A53 era, Mali-G52/Adreno 506, Android 8-10. Numbers are **proposed starting budgets**, to be replaced by measurements on a real low-end device (house rule).

### 6.1 Size

| Item | Budget | Notes |
|---|---|---|
| Store download (AAB -> device estimate) | **<= 150 MB** hard, **<= 80 MB** target for casual/hypercasual | Play base-module limit is 200 MB compressed (I: verify current policy); smaller = better install conversion |
| Empty template build (Unity 6 + URP, ARM64, strip) | ~25-35 MB (I, measure and record in template `gates.json`) | any game over this is content or SDK |
| SDKs (MAX + adapters + Adjust + Firebase) | <= 15-20 MB combined | measure by size diff with/without; drop unused ad networks |
| Textures | ASTC 6x6 default, 4x4 only for UI/hero; max texture 1024 for props, 2048 only for atlases; mipmaps on 3D, off for UI | |
| Audio | Vorbis ~q0.3-0.5 or AAC; music streaming; SFX short mono 22-44 kHz; total <= 15 MB | |
| Meshes | read/write off, compression on, no unused LODs; per-model <= 10k tris mobile | |
| Shaders | strip unused variants (URP shader stripping settings, prewarm only what is used) | big hidden cost |
| Scripting | IL2CPP stripping Medium/High, `link.xml` for reflection; `libil2cpp.so` ARM64 only | KT uses High (V) |
| Per-release regression | <= +5% vs previous | gate in 4.3 |

### 6.2 Startup (cold start, `am start -W` TotalTime, V method in 3.1)

| Phase | Budget on low-end |
|---|---|
| Process start -> first Unity frame (engine splash) | <= 2.5 s (Unity splash screen counts; disable if license allows) |
| Boot scene -> interactive Home | <= 3 s additional |
| **Total cold start to interactive** | **<= 6 s target, <= 8 s hard fail** |
| Warm resume | <= 1.5 s |

How: keep Boot scene tiny; Data load synchronous only for save file; ads/analytics/consent init async and non-blocking (but consent resolved before first ad request); no `Resources.LoadAll`; Addressables/prewarm shaders behind a loading bar rather than before first frame; avoid scenes loaded in Awake chains; mesh combining and heavy one-time cost behind loading screen (house rule). I

### 6.3 Runtime budgets (for `mobile-perf-audit` and 4.3)

Targets 30-60 fps; frame <= 16.6 ms (60) or 33 ms (30) on the baseline device. SetPass+batches: <= 100-150 batches, <= 60 SetPass; GC alloc per frame: **0 B** in steady gameplay; triangles <= 150-300k; RAM PSS <= 700 MB (hard 1 GB on 3 GB device, survive backgrounding); heat/battery: no thermal throttle in 10 min. I (derived from house rules; replace with measured values).

## 7. Store release checklist

Legend: **A** automatable by script/local batch runner, **H** human only, **A+H** script prepares, human approves. Nothing is uploaded or submitted without explicit user approval (house rule, V `mobile-build-release`).

### 7.1 Google Play (primary)

| Step | Mode | Notes |
|---|---|---|
| Developer account, payments profile, 2-step verification | H | one-time. New personal accounts must run **closed testing with a minimum tester count for a minimum period before production** (verify current numbers in Play Console) |
| Create app (name, language, free/paid, category) | H | |
| App signing: opt in to Play App Signing, upload key cert | H | section 5 |
| Build AAB, versionCode increasing, targetSdk meets current Play requirement, 64-bit (ARM64 present, V), 16 KB aligned native libs | **A** | gates 2.5/4.3; verify policy dates at release time |
| Upload symbols zip, mapping.txt | A+H | `fastlane supply` or Play Developer API with service account (**not installed**, I); else manual |
| Store listing: title <=30, short desc <=80, full desc <=4000, original naming (`clone-ip-safety`) | A+H | agent drafts text into `docs/store/listing.md`; human pastes/approves |
| Graphics: icon 512x512 PNG, feature graphic 1024x500, phone screenshots (min 2, 16:9 or 9:16, sides 320-3840 px), 7"/10" tablet shots if tablet-supported | A+H | screenshots can be captured by a PlayMode script / `adb shell screencap`; art review is H |
| Content rating questionnaire (IARC) | H | answers drafted by agent from `docs/store/rating-answers.md` |
| Data safety form | A+H | draft from SDK inventory: ads (device ID, usage), Adjust/Firebase analytics, IAP; must match privacy policy and what SDKs actually collect |
| Ads declaration, target audience (children => stricter ads/analytics rules; avoid targeting <13 unless designed for it), app access, news/health/financial declarations | H | |
| Privacy policy URL (public page) | A+H | template at `docs/store/privacy-policy.template.md` listing: data collected by ad/analytics SDKs, ID for advertising, retention, contact email, children statement, deletion request path, third-party links (AppLovin, Adjust, Google). Host as GitHub Pages; fill company/app placeholders |
| UMP/GDPR consent, `app-ads.txt` on developer website (for ads) | A+H | |
| IAP: create products in Console matching `IAPCatalog` ids; license testers | H | |
| Testing tracks: Internal (up to 100 testers, minutes to publish) -> Closed -> Open -> Production staged rollout (5-20%) | H to promote; A for upload if API set up | always internal first |
| Pre-launch report (Firebase Test Lab) review, crash/ANR check in Android vitals after rollout | H | |

### 7.2 App Store (basics, Unity)

Needs macOS + Xcode: **not available on this Windows machine** (V: `iOSSupport` module exists only for 6000.3.22f1, but no Mac toolchain); use a Mac runner or Unity Build Automation. I
- Build Xcode project from batch (`-buildTarget iOS`), sign in Xcode/local batch runner with team provisioning; certificates not in the repo.
- Apple Developer Program, App Store Connect record, bundle id, **Privacy manifest** (`PrivacyInfo.xcprivacy`) for SDKs and "required reason" APIs, ATT usage description if tracking (and ATT prompt before ads personalization), usage strings only for used capabilities, App Privacy "nutrition labels", age rating, screenshots per required device size (6.9" and 13" iPad if supported), icon 1024x1024 without alpha, review notes + demo account if needed, TestFlight internal/external before release.
- Modes: build/archive/upload via `fastlane` or `xcrun altool/notarytool` on a Mac = A; store forms and review = H.

### 7.3 Pre-release device checklist (H, from `unity-qa-playtest`)
Low-end + modern device: cold start time vs 6.2, backgrounding/memory, FPS, heat 10 min, ad and IAP test flows in test mode, consent flow, offline start, back button behaviour, safe area on notch.

## 8. Automation matrix

| Task | Who/what | Status |
|---|---|---|
| Create repo from template, rename, apply ProjectSettings | `new-game.py` + `BuildCli.Bootstrap` | to build |
| Compile/test/UI validate/size/startup gates | `qa/*.ps1`, `BuildCli`, runner | to build |
| AAB/APK build, versioning, symbols | `BuildCli` | to build |
| Compile-fix / test-fix loops, release notes, listing drafts | `claude -p` with caps (4.4) | to build |
| Keystore creation, secrets provisioning | human | process (5) |
| Play Console forms, content rating, promotion, review | human | manual |
| Play upload | fastlane supply / API, only on explicit user command | optional, later |
| iOS | Mac required | deferred |

## 9. Gaps / risks found

1. No local batch runner, no build script, no template repo exist (V). The studio ships by hand in the Editor.
2. Keystores in git, unpinned framework `#main`, `ProjectVersion.txt` ignored (V catalog 08/manifest): all contradict reproducible, safe release.
3. Unity batch cannot share a project with the open interactive Editor/MCP session: needs a separate worktree (2.1). I
4. Licensing type unknown; batch/local batch runner may need a serial or Hub login: test before choosing local unattended run (4.1). I
5. `gh`, `java` (system), bundletool, fastlane not installed; the bundled JDK can run bundletool (V JDK path). I
6. Android SDK `platforms/` was empty in 6000.3.22f1's bundled SDK on this machine at check time (V: listing printed no platform dirs), so first build may download or fail when offline; run a smoke batch build early. I

## Proposed classification

| Item | Class | Proposed name |
|---|---|---|
| Template repo (layout, ProjectSettings baseline, asmdefs, gitignore/LFS, null SDK interfaces, Boot scene, tests) | DATA/TOOL | `game-template-unity` (repo) |
| One-command new-game creation + safe rename procedure | RECIPE | `new-game-from-template` |
| `BuildCli` + `BuildSettingsApplier` editor scripts (batch AAB/APK, version, symbols, size report, exit codes) | TOOL | `unity-batch-build` (script set in `qa/`) |
| Preflight gates + budgets file (`gates.json`) + local batch runner workflow + `claude -p` capped fix loop | SKILL | `unity-ci-quality-gates` |
| Store release checklist with automatable vs manual split, listing/privacy/data-safety templates | SKILL | extend `mobile-build-release` (add commands, 16 KB, Play App Signing, tracks); templates as DATA in `docs/store/` |
| Secrets rules (per-app keys, placeholders, local untracked, no agent access, no keystores in git) | RULE | `secrets-per-app` (add 6 lines to global AGENTS.md) |
| Size and startup budgets for low-end Android | DATA | `mobile-budgets.json` (read by gates and `mobile-perf-audit`) |

Must-haves (in order):
1. `BuildCli` batch build with env-var signing + exit codes + version/versionCode single source (nothing else works without it).
2. Template repo with pinned framework (`com.sketchengine#tag`), committed lock file, `.gitignore` that excludes keystores/secrets.
3. `new-game-from-template` procedure including placeholder secrets and the human TODO list.
4. Preflight: compile/test/size gates and `gates.json` budgets; run on a local machine runner or local script using a separate worktree.
5. `secrets-per-app` rule + secret scan gate; rotate away from tracked keystores (user-approved task).
6. Extended `mobile-build-release` with Play checklist (target API, 64-bit, 16 KB, tracks, data safety, privacy policy template) and the A/H split.
