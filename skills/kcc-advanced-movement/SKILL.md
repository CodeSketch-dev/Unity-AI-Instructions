---
name: kcc-advanced-movement
description: "Use when a game needs rope swing, wall jump, sink zones, force zones, fly carpet or jetpack movement states."
---

# Advanced KCC movement

Each mechanic is one extra `State` plus a `partial class` file or sibling component on top of `kcc-character-controller`; all feel/tuning values belong in the SO profile and come from the current GDD or auto-balance output.

| Mechanic | Config contract |
|---|---|
| Rope swing | rope constraint, input acceleration, gravity, damping, tangential speed, steering, release impulse, hold/buffer/retract/extend timing, acquire scoring; API `BeginSwing` / `ReleaseSwing` |
| Wall jump | jump mode, up force, cooldown, wall grace, probe, air control, control ramp, feedback timing |
| Sink zone | `EnterSinkZone`: sink speed and jump modifier; trigger posts through the registry |
| Force zone | push magnitude and direction (`platform-kit`) |
| Fly carpet | speed, acceleration, yaw, rig scale, camera presentation, rig offset |
| Jetpack | power, fuel duration, refuel timing, jump magnitude |

## Rules
- A new state needs: enter/exit conditions in `BeforeCharacterUpdate`, a branch in `UpdateVelocity`, animator parameters with guards, a tutorial hook if it is taught (`TutorialActionPressed/SwingPressed`), and a separate input button when relevant (Jump vs Swing).
- Add the mechanic only if the GDD or reference needs it; every extra state multiplies test cases.
- Platform side registers through the collision registry; the controller exposes only a small API (`AddVelocity`, `ForceUnground`, `EnterSinkZone`, swing API).

Verify each state in Play Mode: enter, exit, die inside it and respawn clean, switch states mid-air, bots ignore or handle it. Not Editor-verified here.
