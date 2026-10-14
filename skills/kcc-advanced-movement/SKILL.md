---
name: kcc-advanced-movement
description: "Advanced KCC movement states: rope swing, wall jump, sink zones, force zones, fly carpet and jetpack, each as an extra state with its constants. Use when the game needs swinging, wall jumping, quicksand or flying."
---

# Advanced KCC movement

Each mechanic is one extra `State` plus a `partial class` file or sibling component on top of `kcc-character-controller`; constants come from monkey-escape/knife-tower (report 04 sec 3.2, 7, VERIFIED) and belong in the SO profile.

| Mechanic | Constants (reference defaults) |
|---|---|
| Rope swing | rope limit 8 m, input accel 30, gravity x1, damping 0.5 (idle 0.5), max tangential speed 60, steering sharpness 3, flip assist 1.5 above speed 10, release jump up 8 + forward boost 2, min hold 0.3 s, input buffer 0.12 s, retract 0.75 s / extend 1.25 s, acquire scoring forward weight 130 and distance penalty 0.015. API: `BeginSwing` / `ReleaseSwing`; the platform hooks it (`Platform_Swing`) |
| Wall jump | modes OneJump / Infinite, min up force 25 (override 20), cooldown 0.5 s, wall contact grace 0.12 s, forward probe 0.75 m, horizontal control while rising x0.18, control ramp 1.5 s, blinking highlight 0.35 s |
| Sink zone | `EnterSinkZone`: sink speed 0.5, jump multiplier 0.5 (quicksand, mud); trigger posts through the registry |
| Force zone | constant push ~10 m/s along a direction (`platform-kit`) |
| Fly carpet | speed 8, accel 8, yaw 120 deg/s, rig x1.25, camera FOV 60, bottom rig (-5, 3) |
| Jetpack | power 30, 3 s, refuel 1 s, jump magnitude 0.3 (unused in ME) |

## Rules
- A new state needs: enter/exit conditions in `BeforeCharacterUpdate`, a branch in `UpdateVelocity`, animator parameters with guards, a tutorial hook if it is taught (`TutorialActionPressed/SwingPressed`), and a separate input button when relevant (Jump vs Swing).
- Add the mechanic only if the GDD or reference needs it; every extra state multiplies test cases.
- Platform side registers through the collision registry; the controller exposes only a small API (`AddVelocity`, `ForceUnground`, `EnterSinkZone`, swing API).

Verify each state in Play Mode: enter, exit, die inside it and respawn clean, switch states mid-air, bots ignore or handle it. Not Editor-verified here.
