---
name: mobile-input-controls
description: "Touch input for Unity mobile: finger ownership, discrete tap edges, hold actions, UI-vs-world blocking, joystick and camera controls. Use when adding/fixing mobile input or debugging short taps."
triggers: mobile input, touch, tap edge, short tap, coalesced touch, wasPressedThisFrame, joystick, input he thong, cham ngan, nut bam, cham man hinh, ngon tay
---

# Mobile input controls

On a phone the player has two thumbs and no mouse. Everything depends on assigning each finger a single job for its whole lifetime and keeping UI from stealing touches.

## Design
- **Left thumb**: floating joystick. The finger that starts in the joystick zone owns movement until released.
- **Right thumb**: action buttons; any touch that starts on empty space in the right half drives the **camera drag**. Buttons capture their own finger.
- **Finger identity**: track `fingerId` (or the Input System touch id) per role; never infer the role from the current position. A finger that began on the joystick keeps being the joystick even if it slides over a button.
- **Dead zone** 0.1-0.15, radial clamp, optional response curve; normalise diagonal movement.
- **Floating vs fixed**: floating by default; offer fixed in settings if the reference has it.
- **Auto actions** reduce touch load only when the GDD enables them: use explicit target/eligibility rules and contextual actions that swap by state.
- **Jump**: buffer input (~0.1 s) and coyote time (~0.1 s) for forgiving platforming.

## Implementation notes (Unity)
- Prefer the installed input stack (new Input System with on-screen controls, or the project's existing joystick). Inspect first; do not add a second input package.
- Use `EventSystem`/Graphic Raycaster for UI; for world touches ask whether the touch started over UI (`IsPointerOverGameObject(fingerId)` or the Input System equivalent) once at touch start, not every frame.
- **Discrete action taps:** distinguish down/press edges from held state. A complete down+up can arrive within one input update, leaving `isPressed` false; consume the press edge or queued event as well as held state so the action is not lost. Keep continuous hold/repeat actions driven by their held contract.
- Preserve the touch/pointer identity that owns the gesture, and apply the UI-vs-world decision to that same identity and edge. A UI press must not leak into world input, and a world press must not be reassigned to another finger.
- Full-screen invisible UI images are the classic touch thief; disable Raycast Target on them or size them to the intended zone.
- Camera drag: scale by `Screen.dpi` or by screen height so sensitivity feels the same across phones; smooth lightly; expose sensitivity in settings.
- Keep input reading separate from character logic (an input bridge) so bots and tests can drive the same character (see `npc-bots-and-enemies`).
- Editor simulation: support mouse + keyboard in the Editor so agents can drive Play Mode tests via MCP; guard with `#if UNITY_EDITOR`.
- Haptics: short light impulse on pickup/hit/button; always behind a settings toggle; avoid per-frame vibration.
- Pause/resume: release all captured fingers when the app is paused or a popup opens.

## Verify
Test with two simultaneous touches (joystick + camera drag + button) on a device or the Device Simulator; confirm no stuck movement after a popup opens, after an interruption, and after scene reload. Layout checks belong to `mobile-hud-layout`.
- For each discrete world action, queue/produce down and up before one input update is sampled: the gameplay bridge must receive one command, and a following update with no new input must receive zero. Repeat with the same touch over UI and verify it is blocked; separately confirm intended hold/repeat behavior. Use a rebuilt target-device gesture to confirm the platform input path when available, and label synthetic input tests as such.

How knife-tower/monkey-escape wire joystick, look drag, edge-triggered jump and pinch: `references/touch-input-reference.md`. Camera values: `freelook-third-person-camera`.

## Second stick for body facing (carry/aim games)
- A small fixed right-hand stick sets the body FACING relative to the camera (up = camera forward, left = 90 deg left, down = back); target yaw = cameraYaw + atan2(x, y); turn toward it at a capped rate and keep the yaw when the stick is released. Keep a keyboard fallback (Q/E rate turn) and gamepad right stick. Movement stays camera-relative and independent of facing, so the player can walk sideways with a long carried object.
- A carried long object held in front of the body must sit close (reach ~ thickness + margin, e.g. 0.4 m); a far reach makes sideways passage through narrow gaps impossible. Verify with a scripted pilot that drives the REAL input statics (TOUCH_MOVE / turn stick / roll / lift), not teleports.
