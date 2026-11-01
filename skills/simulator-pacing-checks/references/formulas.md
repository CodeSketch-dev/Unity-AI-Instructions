# Formulas

Source: third-party example (standard math), rewritten. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/other-engines/roblox-simulator-economy/references.

| Quantity | Formula |
|---|---|
| Price of next level (owned = n) | floor(baseCost * g^n) |
| Total cost level a to b | baseCost * g^a * (g^(b-a) - 1) / (g - 1); real play pays the floored per-level sum, slightly less |
| Rebirth requirement k | baseReq * reqGrowth^k |
| Additive multiplier | 1 + k * perRebirth |
| Multiplicative multiplier | q^k |
| Rebirth wait ratio (k+1 over k) | about reqGrowth / (multiplier(k+1) / multiplier(k)) once income scales with the multiplier |
| Offline income | floor(min(away, capSeconds) * rate * efficiency); away <= 0 pays 0 |

Worked check: baseCost 10 with g 1.12 puts level 50 near 2.9k; with g 1.5 it would be near 6.4e9. Use that comparison whenever a price column looks explosive.

Pacing table columns to print: level, price, income, wait, cumulative time. For rebirth: k, requirement, multiplier, wait, ratio vs previous. Flag any ratio above 2 and any single wait above the session budget.
