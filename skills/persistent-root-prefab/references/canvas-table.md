# Canvas table (persistent root)

| Canvas | Render mode | Sort | Scaler | Notes |
|---|---|---|---|---|
| HUD `Canvas` | Overlay, no camera | 2506 | ScaleWithScreenSize 1920x1080, Expand, match 0, ref ppu 100 | Root: screen tint, cutscene bars, `SafeArea` with HUD, warning banner |
| `Canvas_Popup` | Overlay | 12506 | same | ViewContainer, PopupRoot, OverlayContainer, loading, internet popup, native slot |
| `Transition` | Overlay | 20000 | same | full-screen RawImage for the fade; nothing else |
| Per-mode HUD (inside a player/GUI prefab) | Overlay | below the persistent HUD (e.g. 0) | same | joystick, action buttons, bars; has its own SafeArea |
| Debug overlays / vendor splash | Overlay | at or above 10000 | vendor | not part of the root |

Layering low to high: scene content < per-mode HUD < persistent HUD 2506 < vendor popups ~10000 < popup canvas 12506 < transition 20000 < debug.
Any consistent order works as long as HUD < popup < transition < debug. Keep exactly these three overlay canvases in the root; do not add a fourth.

Safe area: `UISafeArea` (conform X and Y, refresh-on-update ON: it re-reads `Screen.safeArea`, size and orientation every frame and applies only when something changed) sits on `Canvas/Root/SafeArea` and on `Canvas_Popup/Root/ViewContainer`. `PopupRoot`, `OverlayContainer`, the loading screen, the tint and the cutscene bars are full-bleed on purpose.
Raycasts: tint image raycast OFF; cutscene bars raycast ON (block input while shown); loading `Root` CanvasGroup blocksRaycasts ON, interactable OFF.
Banner: ad banners are SDK overlays, not Unity UI objects here; keep 200 px bottom clearance by layout convention (`unity-ui`).
