# Worked examples (report 15 sec 10.8)

Values tagged V come from the reference projects (thunder-break-egg TBE, knife-tower KT, climb-tower CT); I = initial proposals to tune with the balance tools. Soft defaults, not law.

## A. Pickaxe (Mine behavior, 15 tiers)
| Field | Value | Source |
|---|---|---|
| Behavior | nearest node in range, one target per swing | V TBE |
| Range / cone | 4.3 m + node radius / none (no facing check) | V |
| Swing | speed 1.5, impact at 0.88 of the clip | V |
| Damage by tier | 1, 4, 15, 60, 250, 1k, 4k, 15k, 60k, 250k, 1M, 4M, 15M, 60M, 250M | V |
| Price by tier | 0, 200, 1k, 5k, 25k, 120k, 620k, 3.1M, 16M, 78M, 390M, 2B, 9.8B, 49B, 240B | V |
| Node HP | `Damage(recommendedTier(zone)) * hits * U(0.9, 1.1)`, hits per rarity 4, 6, 9, 14, 20, 28, 40, 56, 80, 112 | V |
| Feedback | node scale punch (0.18, -0.22, 0.18) 0.22 s, rotation shake z 9 deg 0.25 s, floating red / gold text, light haptic on break | V |
| Terrain option | `IDigTerrain` adapter (`dig-terrain-adapter`), radius `base * PowerMultiplier * worldSize` | V CT |
Hotbar slot 1; held-model aura colour per tier; upgrade = buy the next tier.

## B. Sword (Melee, cone)
| Field | Value | Source |
|---|---|---|
| Behavior | melee cone, MaxTargets 8, ignore self/friendly | I |
| Range | 6 m long sword, 3 m knife, 3.2 m bat | V KT/TBE |
| Cone half angle | 90 deg (KT) or 70 deg (TBE bat) | V |
| Cooldown | 1.5 s (KT) / 0.55 s (TBE bat) | V |
| Impact delay | 0.25 s after the swing starts (KT) or 0.88 of the clip (TBE) | V |
| Damage (HP game) | proposal 30 base; KT `Power 30` is knockback force, not damage | V/I |
| Knockback | `forward * Power + up * 5` (KT); TBE force 10 + up impulse 5.5 | V |
| Hit reaction | ragdoll 2.5 s (KT) / lie 1.6 s + stand 0.55 s (TBE) | V |
| Effects | optional burn (1 s kill delay), freeze (4 s), poison (10 s) | V |
| Crit | 5% x2 (not in any reference) | I |
| Feedback | pooled hit fx at target + 0.75 up, medium haptic, shake 0.4 / 3.5 / 0.2, optional hit-stop 0.06 s | V/I |

## C. Bomb (Thrown, AoE, optional terrain)
| Field | Value | Source |
|---|---|---|
| Throw | direction (0, 0.3, 1), speed 10 + inherit * 0.5, velocity-change impulse | V CT |
| Fuse | 2 s ... 7 s by tier, blink the last 0.8 s | V |
| Blast radius | `3 * PowerMultiplier` (1..10) times world size | V |
| Cooldown | 2.5 s / throw speed (2.2..8.5 by tier) | V |
| Cost by tier | free, 1K, 7K, 34K, 388K, 1M, 100M, 2B, 39B | V |
| Reward multiplier | 2, 2.5, 3, 4.1, 5.7, 6.8, 7.7, 10, 14 | V |
| Combat damage | `Damage * falloff(d / r)`, linear 1 -> 0.3 | I |
| Safety | never hits the owner unless self-damage is on; one-explosion flag; return to pool after the fx | V |
| Pooling | `PoolPrefabGlobal` (not LeanPool or coroutines) | house rule |
