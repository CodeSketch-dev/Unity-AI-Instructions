# Persistent root hierarchy (text tree)

Legend: `[P]` = nested prefab instance; `active=0` = inactive in the prefab.

```
GameSingleton                 GameSingleton : MonoSingleton<GameSingleton> (PersistAcrossScenes = true)
|- EventSystem                EventSystem + InputSystemUIInputModule (default UI actions asset)
|- Manager
|   |- FpsUnlock              target 60, vSync 0
|   |- GameManager            MonoSingleton, central ticker + StaticBus subscriptions
|   |- <Feature>_Manager      one per game-wide system (item, input, ...) - each its own component
|   |- Pool                   Pool_Manager (reads the pool config factory, inits the global pool once)
|   |- IAP                    IAP listener + IAP manager
|   |- GlobalFx [P]           global VFX holder
|   '- Quest_Arrow [P]        world guide arrow (hidden until used)
|- Canvas                       HUD, sort 2506
|   '- Root (stretch)
|       |- OverlayColor         Image alpha 0, raycast OFF + tint script
|       |- CutSceneFocus        two black bars Top/Bottom, 125 px, raycast ON
|       |- SafeArea             stretch + UISafeArea (conform X/Y)  -> HUD prefab [P] goes here
|       '- Notification_Warning Root(active=0) -> Content -> bands (Icon + Text)
|- Canvas_Popup                 popups + views, sort 12506, UIGlobalCanvas
|   |- Root (stretch)
|   |   |- ViewContainer        ViewContainer + UISafeArea
|   |   '- PopupRoot            PopupRootSetter (registers itself as PopupManager root)
|   |- OverlayContainer         empty stretch rect (fly-to FX; focus/tutorial overlays are parented here)
|   |- LoadingScene             LoadingScreen; Root(active=0)+CanvasGroup -> Background(AspectRatioFitter Envelope), Progress(Fill + Text)
|   |- UI_Internet_Popup        connectivity monitor; Root(active=0) -> Board -> Frame, Title, states, Btn_TryAgain
|   '- Ads_NativeSlot           rect anchored right edge (pivot 1,0.5), resized at runtime
'- Transition [P]               transition animator + scene loader; own Overlay canvas sort 20000 -> Screen RawImage
```

Counts to expect: 3 canvases, 1 EventSystem, 0 cameras, 0 audio components, 3-4 nested prefabs.
Every Canvas/view/popup child keeps exactly one empty stretch `Root` child (see `unity-ui`).
