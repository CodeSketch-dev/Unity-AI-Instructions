---
name: combat-health-status
description: "HP, damage, shield, status effects and boss HP phases: IDamageable, DamageInfo, health events, status priority rules, respawn timing. Use when characters, eggs or bosses need health or timed effects."
---

# Health, damage and status

The references have NO generic player HP: knife-tower hits cause ragdoll knockback or one-shot kills, numeric HP exists only on eggs (TBE) and the boss event (percent) (report 15 sec 1, VERIFIED). Everything about player HP numbers is a proposal (INFERRED): tune with the balance loop.

## Model
- `IDamageable { ApplyDamage(in DamageInfo) }`; `DamageInfo` struct: Amount, Source, Tool, Knockback, Point, IsCrit, StatusId, Kind.
- `Combat_Health : MonoCachedHub<Actor>`: `DataValue<double> Hp`, max, regen, shield; events through `StaticBus<Event_Combat_Hit/Dead>` for cross-feature consumers and C# events for the owner (`Combat_Health.EventChanged`, like `Character.EventDead`). Use double for big-number games (`rule-bignumber-safety`). Egg-style "broken when hp < 1".
- Shield: temporary (`SetShield(duration)`, revive protection) or permanent; one-shot and burn respect it; a shield can absorb one hit and be consumed.
- Death and respawn: use the reference's observed timing when available; otherwise expose revive, ragdoll, lie, stand, and shield timing as tunable config (`checkpoint-respawn`).

## Status effects (KT `Character_Effect`)
One active effect at a time (`DataValue<Effect_Type>`), with priority rules taken from the GDD/reference. Expose duration, tick interval, tick damage, stack rule, priority, and blocks as tunable config. Each effect owns a `CancelToken`; clear on death/revive; update UI from events or a throttled presentation path. Generalise with `Status_Asset {type, duration, tick interval, tick damage, stack rule Refresh/Ignore/Replace, priority, blocks[]}`.
CT has a clean `Stat` module (`IStatModifier` with SourceId, flat/percent, over-time) that makes removal exact; consider the same idea for buffs.

## Boss phases
`Boss_Phase_Config { HpThresholds, per-phase overrides }`; post `Event_Combat_PhaseChanged(boss, phase, hp01)` ONLY on change from one manager loop. Boss hitbox delays, spawn cadence/count/lifetime, shake and phase effects are observed/configured values owned by the GDD and balance pass. HP bar draws threshold lines. Simple patrol bosses: `simple-boss-patrol-chase`.

## Rules
Events subscribe/unsubscribe symmetrically (the reference wraps subscribe in try/catch: do not); tokens cancelled on teardown; no per-tick allocation; damage numbers and feedback through `game-feel-polish` (`references/combat-feel.md`); killing posts exactly one `Event_Combat_Dead`. Verify in Play Mode: damage, shield absorb, each status, death, revive, phase change fires once.
