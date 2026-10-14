# Touch input as built in knife-tower / monkey-escape (report 04 sec 2.4, VERIFIED)

- Move: Joystick Pack `Joystick` component; axes read from the player GUI (`PlayerGUI.JoystickMove`), keyboard fallback `Horizontal/Vertical` for desktop testing; a keyboard-latch flag avoids stuck input when switching modes.
- Look: right-side drag area (`UIPointerDrag`): `delta / Screen.dpi * lookSensitivity` (prefab 6; code default 20); desktop arrow axes. Pinch zoom only for touches on the right half (zoom speed 0.01, scroll 2, max 3).
- Actions: `UIPointerClick` down/up; jump is EDGE-triggered (`_inputActionConsumed`): one jump per press; tapping while on the carpet means "carpet off + jump".
- Camera-relative move: camera rotation projected on the up plane, applied to the input clamped to length 1.
- Mode-specific: separate Jump and Swing buttons in monkey-escape (`GoSwingAction`, tutorial events `TutorialActionPressed/SwingPressed`); the poison effect inverts input in knife-tower; `CurrentMoveInput` is exposed for UI feedback.
- Reset input state on focus loss, death and popup open; the joystick touch region is anchored per `unity-ui` (max left half).
