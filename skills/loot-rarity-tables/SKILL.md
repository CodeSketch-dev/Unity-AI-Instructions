---
name: loot-rarity-tables
description: "Loot and rarity tables: weighted roll, rarity asset, luck and mutation tables, pity, money-band rarity, and the rule that displayed odds equal real odds. Use when adding gacha boxes, egg luck, chest rewards or drop tables."
---

# Loot and rarity tables

Facts from knife-tower (`Gacha_Box_Asset.RollItem`, `Rarity_Randomizer`), thunder-break-egg (luck/mutation tables), monkey-escape (boost shop restock), climb-tower (chests) (report 15 sec 4, VERIFIED). Odds are the designer's decision (user decision 2026-10-15); the pipeline tunes numbers automatically and enforces one rule: what is displayed equals what is rolled.

## Rule
What is displayed must equal what is rolled: roll by sum of weights, `random * total`, cumulative scan; expose `GetPercent(item)` to the UI and keep an EditMode test asserting displayed == computed; pity counters persist before the result is shown.

## Data
- `Rarity_Asset`/table: colour, shiny fx, frame, stat multiplier; enums seen: Normal/Rare/Legend (3), Common..Mythic (6), Common..Celestial (10). Power comes from the item tier, not from the rarity enum.
- Loot table: entries {asset, weight, min rarity}, rolls, pity after N, guaranteed rarity. Gacha box: price + weighted rewards.
- Luck (TBE): luck values 1, 2, 3, 5, 10, 25, 50, 100, 500, 1k, 5k, 10k, 100k, 1M with weights 45, 25, 14, 7, 4, 2.5, 1.3, 0.7, 0.3, 0.12, 0.05, 0.02, 0.005, 0.001; higher-rarity eggs lean the weights (`1 + rarity * 0.08`); luck buys at most 4 visual rarity steps but only 2 count for income; mutations at luck 0: Normal 88 / Gold 9 / Diamond 2.5 / Rainbow 0.5 (%), luck 1 triples specials; size roll bell curve in [0.8, 1.4].
- Money-band rarity (KT): odds shift with the player's wealth through bands `{moneyFrom, moneyTo} -> Rate[]`.
- Boost shop (ME): per-rank restock weights (base vs VIP), stock ranges per rank, max stock 10, fuse 3 -> 1 higher.
- Chest (CT): rewards with `UnlockChance` and an open timer; ads or currency price.
- Kill rewards: none in KT; TBE rewards the egg's pet plus deposit money; CT currency per dig/bomb.

Persist pity counters before showing a result; choose the result before the animation (`gacha-box`, `jackpot-slot` patterns). Probabilities are tuned by `economy-auto-balance`.
