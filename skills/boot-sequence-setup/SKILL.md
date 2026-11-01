---
name: boot-sequence-setup
description: "Set up or debug game boot order: data preload/warmup, one-time init hooks, settings-to-audio binding, static resets. Use when adding startup code or when a save, factory or manager is not ready at startup."
---

# Boot sequence setup

No single Bootstrap object exists in the reference projects; init is spread over static hooks plus lazy singletons (report 01).

## Order in knife-tower / monkey-escape (v1, VERIFIED)
1. `RuntimeInitializeOnLoadMethod` stages: `SubsystemRegistration` (static resets) -> `BeforeSplashScreen` -> `BeforeSceneLoad`.
2. Scene 0 = BounceSdk Splash. It calls `SplashScene.DevInitConfig()` -> `DataBlockPreloader.PreloadAll()` (reflection scan of the game assembly, reads every `DataBlock<>` `Instance`) so saves load behind the splash. monkey-escape has no preload (lazy).
3. Splash -> `LoadSceneAsync(1)` = Home.
4. `GameMasterInit.RuntimeInit` (`AfterSceneLoad`; fires after the FIRST scene load): frame rate, `DevicePolicy`, copy `DataSettings` volumes into `AudioManager.VolumnMusic/VolumeSound` and subscribe for changes, `Taptic.tapticOn`.
5. Singletons are lazy: factories load on first static access; `MonoCallback` is created by the first DataBlock `Init`; the Audio pool by `AudioManager.SafeInstance`.

## v2 difference
`DataBlockWarmup` runs automatically at `BeforeSceneLoad` (generated registry or reflection scan), so no hand-written preloader. Switch: `DataWarmupConfig.Enabled`.

## What to do
- v1 project: add a `DataBlockPreloader` template and call it from the splash hook. v2: do nothing, just inherit `DataBlock<T>`.
- Put one-time init in an `AfterSceneLoad` hook like `GameMasterInit`; settings -> audio/taptic binding is project code, not framework.
- Reset statics at `SubsystemRegistration`; static subscriptions made in `RuntimeInitializeOnLoadMethod` accumulate across Play sessions when domain reload is off.
- Anything touching a DataBlock in `BeforeSplashScreen`/`SubsystemRegistration` loads it before the splash.
- Unverified: whether `AfterSceneLoad` really precedes Home (Unity semantics, not tested in the Editor).

## Gotchas (runtime manager to scene-authored)
- Converting a runtime-created manager: serialize its reference on the Master, `FindSceneAuthored` first, and keep runtime creation only as an Editor/test fallback. See `scene-authored-prefabs`.
