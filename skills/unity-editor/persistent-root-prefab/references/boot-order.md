# Boot order with a persistent root

1. `RuntimeInitializeOnLoadMethod(SubsystemRegistration)`: reset static caches and registries (domain-reload-off safe).
2. `BeforeSplashScreen` / `BeforeSceneLoad`: catalog loads without scene objects only. The framework data warmup (`DataBlockWarmup`) runs here automatically, so saves are ready before any scene object (check the installed package; older framework versions need a hand-written preloader called by the boot controller).
3. First scene (index 0, boot) loads. Every `MonoSingleton<T>` Awake runs first (`DefaultExecutionOrder(-50)`): the root registers itself and calls `DontDestroyOnLoad`.
4. `RuntimeInitializeOnLoadMethod(AfterSceneLoad)` init class runs after the FIRST scene is loaded and before the next scene is requested: frame rate (mobile `min(refresh, 60)`, vSync 0), device policy (edits the active URP asset properties, never assigns the pipeline: `device-tier-policy`), settings binding (volume and vibration values into the audio manager).
5. `Start` pass: popup root registers (`PopupRootSetter` -> `PopupManager.SetRoot`), frame-rate unlock, game manager shows the banner, IAP wires, items restore.
6. Boot controller finishes its gate (logo time, privacy, warmup) and loads Home as a Single-mode scene. The Home copy of the root destroys itself.
7. Home -> minigame goes through the loading screen (heavy) or the transition loader (light). The new scene's master registers load tasks in `Awake` (`scene-flow-loading`).
8. Return to Home posts a StaticBus event; managers reset their per-session state.

Rule: no code relies on the order of `Start` between root children; use `Awake` for self-setup and events for cross-talk.
