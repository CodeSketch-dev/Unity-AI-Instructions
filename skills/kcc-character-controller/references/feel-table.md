# Feel table (DATA)

Source: reference-project data. **Reference-only examples**: never apply these values to a new game unless the GDD/evidence selects this movement model. Prefer the current GDD or `auto-balance-game`; keep every stat as data.

## Locomotion
| Parameter | KT / ME Escape | ME Obby | Note |
|---|---|---|---|
| Max ground speed | 4.5 m/s | 6.75 (x1.5) | matches Roblox WalkSpeed 16 studs at 0.28 m/stud |
| Ground / air accel (sharpness) | 1000 / 1000 | same | effectively instant |
| Air drag | 0.1 (`v *= 1/(1+drag*dt)`) | same | |
| Gravity | -30 m/s^2 | same | Roblox ~55: floatier here, offset by a tall jump |
| Jump speed | 11 m/s | 16.5 | height v^2/2g = 2.02 m (4.54 m), air time 0.73 s (1.1 s) |
| Jump buffer / coyote | 0.5 s / 0.5 s | same | unusually long (usual 0.1); tighten if the reference feels strict |
| Max jumps | 1 (2 for double-jump) | same | NPC air jump x1.5 |
| Ladder climb speed | 5 m/s | 7.5 | enter/exit lerp 100 |
| Hero landing | fall >= 25 m -> freeze 0.6 s | same | |
| Capsule | r 0.3, h 1.7, yOffset 0.85 | same | |
| Slope / step | stable slope 60, step 0.5 | slope 89 | ME climbs near-vertical obby slopes (INFERRED) |
| Fall kill | 20 m below last stable ground (NPC 5) | same | |
| Respawn delay | 2.0 s | same | |
| Jump booster / wing | x1.7 / x2 (additive on the multiplier) | | `JumpVerticalMultiplier` layer |
| Jetpack | power 30, 3 s, refuel 1 s | | |
| Fly carpet | speed 8, accel 8, yaw 120 deg/s, FOV 60 | | |

Recipe: choose speed, jump height, and gravity from the current GDD; derive jump speed with `v = sqrt(2 * gravityMagnitude * jumpHeight)`.

## Progression-driven speed (ME)
Real speed = base 4.5 + `max(0, level - world.LevelRequired) * 0.5`; jump bonus +0.1 m/s per level; display speed to real `(display + 14.5) / 5`; `SpeedLimitFactor` (0..1) scales only the added speed; earn tick 0.15 s with moving speed > 0.5 m/s; air steering by angle 0 deg 100%, 90 deg 50%, 180 deg 0%; high-speed FOV +10 from `speed01 >= 0.95`, ramp 1 s, release 0.35 s, speed lines at 0.7.

## Roblox defaults (generic)
WalkSpeed 16 studs/s, gravity 196.2 studs/s^2, JumpHeight 7.2 studs, JumpPower 50 (see `roblox-character-camera`). Roblox gravity (~55 m/s^2) differs from the reference clones (30); do not mix: pick one set per game and derive the jump speed from the chosen height.

## Level design links
Safe jump gaps <= 80% of `speed * air_time`, stair rise <= 1 stud, slopes <= stable slope (`roblox-world-kit`).
