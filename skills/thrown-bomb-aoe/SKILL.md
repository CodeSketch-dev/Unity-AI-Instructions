---
name: thrown-bomb-aoe
description: "Thrown items and bombs: pooled arc or linear projectiles, fuse with blink, NonAlloc blast with falloff, owner safety, optional terrain dig. Use when adding grenades, bombs, shuriken, shields, hammers or banana throws."
---

# Thrown items and bombs

From knife-tower `Item_Throw_Linear/_Parabola`, `Item_Gun_Projectile` and climb-tower `BombController/ThrownBomb` (report 15 sec 2.3, 3.2, VERIFIED). Behavior class for `tool-weapon-pipeline` (`Tool_Behavior_Thrown`).

| Kind | Numbers |
|---|---|
| Linear throw (shield, hammer, shuriken) | speed 12, max distance 12 (weapon range overrides), collision radius 0.15, spin 360 deg/s, pooled, `FixedUpdate` step, optional overlap mode + unstoppable |
| Parabola throw (banana) | throw speed 15, jump power 1, target Y offset 0.5, prediction forward bias 0.25, lifetime 4 s, warning 1 s with 4 blinks then explode fx |
| Gun projectile | speed 50, lifetime 4 s, release by range, collision callback, owner collider ignored, aims at a target only when the owner is the player |
| Bomb (CT) | direction (0, 0.3, 1), speed 10 + inherit velocity x 0.5 (max inherit 20), velocity-change impulse, fuse 2-7 s by tier, blink the last 0.8 s, blast radius `3 x PowerMultiplier x worldSize` |

## Rules
- Pool every projectile and bomb (`pool-everything`, `PoolPrefabGlobal`); the reference CT used LeanPool, coroutines and `WaitForSeconds`: replace with the framework pool and UniTask with cancellation (`async-cancellation`).
- Fuse timer by tween/UniTask delay, cancelled on release; a one-explosion flag prevents double blast; return to the pool after the fx.
- Blast: `Physics.OverlapSphereNonAlloc` into a reusable buffer, explicit layers, `QueryTriggerInteraction`, damage with falloff `Damage * falloff(d / r)` (linear 1 -> 0.3 proposed, INFERRED); owner is excluded unless the design has self-damage (`combat-hit-detection-rule`).
- Target pick for throws: best front-dot, nearest breaks ties; the held item hides on throw and returns after the cooldown.
- Terrain: optional `IDigTerrain.Dig(pos, radius)` adapter (`dig-terrain-adapter`); the bomb needs a detector scan to find diggable colliders before exploding (reference uses RaycastPro `RangeDetector`).
- Feedback via `game-feel-polish` (`references/combat-feel.md`): shake on blast, floating numbers, haptic.

Verify in Play Mode: arc lands where aimed, fuse blink, blast radius matches the tier, owner safe, no allocation per frame, pool reuse after 50 throws.
