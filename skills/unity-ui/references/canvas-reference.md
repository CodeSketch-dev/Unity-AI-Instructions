# Canvas reference (what the reference projects actually do)

Evidence: reports 06 and 07 (knife-tower and monkey-escape `GameSingleton.prefab`, VERIFIED). Use as defaults; `unity-ui` rules win when they differ.

| Canvas | Mode / sort | Contains | Per-frame work |
|---|---|---|---|
| HUD `Canvas` | Overlay / 2506 | `Root` > warning toast, screen-flash overlay, `SafeArea` (UISafeArea), cut-scene letterbox bars (125 high) | none |
| `Canvas_Popup` + `UIGlobalCanvas` | Overlay / 12506 | `Root/PopupRoot` (`PopupRootSetter`), `OverlayContainer` (fly FX), internet popup, loading scene; `ViewContainer` under this Root (INFERRED) | none |
| Per-mode `Player_GUI` | own Overlay canvas, sort 0 | `SafeArea` with joystick, action buttons, bars, drag-look pad | event-based |
| Third party | Transition 20000, Graphy 30000, ad prefabs 500/999 | | |
| World space | only name tags / a quiz prefab | | |

- Whole game = 2 persistent overlay canvases (inside a persistent `GameSingleton`) plus per-mode HUD canvases. Almost no world-space UI. Every CanvasScaler is ScaleWithScreenSize 1920x1080 Expand.
- Popup prefabs have NO Canvas of their own; they inherit the popup canvas. Order HUD < popup < transition < debug.
- Fly-to FX items spawn into the overlay container; loading screen sits under the popup canvas.
- `UISafeArea`: `Screen.safeArea` -> anchors, conform X/Y, refresh on enable and on screen-size/orientation change (not every frame); handles Samsung NaN anchors. Search for the installed one before writing another.
- Banner clearance has no code in the references (banner prefabs are ad-plugin canvases, sort 500): the 200 px bottom clearance is a layout convention.
- Joystick: an existing joystick pack behind the player GUI; the right half is a drag-look pad anchored (0.5,0)-(1,1).
- Framework identity: one framework in three eras (CFramework folder, `com.codesketch`, `com.sketchengine`); same type names, different namespaces. Resolve from the installed package (`framework-version-map`).
