---
name: economy-autobalance-simulator
description: "Tune an economy with a simulator: model income, prices and gates, target a playtime curve, iterate within a cap, write results to config. Use when prices, rates or progression pacing must be set or re-checked."
triggers: balance, simulator, pacing, playtime, economy, prices, income, curve, offline, rebirth, can bang
---

# Economy auto-balance simulator
1. Write targets first (time to first purchase, session length, total playtime) in `docs/economy/`.
2. EditMode or Python sim of the real formulas (read them from code/config, never retype constants).
3. Iterate with a bounded loop; change one lever at a time; keep a baseline table.
4. Re-sim after ANY economy change; keep pacing within the stated tolerance; see `simulator-pacing-checks`, `auto-balance-loop`, `consistency-check`.
5. Live games: saved data changes need migration plus a test.
