---
name: freelook-third-person-camera
description: Cinemachine FreeLook player camera with the reference orbit values, zero damping, touch-drag input, speed FOV, far-clip zones, occluder fade, shake and teleport warp. Use when building or tuning the third-person camera of a clone.
---

# FreeLook third-person camera

From `Player_Camera.prefab` in knife-tower and monkey-escape (report 04 sec 2.3, VERIFIED). Defaults, not law: compare with the reference footage, then adjust (`roblox-character-camera` has the generic Roblox numbers, FOV 70 and 8-12 m; the references run FOV 40-50 at ~6.7 m).

| Parameter | Value |
|---|---|
| Rig | CinemachineFreeLook, 3 orbits, ALL damping 0 (X/Y/Z, composer, lookahead, dead zone), soft zone 0.8 |
| Orbits (height, radius) | top (6, 1), mid (3, 6), bottom (-1, 3); bottom overridden at runtime to (-5, 1) via a camera factory; carpet (-5, 3) |
| Mid rig | 6.7 m behind (sqrt(3^2+6^2)), 3 m up; follow pivot (0, 1, 0) above the character |
| FOV / near / far | 40 (KT) or 50 (ME factory `_defaultFOV`); near 0.5-0.75; far 500, per-zone override |
| Binding | SimpleFollowWithWorldUp (KT) / WorldSpace (ME: camera does not yaw with the character) |
| Drag | X axis max speed 700 (wrap, no invert), Y axis 10 (0..1, invert), accel/decel 0.1 |
| Look sensitivity | 6 (prefab) with `touch delta / Screen.dpi * sensitivity` |
| Collision | CinemachineCollider radius 0.1, min distance 0.1, damping 0 |
| Pinch zoom | `_maxUserZoom` 3, speed 0.01, only right-half touches |
| Shake | amplitude 0.4, frequency 3.5, duration 0.2, decay 2/s |

Zero damping with an instant (sharpness 1000) character gives the locked, snappy Roblox feel.

## Behavior to copy
- A follow transform one unit above the pivot updated in `LateUpdate`; input via `m_XAxis.m_InputAxisValue` from the drag delta, nothing smoothing the drag itself.
- Speed FOV: boost = max speed FOV - default FOV (+10), starts at `speed01 >= 0.95`, rises over 1 s, releases in 0.35 s.
- Far-clip zones through the collision registry (deepest zone wins): `culling-group-distance`.
- Occluder fade: NonAlloc ray camera -> player (buffer 32), alpha 0.25, fade 0.15 s on tagged renderers.
- Camera lifecycle events: reset after revive/teleport (`Event_Camera_Reset`, place at `character.TransformPoint((0, 10, -20))` next frame); teleport warp calls the rig's `OnTargetObjectWarped` / force position after one frame.
- Low-end: disable post-processing and depth texture per camera (`device-tier-policy`).

Input wiring: `mobile-input-controls`. Intro flyover: `intro-camera-flyover`. Not verified in the Editor.
