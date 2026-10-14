---
name: recipe-restock-shop
description: "Rotating restock shop recipe: slot timer on UTC, weighted rarity roll per tier, stock limits, ad-forced restock, capacity slots. Use for boost or item shops that refresh."
---

# Recipe: restock shop

## Parts
- `Data_Shop`: purchased and equipped lists, next restock UTC (ISO string), restock count, per-slot stock, capacity level.
- `Factory_Shop`: display slot count, restock interval, weight tables per unlock tier, stock ranges per rarity, lifetime max stock per item.
- Timer: compare against UTC on open and on resume; never run a per-frame timer on the shop.

## Behavior
- Each slot rolls its rarity independently from the weight table of the highest unlocked tier; weights are normalized so they need not sum to 100.
- A special table can apply every Nth restock (VIP style) if the GDD says so; the first restock is a guaranteed gentle one.
- Purchase checks slot stock and lifetime max; a paid IAP never fails on stock.
- Buying never auto-equips; equip is explicit, replacing the weakest when full.
- Sold out offers a rewarded ad that forces a restock.

All numbers (interval, weights, stock) come from the GDD tables. Use `loot-rarity-tables` for the weighted pick helper and `config-and-factory-authoring` for assets.
