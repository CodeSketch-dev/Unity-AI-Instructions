---
name: ui-scaling-safe-area-checklist
description: "Checklist for UI that survives phone, tablet and notch aspect ratios: CanvasScaler, anchors and pivots, safe area, event-driven HUD, screen stack, text growth. Use when UI breaks on other resolutions or before sign-off of any screen."
triggers: canvas scaler, safe area, notch, aspect ratio, resolution, anchors, pivot, ui breaks, ui cut off, screen stack, back button, text overflow translation, 9:16, 9:20, tablet, man hinh, tai tho, bi cat, doi ty le
---

# UI scaling and safe-area checklist

Source: third-party example (concepts), rewritten for uGUI. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/game-ui-ux. Zone maps and sizes live in `mobile-hud-layout`; this is the verification checklist. UI tasks still start with `ui-always`.

## Checklist
1. **Scaler:** Canvas Scaler = Scale With Screen Size, reference set once per project, Match chosen deliberately (height-critical HUD leans to height). Never absolute pixel positions.
2. **Anchors and pivots:** anchor to the nearest edge/corner. A corner-anchored element that grows (longer translation, bigger font) needs its pivot on that same corner, or it grows off-screen.
3. **Safe area:** one SafeArea root under the canvas for interactive UI; decorative backgrounds may go full-bleed. Re-apply on orientation or resolution change.
4. **Layout groups over hand offsets;** let containers size to content; text uses autofit with a minimum, no ellipsis for key labels.
5. **Event-driven HUD:** subscribe to value-changed events and set text only when the value changes; no per-frame polling of game state.
6. **Screen stack:** push/pop for popups with one owner of the Android back button and input blocking; no boolean flag soup (`isPaused`, `inShop`).
7. **Touch targets:** primary actions big and in thumb reach; spacing between stacked controls at least 12 px at the 1080 reference; nothing in the banner zone.
8. **Text growth test:** swap to the longest language and 130% font; nothing clips or overlaps.
9. **Input focus:** if gamepad or keyboard is supported, one control is focused on open and navigation is defined; otherwise state that it is touch-only.
10. **Verify with captures:** 9:16, 9:20 (tall notch), 3:4 (tablet) and the landscape primary if used. Report what was seen at which size, with measured overlaps.

## Pitfalls
- Looks right only at the editing resolution.
- HUD under the notch or the system gesture bar.
- Popup centered on the full screen instead of the area above the banner.
- Old StandaloneInputModule left after switching to the Input System (UI stops responding).

Related: `mobile-hud-layout`, `unity-ui`, `ui-layout-audit`, `ui-text-autofit-system`, `ui-localization`, `native-ad-beside-popup`.
