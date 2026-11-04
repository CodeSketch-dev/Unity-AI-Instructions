# Two loaders in the persistent root

| | Loading screen (heavy) | Transition loader (light) |
|---|---|---|
| Use for | minigame / world entry with combine, warmup, big scenes | return to Home, small scenes, mode switches |
| Presentation | background art, progress bar with percent, optional native slot | fade out, load, fade in (full-screen RawImage or shader transition) |
| API shape | `LoadingScreen.Load(scene, onComplete, onBeforeLoad, background)`, `IsBusy`, `RegisterLoadTask(Func<IProgress<float>, UniTask>)` | `Load(scene, onBeforeLoad, onComplete)`, `Reload`, `FadeIn/FadeOut`, `IsBusy`, `BusyChanged` |
| Steps | fade the CanvasGroup in, mute audio, `LoadSceneAsync` with activation off up to 0.9, activate, wait N frames so the new scene registers tasks, run tasks to 100%, hold ~0.15 s, fade out, restore audio | play fade in, `onBeforeLoad`, `LoadSceneAsync`, `onComplete`, fade out |
| Lives in | `Canvas_Popup/LoadingScene` (sort 12506) | `Transition` (sort 20000) |

- Both are scene-authored children of the persistent root; their views are prefab hierarchies edited in Prefab Mode (never built in code). One shared busy gate: reject a second `Load` while either is busy.
- Which loader a destination uses is authored data on its selection asset (`Transition` or `LoadingScreen` load type); Home return always uses the light one.
- The loading screen is game-layer code in the reference (not in the framework package): write it once per studio as a reusable prefab + script and reuse it in every game; the fade transition may come from a vendor transition asset behind the same facade.
- Registration window: the new scene's master calls `RegisterLoadTask` in `Awake`; the loader waits a few frames (3 is enough in the reference) before closing the window, so register synchronously or document the window.
- Entering a mode: selection asset `Switch()` -> reset static game state -> resolve the scene -> loader. Returning home: post a StaticBus event; views close on `activeSceneChanged`.
- Verify with the repeated scene-flow test (`scene-teardown-safety`) and the timeline checks of SKILL.md section 4.
