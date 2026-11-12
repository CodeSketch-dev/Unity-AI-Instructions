---
name: input-reader-asset
description: "Input Reader asset: one ScriptableObject wraps generated Input System actions and exposes C# events, with action-map switching for gameplay vs UI. Use when input is read in many scripts or must switch between gameplay, menu and tutorial."
triggers: input reader, input system, action map, joystick, touch input, switch input, input asset, dieu khien, nhap lieu, bat tat input
---

# Input Reader asset

Source: third-party example (open-project-1 InputReader, Apache-2.0) simplified + our practice. See `mobile-input-controls` for touch/joystick specifics.

## When
Several systems poll input directly, or a popup/tutorial must disable gameplay input cleanly.

## Steps
1. Generate the C# class from the `.inputactions` asset; one reader asset owns the generated class instance, created in `OnEnable`, disposed in `OnDisable`.
2. The reader implements the generated `I<Map>Actions` interfaces and re-raises `event UnityAction<Vector2> MoveEvent`, `JumpEvent` etc., initialised with `delegate { }`.
3. Provide `EnableGameplayInput()`, `EnableMenuInput()`, `DisableAll()`; only one map is enabled at a time; popups switch to menu mode and restore on close.
4. Consumers subscribe in `OnEnable` and unsubscribe in `OnDisable`; gameplay code never reads `Keyboard.current`.
5. UI-only mobile games keep the reader and feed it from on-screen controls.

## Pitfalls
- Two readers each create their own generated instance and double-enable maps; keep a single asset.
- A missing `Disable()` leaves the map active after Play (domain reload off).
- Switching maps mid-press leaves a stuck pressed state; raise the cancelled events on switch.
- Use a counted lock (`gameplay-polish-recipes`) when many popups can stack.

## Verify
Play Mode: open popup, assert gameplay events stop; close, assert resume; Console empty.
