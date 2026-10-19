---
name: ui-button-anatomy
description: "Required components and behavior of every button: press scale, click sfx on pointer down, grayscale disabled, per-state variants, notify dot, hit areas. Use when creating or auditing any button, tab or HUD icon."
---

# Button anatomy

From report 07 (counts over 223 KT / 184 ME button objects, VERIFIED).

- **Every button = Image + Button + press-feedback script + click-sfx script** (about 85% of buttons have both). Search the installed package first (`UIPressPrimeTween`, `AudioButtonSfx`) and reuse it; never write a second press script.
- Press feedback: scale to 0.9 in 0.1 s OutQuad, unscaled time, ignored when not interactable, reset on disable.
- Click sfx plays on pointer DOWN (not onClick), default from the audio mixer factory, skipped when not interactable. Needs a `Button` on self or children.
- **Disabled = grayscale material swap** on the button image and extra images, not a tint. Locked and unaffordable states are separate visuals (see `ui-scroll-board` state plates).
- **States as child objects** toggled by SetActive (`BtnClaim / Missed / Today / Claimed`), or sibling buttons per state; never one button with many conditional sprites.
- Role variants: popup opener (`PopupButtonOpen`), IAP button (store price text), non-Button touch areas for jump/attack/look (pointer click/drag components).
- **Notify dot**: child `Notify` ~40x41, anchored top-right (-10, -6.5), plain SetActive from a data event; no count, no tween; same on tabs.
- Attention loops only on the primary CTA (`game-feel-polish`); stop them on disable.
- Hit area at least a comfortable thumb target (`mobile-hud-layout`); non-interactive Graphics have Raycast Target off.
- Icon never as large as its button (`ui-style-rules`); icon + label group layout is in `ui-icon-label-layout`.
- Custom buttons derive the framework's button base (finds the Button in children, listener in `Awake`, override the click method).

## Safe expansion

Build a button inside a parent-owned padded content area. Its label uses TMP Auto Size and its icon+label group is centred within the button content inset. Preferred-size expansion is permitted only while the full button rect stays inside that parent content area and does not intersect another content or interactive sibling. A Board/Frame is a decorative layer, not permission to cover its border or a neighbour. If the label cannot fit at its minimum font within those limits, fail the build for a design/content choice instead of clipping, overflowing or overlapping.
