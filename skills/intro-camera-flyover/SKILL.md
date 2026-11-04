---
name: intro-camera-flyover
description: "Level intro cutscene: bezier camera path over waypoints with the FreeLook disabled, UI hidden, then gameplay start events. Use for obby/tower intro flybys and cinematic camera moves."
---

# Intro camera flyover

Reference facts (verified in the studio reference game): a `CameraFollowPath.Follow(points, onStart, onComplete)` driven by a level master. It deactivates the FreeLook GameObject, puts the camera on points[0], runs a cubic-bezier path tween (about 1 s per point, start delay 1 s, look-at 0.01), then reactivates the FreeLook. The camera prefab layout: `freelook-third-person-camera`.

- Path: a cubic-bezier path tween through scene waypoints placed in the level (radius and spacing are per level), about 1 s per waypoint, start delay 1 s; the FreeLook is disabled during the move and restored after. Use the project's tween library (prefer PrimeTween for new code; the reference ships both).
- Master sequence: wait until the loader is idle -> hide gameplay UI (event) -> run the flyover -> post the start event (`Event_AI_ConstructAllowed`) so bots and timers begin only after the cutscene -> show the HUD.
- Skippable (studio improvement; the reference flyover is not skippable): tap to skip finishes the tween instantly and runs the same end steps (no half state).
- Cancellation: cancel the sequence on destroy or scene change (`async-cancellation`); letterbox bars: two black bars (about 125 px) in the HUD canvas toggled by an overlay component (`persistent-root-prefab`, `unity-ui`).
- Cheap: one camera, no extra render passes; tune path waypoints in the scene, durations in a config.

Verify: intro plays once per run, skip works at any frame, input is blocked during it and restored, camera ends at the gameplay pose.
