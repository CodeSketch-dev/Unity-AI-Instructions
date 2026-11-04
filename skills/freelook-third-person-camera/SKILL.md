---
name: freelook-third-person-camera
description: "Use when building or tuning a Cinemachine third-person player camera: one brain in a camera prefab nested in the player, 3-orbit FreeLook (v2) or OrbitalFollow (v3) values, zero damping, touch-drag input, FOV on the lens, far-clip zones, shake, respawn warp."
triggers: kt style, knife tower, camera prefab, player camera, third person camera, cinemachine, freelook, orbital follow, cinemachine brain, camera shake, far clip zone, camera warp, camera drag, camera khong xoay, camera nhan vat, camera nguoi thu ba
---

# Third-person player camera (Cinemachine)

The studio's standard player camera is ONE prefab nested inside the player prefab, with ONE `CinemachineBrain` in the whole game. Values below were read from the reference prefab (verified in YAML, not observed in Play); treat them as defaults and compare with the target footage (`roblox-character-camera` has generic Roblox numbers).

## 0. Version first (ruling: follow the installed major version)
1. Read `Packages/manifest.json` for `com.unity.cinemachine`. Major 2 (namespace `Cinemachine`: `CinemachineFreeLook`, `CinemachineVirtualCamera`) and major 3 (`Unity.Cinemachine`: `CinemachineCamera` + `CinemachineOrbitalFollow`) have different APIs. Never mix them; one generation per project.
2. v2 is the reference form (below). The v3 mapping is in [cinemachine-version-notes](references/cinemachine-version-notes.md); it comes from public docs and was not run against an installed v3 package.
3. Unity 6 projects can still pin v2; do not upgrade the package as part of a camera task without the owner asking.

## 1. Prefab recipe ([tree and full value table](references/player-camera-prefab.md))
`Player_Camera` root (manager + third-person + shaker + follow-path scripts)
- `CameraMain`: Camera (tag MainCamera, FOV 40, near 0.75, far 500) + AudioListener + CinemachineBrain (UpdateMethod LateUpdate, BlendUpdateMethod LateUpdate, DefaultBlend EaseInOut 2 s)
- `FreeLook`: one `CinemachineFreeLook` + `CinemachineCollider`; Follow = LookAt = `FollowTransform`
- `FollowTransform`: empty, moved to the player in `LateUpdate`
- optional overlay camera (URP camera stack, own layer) for a preview/gacha box, inactive by default; never a second Brain
Nest the prefab in the player prefab and override only `_followTarget`. The scene has no camera of its own.

## 2. Key values (v2, reference)
| Parameter | Value |
|---|---|
| Rig | 3 orbits (height, radius): top (6, 1), middle (3, 6), bottom (-1, 3) |
| Binding | SimpleFollowWithWorldUp, spline curvature 0.2, heading definition velocity |
| Per rig | Transposer offset (0, 3, -6), ALL damping 0; Composer ScreenY 0.6 / 0.55 / 0.5, dead zone 0, soft zone 0.8 x 0.8, lookahead 0 |
| Axes | Y value 0.5 range 0..1, X -180..180 wrap, X max speed 700, accel/decel 0.1, NO input name, recentering off (drive from your input) |
| Collision | CinemachineCollider: mask world layers, PullCameraForward, radius 0.1, min distance 0.1, MaximumEffort 4, damping 0, ignore tag Player |
| Follow pivot | FollowTransform = target pos + (0, 1, 0), rotation = target rotation |
| Noise | Perlin on every rig, amplitude and frequency 0 at rest; shake sets the gain |
| Stand-in numbers | Shake default amp 0.4, freq 3.5, dur 0.2 (stronger wins); user zoom max 3x; carpet/vehicle bottom rig (-5, 3) vs normal (-5, 1) from a camera factory |

Zero damping with a snappy character gives the locked Roblox feel; smoothness comes from the character, not the camera.

## 3. Behavior to copy
- Drive the axes from your input: `m_XAxis.m_InputAxisValue` / `m_YAxis.m_InputAxisValue` (v2). Nothing smoothes the drag itself.
- **FOV, near and far go on the vcam LENS, never on `Camera`**: the brain overwrites `Camera.fieldOfView/farClipPlane` every frame. Write the overlay camera too if present.
- Respawn / teleport: post a camera-reset event (StaticBus), then `ForceCameraPosition(player.TransformPoint(0, 10, -20), rotation)` ONE frame later (`await UniTask.Yield()`); earlier is overwritten.
- Tutorial / special vcam: a second vcam of equal priority toggled with `SetActive`; the newest activated wins and the brain blends over `DefaultBlend`; wait the blend time, then disable it to blend back.
- Occlusion = `CinemachineCollider` only in the reference (no fade). Optional prop fade: `camera-occlusion-fade` (studio addition).
- Far clip: per-stage trigger zones (deepest zone wins) that write the lens far plane, applies to all tiers: `culling-group-distance`.
- Low end: post-processing off and depth texture mode none per camera (`device-tier-policy`).
- Intro flyover: disable the FreeLook GameObject, move the Camera, re-enable (`intro-camera-flyover`). Input wiring: `mobile-input-controls`.
- Code skeleton (v2, <= 40 lines): [CameraRig.cs.txt](references/CameraRig.cs.txt).

## 4. Not verified (carried from earlier mining, not re-read)
Y-axis speed 10 with invert, look sensitivity 6 with `touch delta / dpi * sensitivity`, pinch zoom speed 0.01 on the right-half touches, speed-FOV boost (+10 over 1 s, release 0.35 s). Check them in the player GUI/input code of the reference before relying on them.

## 5. Done check
- Exactly one Brain and one AudioListener in Play (`FindObjectsByType` count 1), no camera in the scene.
- Camera follows through a respawn and a teleport without a whip; FOV change visible (lens, not Camera).
- Shake returns to amplitude 0; collider pulls the camera forward at walls.
- Screenshot at the target aspect ratios; profile on a low-end device before claiming gains.

## Pitfalls
- Editing `Camera.fieldOfView`/`farClipPlane` (silently overwritten).
- A second Brain in a scene or minigame prefab (blends fight).
- `ForceCameraPosition` in the same frame as the reset event.
- Equal-priority vcams rely on tie-break (newest wins); set priorities explicitly if you add more.

## Added from third-party notes (2026-11-02)
Frame-rate independent smoothing (`1 - exp(-rate * dt)` or SmoothDamp, not a constant Lerp); follow after the target moved (LateUpdate matching the mover); clamp pitch about -80..+45; compose follow first, shake additive last; hard-cut on teleport; deadzone for twitchy games.
