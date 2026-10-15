---
name: auto-balance-game
description: "Use when a Roblox clone needs all time-sensitive gameplay stats generated from a full-game playtime target, daily session budget, optional milestone timeline, or additional balance constraints."
---

# Auto-balance game

Generic, topology-neutral balance entrypoint. It does not require biomes/zones and does not ask the human to author price, income, boost, damage, HP, cooldown, drop, or upgrade tables.

Run:

```text
/auto-balance-game --full-days 10 --hours-per-day 1 --milestone quest.main_01=2m --milestone map.center=15m --constraint player_sessions_per_day=1 --constraint currency.coins.sinks=upgrades,shop --set combat.enemy_hp_factor=1.2 --gdd ./gdd --out ./gdd/_generated/balance-plan.json
```

Every repeatable parameter may be supplied multiple times. `--milestone PATH=DURATION` accepts any gameplay topology: quest, map, boss, dungeon, round, objective, or custom path. Milestones are optional; without them the target is open-world/global completion. If explicit time exceeds the full-game target, stop and report the conflict.

The output contains numeric `generated_values` per milestone for progression gates, currency income, unlock/upgrade costs, action rewards, player power, enemy HP/damage, action cadence, drop weights, and collection targets, plus domain contracts for retention/offline/rebirth. It also emits `discovered_stats` from GDD files using tunable-key detection; unknown game-specific stats must be added to the balance binding, not discarded. Validate with `py -I <skills>/auto-balance-game/scripts/validate_balance_plan.py PLAN.json`. Generated values must be materialized by the Unity config/factory layer and verified on a fresh-save golden path at normal time. Observed GDD facts override generated values; explicit `--set` overrides generated values.

Materialization contract: import the plan as generated data, map each `generated_values[].path` to the game's config/factory IDs, preserve GDD-observed values, apply explicit overrides last, and fail on an unmapped discovered stat that affects completion time. Never silently invent a feature from an unknown stat.

Do not use this skill for a reference-only audit where the task is to reproduce observed numbers without tuning.
