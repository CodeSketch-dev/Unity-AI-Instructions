---
name: mobile-input-controls
description: Touch input for Unity mobile: floating joystick, camera drag, action buttons, multi-touch separation, UI-vs-world blocking. Use when adding/fixing movement or camera controls or porting PC/Roblox controls.
---

# Mobile input controls

On a phone the player has two thumbs and no mouse. Everything depends on assigning each finger a single job for its whole lifetime and keeping UI from stealing touches.

## Design
- **Left thumb**: floating joystick. The finger that starts in the joystick zone owns movement until released.
- **Right thumb**: action buttons; any touch that starts on empty space in the right half drives the **camera drag**. Buttons capture their own finger.
- **Finger identity**: track `fingerId` (or the Input System touch id) per role; never infer the role from the current position. A finger that began on the joystick keeps being the joystick even if it slides over a button.
- **Dead zone** 0.1-0.15, radial clamp, optional response curve; normalise diagonal movement.
- **Floating vs fixed**: floating by default; offer fixed in settings if the reference has it.
- **Auto actions** reduce touch load: auto-attack/collect when a valid target is in range, auto-run on treadmills, contextual action button that swaps by state.
- **Jump**: buffer input (~0.1 s) and coyote time (~0.1 s) for forgiving platforming.

## Implementation notes (Unity)
- Prefer the installed input stack (new Input System with on-screen controls, or the project's existing joystick). Inspect first; do not add a second input package.
- Use `EventSystem`/Graphic Raycaster for UI; for world touches ask whether the touch started over UI (`IsPointerOverGameObject(fingerId)` or the Input System equivalent) once at touch start, not every frame.
- Full-screen invisible UI images are the classic touch thief; disable Raycast Target on them or size them to the intended zone.
- Camera drag: scale by `Screen.dpi` or by screen height so sensitivity feels the same across phones; smooth lightly; expose sensitivity in settings.
- Keep input reading separate from character logic (an input bridge) so bots and tests can drive the same character (see `npc-bots-and-enemies`).
- Editor simulation: support mouse + keyboard in the Editor so agents can drive Play Mode tests via MCP; guard with `#if UNITY_EDITOR`.
- Haptics: short light impulse on pickup/hit/button; always behind a settings toggle; avoid per-frame vibration.
- Pause/resume: release all captured fingers when the app is paused or a popup opens.

## Verify
Test with two simultaneous touches (joystick + camera drag + button) on a device or the Device Simulator; confirm no stuck movement after a popup opens, after an interruption, and after scene reload. Layout checks belong to `mobile-hud-layout`.
