---
name: currency-spread-fx
description: Make rewards (money, gems, speed) fly from source to the HUD currency bar with count-up, using the reference currency-spread kit. Use for any reward grant/claim, IAP pack, ad reward, or "no fly effect".
---

# Currency spread FX

Recipe, not fixed code. Resolve the real class names first: `reference-index` query `currency spread`, or grep the current project. Names below (`Currency_Bar`, `Currency_Bar_Spread`, `Currency_Spread_Config`, `Event_Currency_Spread_Start`) are those of the reference kit; use the project's equivalents. If the project has none, port the kit with `asset-transfer-closure`.

## Pieces (reuse, never rewrite)
- `Currency_Bar` (number pill, eases to the real value, punch on growth) with `_Type`; `Currency_Bar_Spread` on the same object (target icon, spread prefab); `Currency_Spread` prefab + `Currency_Spread_Config` asset (item prefab, timings); event `Event_Currency_Spread_Start(type, amount, startPosition, useBackground, renderCount, mode, startIsWorldPos)` on the StaticBus.
- The bar subscribed to the bus must **filter by currency type** (`e.Type == bar.Type`), otherwise every bar flies every currency.

## Grant pattern
1. Add the value to the wallet FIRST (`Data_Currency.X.Value += amount`; speed via its grant method).
2. Post the spread event with the button/icon position as start (`startIsWorldPos=false` for UI, true for world points). The bar subtracts the amount for display and counts up when the items land.
3. Preset mode needs `renderCount <= spawnPoints.Length` (clamp inside `Construct`, otherwise index out of range).
4. While a popup is open the flying items parent on the popup root so they are not hidden behind it.

## Setup checklist for a new currency
- Config asset (copy the money one) with the currency's item prefab; spread prefab pointing at that config; wallet field + `Currency_Type` entry.
- HUD number is a real `Currency_Bar` (not hand-written text in the HUD script); popup headers that show a wallet (store trophy) get their own Currency_Bar + Currency_Bar_Spread.
- Repair broken imports first: missing config GUID on the spread prefab, item prefabs whose sprite was lost (white squares).
- Test: post the event from a script in Play Mode and screenshot while items fly; test each currency.

## Spots that must use it
Claim buttons (index, daily, free cash), IAP packs (fly from the buy button), rewarded ad rewards, sell/collect, speed grants.
