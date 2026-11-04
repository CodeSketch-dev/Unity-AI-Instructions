# Canvas reference (moved)

The canvas table (HUD 2506, popup 12506, transition 20000, scalers, safe area, raycast rules) now lives in `persistent-root-prefab/references/canvas-table.md`; the full tree is in `persistent-root-prefab/references/hierarchy-tree.md`.

Kept here (UI-specific facts):
- Per-mode HUD canvases (inside a player/GUI prefab): own Overlay canvas, sort 0, `SafeArea` holding joystick, action buttons, bars and a drag-look pad (right half anchored (0.5,0)-(1,1)); event-based, no per-frame work.
- Popup prefabs have NO Canvas of their own; they inherit the popup canvas. Fly-to FX items spawn into `OverlayContainer`; the loading screen sits under the popup canvas.
- `UISafeArea`: `Screen.safeArea` -> anchors, conform X/Y, re-checked each frame when refresh-on-update is on and applied only when the value changed; handles NaN anchors on some Samsung devices. Search the installed package for it before writing another.
- Banner clearance has no code in the reference (banner prefabs are ad-plugin canvases): the 200 px bottom clearance is a layout convention.
- World-space UI only for name tags and similar.
- Framework identity: one framework in several eras (older folder copy, `com.codesketch`, `com.sketchengine`); same type names, different namespaces. Resolve from the installed package (`framework-version-map`).
