---
name: roblox-character-camera
description: Roblox-feel movement, jump, ragdoll, animation states and third-person camera in Unity, with stud/WalkSpeed/JumpPower conversions. Use when building or tuning player character/camera or fixing controller issues.
---

# Roblox-style character and camera

Roblox games share a movement feel: blocky avatar, predictable constant-speed running, floaty-but-snappy jump, and a draggable third-person camera. Use these defaults, then correct them against the reference video.

## Unit conversions (approximate; verify against the reference scale)
- 1 stud ~ 0.28 m. Default avatar ~ 5 studs tall (~1.4-1.8 m depending on rig).
- Default WalkSpeed 16 studs/s ~ 4.5 m/s. Games often boost speed through stats; keep the number as a stat and convert at one place.
- Default gravity 196.2 studs/s^2 ~ 55 m/s^2 (about 5.6x Earth). Default JumpPower 50 / JumpHeight 7.2 studs ~ 2 m.
- Treat the above as starting points; if the reference clearly differs, trust the observed scale (compare avatar to doors/stairs in video frames).

## Character
- Use the project's existing character controller (kinematic/Character Controller based) before writing a new one. Stats (speed, jump, etc.) come from data, not magic numbers.
- Movement: instant acceleration (or very short), no drifting; speed from a single stat; run animation intensity can scale with speed.
- Ground check with a short ray/spherecast, coyote time, jump buffer (see `mobile-input-controls`).
- States: idle, run, jump/fall, carry (arms raised), action, ragdoll. Use the project's state machine for modes; force-run animation while on a treadmill or similar.
- Ragdoll/knockback: keep the visible skin continuous (detach the skin pose before disabling the Animator, sync transforms, then enable physics) to avoid a one-frame snap; recover by blending back to animation.
- Collision: capsule only; keep physics layers minimal; route triggers through the project's collision registry (see `mobile-perf-audit`).
- Nameplates/labels: world text batched, billboarded, scaled by distance.

## Camera
- Third-person follow with a pivot at the head/chest, distance ~ 8-12 m default, FOV ~ 70, pitch clamp (-10 to 80 degrees).
- Touch-drag orbit on the right side (see `mobile-input-controls`); smooth with critically-damped follow; no smoothing on the drag itself.
- Collision: spherecast from pivot to camera, pull in on hit; avoid jitter by smoothing the correction slightly.
- Update in `LateUpdate` after the character moved; fixed-update physics characters need interpolation.
- Effects: shake on impacts (small, decays), FOV kick when sprinting, optional zoom limits.
- Fog and skybox colors should match; see `zone-level-design`.

## Verify
Compare a video frame of the reference and a screenshot of ours at the same situation (camera distance, avatar size relative to props). Walk across stairs, edges, thin platforms and slopes; jump onto a ledge; rapidly rotate the camera; check there is no sliding when idle.
