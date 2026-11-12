---
name: thrown-bomb-aoe
description: "Thrown items and bombs: pooled arc or linear projectiles, fuse with blink, NonAlloc blast with falloff, owner safety, optional terrain dig. Use when adding grenades, bombs, shuriken, shields, hammers or banana throws."
---

# Thrown items and bombs

Generic projectile/area-effect behavior contract. Use only when the current GDD explicitly contains a thrown explosive or equivalent area attack.

| Kind | Numbers |
|---|---|
| Linear throw (shield, hammer, shuriken) | speed 12, max distance 12 (weapon range overrides), collision radius 0.15, spin 360 deg/s, pooled, `FixedUpdate` step, optional overlap mode + unstoppable |
| Parabola throw (banana) | observed trajectory, target offset, lifetime, warning, and impact feedback are config-driven; populate from the current GDD/reference |
| Gun projectile | observed speed/lifetime/release rules are config-driven; collision callback ignores the owner and aims according to the current actor contract |
| Bomb (CT) | direction (0, 0.3, 1), speed 10 + inherit velocity x 0.5 (max inherit 20), velocity-change impulse, fuse 2-7 s by tier, blink the last 0.8 s, blast radius `3 x PowerMultiplier x worldSize` |

## Rules
- Pool every projectile and bomb (`pool-everything`, `PoolPrefabGlobal`); the reference CT used LeanPool, coroutines and `WaitForSeconds`: replace with the framework pool and UniTask with cancellation (`async-cancellation`).
- Fuse timer by tween/UniTask delay, cancelled on release; a one-explosion flag prevents double blast; return to the pool after the fx.
- Blast: `Physics.OverlapSphereNonAlloc` into a reusable buffer, explicit layers, `QueryTriggerInteraction`, and config-driven damage falloff; owner is excluded unless the design has self-damage (`combat-hit-detection-rule`).
- Target pick for throws: best front-dot, nearest breaks ties; the held item hides on throw and returns after the cooldown.
- Terrain deformation is optional and must be explicitly evidenced by the GDD; otherwise resolve damage against ordinary colliders only.
- Feedback via `game-feel-polish` (`references/combat-feel.md`): shake on blast, floating numbers, haptic.

Verify in Play Mode: arc lands where aimed, fuse blink, blast radius matches the tier, owner safe, no allocation per frame, pool reuse after 50 throws.
