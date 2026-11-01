---
name: bot-path-follow-smoothing
description: "Fix jittery bots on waypoint paths at speed: corner-pass test, speed hint, last-leg easing, turn-rate limit, fresh direction between throttled ticks, jitter harness. Use when bots wobble, orbit waypoints or snap their facing."
triggers: bots wobble, waypoints, jitter, orbit waypoint, bot giat
---

# Bot path-follow smoothing

Extends `bot-brain-waypoints`. Symptom: bots spin or wobble at high speed. Causes: a fixed arrive radius smaller than one frame of travel (overshoot, then turn back), steering from a stale direction between throttled AI ticks, instant yaw.

1. **Corner reached = passed the segment**, not inside a radius: advance when `dot(target - pos, segmentDir) <= 0` (or distance < `max(radius, speed*dt*2)`).
2. **Speed hint**: the path tells the driver the next-leg length and turn angle; slow before sharp turns, full speed on straights.
3. **Last leg**: ease speed toward the final waypoint; stop inside a tolerance, never chase an exact point.
4. **Turn-rate limit**: yaw toward the move direction with a max deg/s and a dead-zone for tiny angles; never set facing from raw velocity noise.
5. **Between throttled AI ticks**, recompute only the direction to the current target every frame (cheap vector) rather than reusing the last tick's vector; the tick just changes the target.
6. **Measure**: log per-frame yaw delta per bot to CSV before and after (frames over e.g. 25 deg, p95 and max); accept only when the numbers drop. Keep the harness outside `Assets/`.
7. Restore bot/test state afterwards (`playmode-driver-recipes`).
