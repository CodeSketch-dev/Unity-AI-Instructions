---
name: ui-button-anatomy
description: "Required components and behavior of every button: press scale, click sfx on pointer down, grayscale disabled, per-state variants, notify dot, hit areas. Use when creating or auditing any button, tab or HUD icon. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# Button anatomy

From report 07 (counts over 223 KT / 184 ME button objects, VERIFIED).

- **Every button = Image + Button + press-feedback script + click-sfx script** (about 85% of buttons have both). Search the installed package first (`UIPressPrimeTween`, `AudioButtonSfx`) and reuse it; never write a second press script. **Anything pressable gets it**: Button, Toggle, tab, HUD icon, custom touch area, and world sprite/text buttons. Add `UIPressPrimeTween` in every builder and runtime `AddComponent<Button>` (guard with GetComponent); backdrops/dim areas excluded.
- Press feedback (verify: pointer down -> scale 0.9, up -> back to 1): scale to 0.9 in 0.1 s OutQuad, unscaled time, ignored when not interactable, reset on disable.
- Click sfx plays on pointer DOWN (not onClick), default from the audio mixer factory, skipped when not interactable. Needs a `Button` on self or children.
- **Disabled = grayscale material swap** on the button image and extra images, not a tint. Locked and unaffordable states are separate visuals (see `ui-scroll-board` state plates).
- **States as child objects** toggled by SetActive (`BtnClaim / Missed / Today / Claimed`), or sibling buttons per state; never one button with many conditional sprites.
- Role variants: popup opener (`PopupButtonOpen`), IAP button (store price text), non-Button touch areas for jump/attack/look (pointer click/drag components).
- **Notify dot**: child `Notify` ~40x41, anchored top-right (-10, -6.5), plain SetActive from a data event; no count, no tween; same on tabs. When to show it and how to wire it: `ui-notification-dots`.
- Attention loops only on the primary CTA (`game-feel-polish`); stop them on disable.
- Hit area at least a comfortable thumb target (`mobile-hud-layout`); non-interactive Graphics have Raycast Target off.
- Icon never as large as its button (`ui-style-rules`); icon + label group layout is in `ui-icon-label-layout`.
- Custom buttons derive the framework's button base (finds the Button in children, listener in `Awake`, override the click method).

## Safe expansion

Build a button inside a parent-owned padded content area. Its label uses TMP Auto Size and its icon+label group is centred within the button content inset. Preferred-size expansion is permitted only while the full button rect stays inside that parent content area and does not intersect another content or interactive sibling. A Board/Frame is a decorative layer, not permission to cover its border or a neighbour. If the label cannot fit at its minimum font within those limits, fail the build for a design/content choice instead of clipping, overflowing or overlapping.

- Text centring: Capline alignment plus the sprite face offset, never a per-label nudge (`ui-text-tmp` Optical centring).

## World buttons

- Screen taps swallowed by a full-screen look area: forward pointer DOWN, UP and click with `ExecuteEvents.ExecuteHierarchy` to the topmost registered world raycaster hit (`World_ButtonPassThrough` pattern); the press script on the button then animates like a screen button.
- A world button is a World Canvas Image/TMP with Button + press script (+ collider registered for the pass-through). Non-UI sprites/meshes: write one PrimeTween press script implementing `IPointerDownHandler/UpHandler/ExitHandler`, same 0.9 / 0.1 s OutQuad / unscaled spec.
- Do not put press on an object another script already scales (pop/pulse): put it on a child wrapper `_target`.
- Audit with `Qa_PressAnim` (asset in this folder): dry run lists Button/Toggle without press, apply adds it to prefabs and scenes (skip third-party sets and prefabs with missing scripts). Confirm in Play Mode by sending pointer down/up and reading localScale.
