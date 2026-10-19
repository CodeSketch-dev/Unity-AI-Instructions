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
- Luck and rarity values, weights, pity thresholds, mutation odds, and size distributions are per-game data. Generate them with `auto-balance-game` when the GDD does not provide evidence; displayed odds must equal real odds.
- Money-band rarity (KT): odds shift with the player's wealth through bands `{moneyFrom, moneyTo} -> Rate[]`.
- Boost shop (ME): per-rank restock weights (base vs VIP), stock ranges per rank, max stock 10, fuse 3 -> 1 higher.
- Chest (CT): rewards with `UnlockChance` and an open timer; ads or currency price.
- Kill rewards: none in KT; TBE rewards the egg's pet plus deposit money; CT currency per dig/bomb.

Persist pity counters before showing a result; choose the result before the animation (`gacha-box`, `jackpot-slot` patterns). Probabilities are tuned by `economy-auto-balance`.
