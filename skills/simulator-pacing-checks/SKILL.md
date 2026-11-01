---
name: simulator-pacing-checks
description: "Pacing and economy checks for simulator, idle and pet games: cost curves, buy-max, rebirth ratio, offline cap, big-number rollover, odds disclosure, save repair. Use when tuning or reviewing prices, rebirth, offline income or progress stalls."
triggers: pacing, cost curve, cost growth, rebirth, prestige, offline earnings, offline income, big number, number format, buy max, progress stalls, too grindy, income per second, odds disclosure, can bang kinh te, tien do cham, hoi sinh, thu nhap offline
---

# Simulator pacing checks

Source: third-party example (ideas only; its Luau code is not used). Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/other-engines/roblox-simulator-economy. Complements `economy-progression-design`, `economy-loop-archetypes`, `loot-rarity-tables`, `auto-balance-loop`.

Choose numbers with a pacing table before writing code; keep every amount owned by one authority (game logic, never UI input).

## Check list (run on every economy change)
1. **One config table** for base income, each upgrade (baseCost, growth, max level), rebirth (requirement, growth, multiplier per rebirth), offline (cap hours, efficiency).
2. **Wait table:** per level, `wait = price / income`; per rebirth, the active time to reach the requirement. Print it, do not eyeball.
3. **Targets (starting points):**
   - first 10 levels take seconds each;
   - each rebirth takes only a little longer than the previous (ratio about 1.2-1.5, never a cliff);
   - growth 1.07-1.15 for upgrades bought many times, 1.5-3 only for rare one-shots;
   - offline earns less than online (efficiency 0.25-0.5, cap 8-12 h) unless a design decision says otherwise (an ad-doubled claim is a valid hook).
4. **Ratio test:** if `requirementGrowth` far exceeds the multiplier growth, rebirth N takes weeks; with a multiplicative multiplier keep `requirementGrowth / multiplierBase` near the wanted ratio.
5. **Buy-max** walks real floored prices and is capped by max level; never a log formula alone, never an uncapped loop.
6. **Spend atomically:** check every currency of a multi-currency cost before subtracting any; reject negative or non-finite costs.
7. **Offline time** comes from a trusted clock, is capped, and a time that went backwards pays 0.
8. **Save repair on load:** NaN/infinity/negative become 0, levels clamp to max, unknown ids dropped, repairs logged. Above about 1e15 doubles lose integers: use a mantissa/exponent or log representation.
9. **Number display:** format after rounding and bump the suffix when rounding reaches 1000 (999950 shows 1.0M, never 1000.0K). Display only; never parse text back.
10. **Random paid items** (eggs, crates, spins): show every outcome and real odds before purchase from the same list the roll uses (boosts included, live), sum to 100%, reachable from a labeled Info control. See `loot-rarity-tables`.

## Pitfalls (symptom -> cause)
- Rebirth takes weeks -> requirement curve outruns the multiplier.
- Prices outrun income after ~20 levels -> growth too high for repeat upgrades (1.5^50 is about 6e8).
- Late game breaks after a few rebirths -> multiplier compounding without a matching requirement.
- Two purchases pass one balance check -> yield between check and spend.
- Offline pays days -> client clock, no cap, corrupt timestamp.

Formulas and a worked table: `references/formulas.md`. Simulate with the project's own sim (`auto-balance-loop`) and keep the pacing target within the documented tolerance.
