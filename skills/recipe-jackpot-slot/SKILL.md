---
name: recipe-jackpot-slot
description: "Slot or jackpot spin recipe: outcome roll, pity counter, free daily spin plus banked spins, IAP spin fallback, paytable UI. For slot machines and jackpot spins."
---

# Recipe: jackpot slot

## Parts
- `Jackpot_Item_Asset` entries (reward, ranking, rate, display rate) listed in `Factory_Jackpot` with roll timings and outcome rates.
- `Data_Jackpot`: last free spin day, free spins used, banked spins, pity counter.
- `Jackpot_Spin.Roll`: choose the result first, then animate to it. Pity forces a good outcome after N misses.
- UI: spin button states (free, banked, buy), paytable, result popup, red dot when a free spin exists.

## Rules
- The result is decided before the animation and the animation lands deterministically.
- The paytable shows the same rate the roll uses (displayed equals rolled). The numbers themselves are the designer's decision.
- Spin sources: one free per day (plus VIP bonus if the GDD has VIP), banked spins from rewards, then an IAP product (`iap-catalog`).
- Level-gated tables are config, not code branches.

## Wiring
Grant through the shared currency/shop path, spread FX on rewards, events `wheel_spin`-style from the taxonomy. For a wheel variant use `recipe-spin-wheel` shape (slots instead of reels).
