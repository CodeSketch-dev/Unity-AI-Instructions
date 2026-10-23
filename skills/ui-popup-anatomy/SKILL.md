---
name: ui-popup-anatomy
description: Popup prefab tree, animation modules and timings, dim, Escape stack and page-vs-popup distinction. Use when building or fixing any popup, confirm dialog or full page.
---

# Popup anatomy

From knife-tower / monkey-escape (report 07, VERIFIED). The reference wins when it differs; the standing look defaults are in `ui-style-rules`.

## Tree
`Feature_Popup (Popup + CanvasGroup, stretch) > Root (stretch) > [Scale (fixed size = board + margin, the scale-animation target)] > Board (sprite) > Btn_Close / Title / content (ScrollRect, Layout HLG, action Btn_*)`. 94% of popups have `Root`, 75% a `Board`. No Canvas on the popup. Instantiate per open under the popup root with `PopupManager.Create(prefab)` (HUD buttons use `PopupButtonOpen` with a serialized prefab, zero code); destroy on close, never pool.

## Behavior (framework `Popup`)
- Push on enable; `Close()` plays the sequence backwards then destroys. Not interactable until the open ends.
- **Escape / Android Back closes the top popup only**; lower popups are disabled while one is on top. No per-screen Back handlers; HUD views have no back.
- Modules: Background (full-stretch dim as a sibling behind, fades to its alpha, click closes), Scale (0.3 -> 1, OutBack), Fade (CanvasGroup). Defaults: open/close 0.1/0.1 (~70%), big popups 0.3/0.2; ignore-time-scale off. Dim alpha observed 0.94 (most), 0.86 inventory, 0.706 settings, 0.5 debug; the team default in `ui-style-rules` is black 220/255.
- Ad/revive popups add `PopupButtonNoThanks`: appears after open + 0.5 s, scale 0 -> 1 in 0.25 s.
- Depth-of-field post trigger while open exists on 12 popups (optional).

## Sizes seen (1920x1080 reference; soft defaults)
Boards 1146x754 / 1154x768-800 large, 800x650 settings, 665x512 confirm, 528x435 and 525x370 mini, 1432x743 hero. `Btn_Close` 97x93 (or 100x100) top-right, inset about 65-70. Row/card prefabs are separate `<Feature>_Item.prefab` files; per-state variants are child objects toggled with SetActive.

## Page vs popup
Page: title bar (~175 high) + `Btn_Back` (~103x107) + Background + SafeArea; use for tabbed or scrolling content. Popup: floating Board + `Btn_Close`; use for confirmations and short offers.

Framework APIs differ slightly by version (`framework-version-map`); read the installed `Popup` before writing.

## Close during open animation
Frameworks may ignore `Close()` while the open tween plays. Owners: never consume state or set a busy flag before the close succeeded; retry Close next frame until the popup is gone. Test drivers: wait for the open tween (up to ~8 s) before the first tap.

- Text centring: Capline alignment plus the sprite face offset, never a per-label nudge (`ui-text-tmp` Optical centring).

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.
