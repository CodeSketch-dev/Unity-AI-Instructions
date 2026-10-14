---
name: economy-loop-archetypes
description: "Economy loop archetypes for Roblox clones: earn-spend-upgrade, collect-sell, hatch-merge, rebirth, with sinks, sources and pacing checks. Use when turning GDD economy into systems."
---

# Economy loop archetypes

Pick the loop(s) the GDD describes, then wire sources and sinks through `economy-progression-design` and config assets. Numbers always come from the GDD tables.

| Loop | Core cycle | Required parts |
|---|---|---|
| Earn-spend-upgrade | action earns currency, upgrade raises earn rate | wallet, upgrade asset, cost curve in config |
| Collect-sell | carry capacity, sell at a point | capacity stat, sell zone, bonus multipliers |
| Hatch-merge | currency to egg to pet, merge duplicates | egg asset, weight table, merge rule |
| Rebirth | reset progress for a permanent multiplier | reset list, kept list, multiplier data |
| Idle income | pets or machines produce while away | income manager, offline rule (`recipe-retention-timers`) |

## Pacing checks (automation, not formulas)
- Every currency has at least one source and one sink reachable in the first session.
- Time to first purchase and first unlock is measured in a real run at timeScale 1 (`rule-qa-validity`).
- A sink is never gated behind a source the player cannot reach yet.

The orchestrator's economy task records the measured times as evidence; tuning loops belong to the economy-balancer agent.
