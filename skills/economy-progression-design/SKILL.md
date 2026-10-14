---
name: economy-progression-design
description: "Design/tune economy and progression: cost curves, income, payback, drop tables, rebirth, zone gating, FTUE pacing, with a simulation script. Use for prices, \"too grindy/fast\", balance or drop rates."
---

# Economy and progression design

Numbers define how the game feels more than any feature. Derive them from observed reference data first, then tune with a simulation instead of by gut. A bundled script (`scripts/simulate_economy.py`) prints cost / income / wait-time tables for an upgrade chain so you can see where pacing breaks.

## Method
1. **Collect observed numbers** from `docs/gameplay-analysis.md` (prices, incomes, timers). Fit the curve: cost(n) ~ base * growth^n is typical; growth 1.07-1.15 for stackable upgrades, 1.5-3 per tier for tiered purchases.
2. **Set pacing targets** (adjust to the reference): first reward < 30 s; first upgrade 30-90 s; each next upgrade wait grows slowly and stays under ~5 min until a "wall" that motivates prestige, ads or purchases; first zone change 5-15 min; first rebirth 30-90 min.
3. **Simulate**: run the script with candidate parameters; look for waits that spike, income that outruns costs (trivialized), or dead ends.
   `python -I scripts/simulate_economy.py --base-cost 10 --cost-growth 1.15 --base-income 1 --income-step 0.3 --levels 40 --target-wait 120`
4. **Rarity tables**: store as weights in config assets; verify they sum to 100 (or normalize), expose luck multipliers, and check expected cost to obtain each tier. Rarer = higher income and more spectacular presentation. Consider pity counters for top tiers.
5. **Multipliers**: keep a single formula for total income = base * (1 + sum of additive bonuses) * product of multiplicative bonuses; additive within a group, multiplicative across groups. Document it in a config comment so designers can reason about it.
6. **Gating**: zones gated by a stat with a *recommended* value banner; make the next gate reachable by the pace target.
7. **Monetization coupling**: rewarded ad = 2x for N minutes or instant payout equal to ~2-5 min of income; permanent passes give 2x multipliers; never make the free path impossible, make it slower. See `monetization-integration`.
8. **Big numbers**: store as `double` (or a BigNumber type if beyond 1e300); format with K/M/B/T/Qa/Qi; round for display only; do not accumulate floating error in the saved value more than needed.
9. **Offline earnings**: cap (e.g. 2-8 h) and apply a reduced rate.
10. **Record** the final tables and formulas in `docs/economy.md` and in config assets; keep the simulation parameters beside them.

## Balance the whole loop, not a table
Every number is coupled: zone access speed, boss chase/recovery and exposure time, tool damage and price, egg HP by biome/rarity/luck, hit cadence, treadmill/speed price, pet income, cage slots and multiplier, rewards, ads and IAP. Tuning one table alone produced a cage that would take ~165 years to afford. Therefore:
1. Keep **one deterministic formula source** (code + config) for the whole chain and a simulator/audit that reads it; every change re-runs the audit.
2. Define **target horizons** with the human (e.g. full completion in a stated number of days; first session, day 1, week 1 goals) and check each against the simulation. The game must not end too quickly: onboarding, session, day-scale and long-term collection goals all need content.
3. Learn **relationships and rhythm** from the reference (monotonic zone speeds, readable rarity jumps, late pets creating discrete income jumps), not its absolute numbers.
4. Measure real values in Play Mode (hit cadence from the actual animation clip, travel distances from real geometry, measured income uplift from size/mutation) before accepting a model; a provisional guess falsely showed near-zero boss exposure.
5. Fast-forward is only a QA accelerator: `normal duration = QA duration / timeScale`. Judge balance on normalized time and on a **fresh save**; a polluted save is valid only for runtime smoke checks.
6. Monetization guardrails are part of balance: rewarded ads are recovery/temporary acceleration, interstitials only at natural breaks with cooldown, IAP is utility/cosmetic value; none replaces the progression loop or forms a forced paywall.
7. Verify with assertions (monotonic speeds, price growth, multiplier bounds) in an editor audit and keep results in `docs/balance/`.

## Tuning checklist
- Any wait over target? Reduce cost growth or raise income step.
- Does buying the cheapest next upgrade always beat saving? If never, upgrades are pointless.
- Is there a variety of "best next buy" across the game? If one upgrade dominates, rebalance.
- Test with a fresh save and with a mid-game save.
