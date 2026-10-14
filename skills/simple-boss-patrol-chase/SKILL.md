---
name: simple-boss-patrol-chase
description: "Cheap boss/hazard enemy without pathfinding: rectangle patrol, detector trigger, chase, contact kill via the collision registry. Use for obby bosses, patrolling hazards and simple chasers."
---

# Simple boss: patrol and chase

From monkey-escape `Boss_SimpleTransformMove` and `Boss_TargetDetector` (report 04 sec 6, VERIFIED).

- No pathfinding: a transform mover with an inner `IStateMachine` (`Patrol`, `Chase`) (`state-machine-template`).
- Patrol: random points inside a rectangle within the parent bounds (`_patrolRangeX` 1, `_patrolRangeZ` 0.5, padding 10%), speed 2, rotation smoothness 6, arrival distance 0.1.
- Chase: speed 4 toward the target when the detector trigger (a volume registered through the collision registry) sees a character; return to patrol when it leaves.
- Kill on contact through `OptCollisionRegister` -> `Character.Kill(Killer_Type.Boss)`; the boss skips the revive hook (type Boss).
- Tuning in a config asset; one detector per boss, no per-frame `Physics` queries; disable the component when far (`culling-group-distance` events) and stop tweens on destroy.
- KT full AI bosses (`AI_Type.Boss` with patrol/chasing states) are for richer fights: use `bot-brain-waypoints` then.

Verify: boss patrols inside bounds, chases only inside the detector, kills once, respawn resets it.
