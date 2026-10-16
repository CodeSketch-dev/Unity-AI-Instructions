# Knife Tower reference foundation profile

Verified from `D:\GitProject\knife-tower\knife-tower-troll-unity` (read-only):

- Unity 6, URP, Android low-end target, namespace `Game`.
- `Packages/manifest.json` uses CodeSketch v1 (`com.codesketch`); use `CodeSketch` namespaces and its actual generic APIs.
- `GameSingleton : CodeSketch.Mono.MonoSingleton<GameSingleton>` with `PersistAcrossScenes => true`.
- `UIGlobalCanvas : MonoSingleton<UIGlobalCanvas>` is persistent and exposes the authored global Canvas/container.
- `GameMasterInit` runs at `AfterSceneLoad`, applies mobile frame/physics/render policy, then initializes settings and runtime services.
- UI is owned by the persistent singleton prefab/canvas contract; use the project UI skills for exact hierarchy and TMP containment rules.
- Audio uses `Factory_Audio : ScriptableObjectSingleton<Factory_Audio>` with authored `AudioConfig` references, `AudioManager` playback and optional mixer override; `Audio_Volume` binds `DataSettings.SoundVolume` and unsubscribes in `OnDestroy`.
- BGM is centralized in `BGMHelper`: one current track, cancellable UniTask crossfade, default/fallback track, immediate stop and clamped volume/pitch. New features must not create ad-hoc BGM managers.
- Scene transitions use persistent `SceneLoaderPlus` with busy gating and fade callbacks; heavy scenes use persistent `LoadingScreen` with displayed-progress smoothing, scene activation, registered async load tasks and audio mute/restore.
- Settings/localization use `DataSettings` values and Unity Localization; locale-change subscriptions are paired in `Awake`/`OnDestroy`. UI text/font is resolved through `Factory_Localize`/localized TMP components.
- Camera is owned by `CameraManager`, communicates through `StaticBus` events, cancels owned async reposition work, and applies the low-end camera/device policy. Do not scatter `Camera.main` or camera reset logic through features.
- Pooling is global/config-driven: `Pool_Manager` initializes `Factory_Pool.Configs` once and calls `PoolPrefabGlobal.Init`; pooled prefabs require the framework pool component and validated prewarm/capacity.
- Feature UI commonly uses popup-owned components and event-driven bindings; buttons and popup close callbacks must be unsubscribed/owned by the popup lifecycle.
- Factories follow `Factory_* : ScriptableObjectSingleton<Factory_*>` (or serialized singleton when Odin dictionaries are required); data follows `DataBlock<T>`/`DataValue<T>`; events use `StaticBus<TEvent>`; feature state uses the installed state machine; repeated runtime objects use the existing pool.
- Collision must use the installed CodeSketch `OptCollisionRegister<T>`/sensor contract after confirming the exact package source; never add per-object `OnTriggerEnter` + `GetComponent` dispatch.
- Preserve feature-first folders under `Assets/_Game/Scripts`, `namespace Game`, cached references/`MonoCachedHub<T>`, PrimeTween preference, and low-end mobile budgets.

Unknowns remain explicit until package/API or Unity inspection confirms them.
