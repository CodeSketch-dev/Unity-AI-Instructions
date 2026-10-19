---
name: combat-hit-detection-rule
description: "Rule for finding hit targets cheaply: no per-frame weapon collider, NonAlloc overlap or static target list, squared range plus cone dot, projectile sensors through the registry. Use whenever code decides who an attack hits."
---

# Hit detection rule

Why: melee in the reference is non-physical and scheduled at an impact time; per-frame weapon colliders and per-tick allocations cost CPU and GC on low-end Android (report 15 sec 1, 8; knife-tower allocates `new HashSet/List` every 0.15 s: do not copy).

1. **Impact-time queries only**, never a weapon collider enabled every frame.
2. Gather candidates from a static target list (`Combat_Target.All`, no physics) or `Physics.OverlapSphereNonAlloc(pos, range, buffer[32], layerMask, QueryTriggerInteraction.Ignore)` with a reusable buffer sized for the realistic maximum.
3. Filter with squared planar distance (+ vertical tolerance, reference 2 m for non-players) and a front dot test: half angle 90 deg (KT) or 70 deg (TBE); no facing check for mining nearest-node.
4. Pick all in cone (cap `MaxTargets`) or nearest only; throw target = best front-dot, tie broken by nearest; remove friendly fire unless the design has it.
5. Range = weapon range x skin scale x multipliers (player extra, AI multiplier from config).
6. **Projectiles** use a real collider: the pooled projectile is the sensor, resolves the owner of the touched collider through the registry (`OptCollisionLookup.TryFindFirst<IDamageable>` in v2, `OptCollisionRegister<T>` in v1; `collision-registry`), ignores the owner's colliders, releases on hit or range (`pool-everything`).
7. Throttle attackable-indicator checks (reference interval 0.15 s); no `GetComponent` or LINQ in the query; no allocation in the check.
8. Checks run on the main thread at impact; cancel pending impacts on death/unequip.

Resolver surface: `Combat_Resolver.FindInCone(origin, fwd, range, halfAngle, buf)`, `FindNearest`. Verify with a profiler capture that an attack allocates 0 bytes (`profiling-evidence`; say if only Editor-measured). Used by combat features such as `thrown-bomb-aoe` when present.
