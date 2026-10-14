---
name: intro-camera-flyover
description: "Level intro cutscene: bezier camera path over waypoints with the FreeLook disabled, UI hidden, then gameplay start events. Use for obby/tower intro flybys and cinematic camera moves."
---

# Intro camera flyover

From knife-tower `CameraFollowPath` and `Tower_Master` (report 04 sec 2.3, 8.4, VERIFIED).

- `CameraFollowPath.Follow(path)`: a cubic-bezier `DOPath` through scene waypoints (7.5 radius in the tower), about 1 s per waypoint, start delay 1 s; the FreeLook is disabled during the move and restored after (`freelook-third-person-camera`). Use the project's tween library (both DOTween and PrimeTween exist in the reference).
- Master sequence: wait until the loader is idle -> hide gameplay UI (event) -> run the flyover -> post the start event (`Event_AI_ConstructAllowed`) so bots and timers begin only after the cutscene -> show the HUD.
- Skippable: tap to skip finishes the tween instantly and runs the same end steps (no half state).
- Cancellation: cancel the sequence on destroy or scene change (`async-cancellation`); letterbox bars via the HUD canvas (`canvas-reference`).
- Cheap: one camera, no extra render passes; tune path waypoints in the scene, durations in a config.

Verify: intro plays once per run, skip works at any frame, input is blocked during it and restored, camera ends at the gameplay pose.
