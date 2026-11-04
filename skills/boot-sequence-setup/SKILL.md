---
name: boot-sequence-setup
description: "Set up or debug game boot order: persistent root prefab as the bootstrap, data preload/warmup, one-time init hooks, settings-to-audio binding, static resets. Use when adding startup code or when a save, factory or manager is not ready at startup."
triggers: boot, startup, init order, awake order, runtimeinitializeonloadmethod, afterSceneLoad, preload, warmup, static reset, khoi dong, thu tu khoi tao, kt style
---

# Boot sequence setup

The bootstrap IS the persistent root prefab (`GameSingleton`, see `persistent-root-prefab`): a scene-authored object placed in the boot scene whose duplicate copies destroy themselves. Initialization is spread over it, its `Manager` children and a few static hooks. There is no code-created bootstrap object.

## Order (reference style, verified)
1. `RuntimeInitializeOnLoadMethod`: `SubsystemRegistration` (static resets) -> `BeforeSplashScreen` (static catalog loads, e.g. a product catalog) -> `BeforeSceneLoad`.
2. Scene 0 (boot/splash) loads; every `MonoSingleton<T>` Awake runs first (execution order -50); the persistent root registers and calls `DontDestroyOnLoad`.
3. `AfterSceneLoad` init class (`GameMasterInit`) runs after the FIRST scene load and before Home is requested: frame rate, device policy, copy saved settings into audio volumes and haptics and subscribe for changes.
4. `Start` pass: popup root registers, frame-rate unlock, banner, IAP wiring, item restore.
5. The boot controller's hook (a `partial` class of the vendor splash, never edit the vendor file) preloads every `DataBlock<T>` save while the logo shows, waits its gate, then loads Home (`LoadSceneAsync(1)`).
6. Singletons that are not in the root are lazy: factories load on first static access; the audio pool is created by the audio manager's `SafeInstance`.
Diagram and the full chain: `persistent-root-prefab/references/boot-order.md`.

## SketchEngine form
`DataBlockWarmup` runs automatically at `BeforeSceneLoad` (generated registry or reflection scan), so no hand-written preloader: just inherit `DataBlock<T>`. Switch: `DataWarmupConfig.Enabled`. On the older CodeSketch v1 a hand-written preloader called by the boot hook does the same job (`framework-version-map`).

## What to do
- Put one-time init in an `AfterSceneLoad` hook (`GameMasterInit`); settings -> audio/haptics binding is project code, not framework.
- Reset statics at `SubsystemRegistration`; static subscriptions made in `RuntimeInitializeOnLoadMethod` accumulate across Play sessions when domain reload is off.
- Touching a DataBlock in `BeforeSplashScreen`/`SubsystemRegistration` loads it before the splash.
- Never rely on `Start` order between root children; cross-talk by StaticBus events.
- Check: Console empty from a cold start of each scene; saves ready before the first read; exactly one root and one EventSystem after Home (`persistent-root-prefab/references/verify.md`).

## Gotchas
- Converting a runtime-created manager to a scene prefab: see `scene-authored-prefabs` (one place, not duplicated here).
- Code after `base.Awake()` in a derived singleton still runs once in a duplicate root copy; guard with `Instance != this`.
