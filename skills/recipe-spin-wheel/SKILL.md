---
name: recipe-spin-wheel
description: "Spin wheel recipe: wheel asset with weighted slots, daily free spin, ad spins with a cap, result chosen before animation. For the lucky wheel."
---

# Recipe: spin wheel

- `Wheel_Asset { slots[{reward, amount, weight, color, displayChance}] }`, `Factory_Wheel`, `Data_Wheel { lastFreeSpinDay, adSpinsToday, pity }`.
- Flow: free daily spin, extra spins by rewarded ad up to a daily cap, pick the slot by weight (with pity), then ease the wheel to the exact angle over several turns, grant on stop with currency spread.
- Displayed chance equals the weight used by the roll.
- UI: wheel, pointer, slot labels, spin button (free), ad button (cooldown/limit state), result popup, red dot while a free spin is available.
- Events: `wheel_open`, `wheel_spin{source}`, `wheel_reward`.
- GDD supplies slots, weights, spin counts and pity; do not invent them.
