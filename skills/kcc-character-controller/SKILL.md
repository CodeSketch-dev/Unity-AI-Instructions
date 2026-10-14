---
name: kcc-character-controller
description: "Build the Roblox-feel character with the KinematicCharacterController: states, callback pipeline, SO tuning profiles, jump graceand input structs. Use when creating or tuning the player or bot movement controller."
---

# KCC character controller

Pattern from knife-tower and monkey-escape (report 04, VERIFIED unless marked). Look first at the project's existing controller (`reference-index`); reuse the KinematicCharacterController asset if it is installed. Numbers are in `references/feel-table.md` as soft defaults.

## Shape
- `Character : OptCollisionSensorFast<ICharacterCollidable>` is the actor root and the single physics-callback owner (`collision-registry`). Sibling components (renderer, animator, checkpoint, dead, fx, sfx, fall detector, skin) derive from the cached-mono hub base and read the root through `Hub`.
- `CharacterKC : ICharacterController` holds motion. Same character, different driver: `Player` and `AI` write an input struct and call `SetInputs(ref input)` (`bot-brain-waypoints`).
- Input structs: `{moveAxisForward, moveAxisRight, cameraRotation, jumpDown}` for the player, `{MoveVector, LookVector, Jump}` for AI. Camera-relative movement: project the camera rotation onto the up plane, clamp the input to length 1.
- States via the framework `StateMachine<State>` used as a holder with a `switch` in the KCC callbacks (`Default, Freeze, ClimbingLadder, Jumping, Jetpack, FlyCarpet, Treadmill, Stop`; advanced states in `kcc-advanced-movement`). `IsGrounded = CurrentState == Default`.

## Callback pipeline
`SetInputs` (clamp, camera plane, set `_jumpRequested`) -> `BeforeCharacterUpdate` (state switches) -> `UpdateRotation` -> `UpdateVelocity` (ground lerp / air accel + gravity + drag / jump / ladder) -> `AfterCharacterUpdate` (buffer expiry, reset `_jumpConsumed` on stable ground, coyote timer) -> `PostGroundingUpdate` (`OnLanded`, `OnLeaveStableGround`).

## Rules and why
- Jump: `canGroundJump = !consumed && (stable || timeSinceAbleToJump <= postGrace)`; apply `v += up*jumpUp*verticalMultiplier - project(v, up)` and `ForceUnground(0.1)`. Edge-triggered input: one jump per press.
- Keep base stats immutable and layered: `StableMoveSpeedMax + StableMoveSpeedAdd * SpeedLimitFactor`, `JumpVerticalMultiplier`, `FallGravityMultiplier`. Shop, booster, wing and level systems change the layers, never the base asset (the reference KT mutates its singleton from setters: anti-pattern).
- Tuning by SO profile: base `CharacterKC_Asset` + a per-minigame override asset; derive Obby from Escape by a scalar (x1.5 speed and jump) instead of copying.
- Ground speed uses an exponential lerp with sharpness 1000 (effectively instant); turning is instant (`1-exp(-100 dt)`; the `orientationSharpness` field of 10 is dead tuning, copy the 100).
- Landing: falls >= 25 m freeze 0.6 s with hero-landing animation; fall detector kills at 20 m below the last stable ground (`checkpoint-respawn`).
- Capsule r 0.3, h 1.7, yOffset 0.85; step 0.5, stable slope 60 (89 for slope obbies), ledge denivelation on, 5 movement iterations.
- Animator parameters through a hash dictionary with "IfExists" guards so skins missing a parameter do not warn (`character-rig-and-animation-contract`).

## Verify
Compare the asset values with the feel table; walk edges, thin platforms and slopes in Play Mode via Unity MCP; check coyote/buffer by eye (0.5 s is very forgiving, lower it if the reference feels stricter). Not compiled or run in this session.

More: `references/gotchas.md`, `freelook-third-person-camera`, `platform-kit`, `roblox-character-camera` (generic Roblox numbers), `mobile-input-controls`.
