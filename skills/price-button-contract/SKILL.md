---
name: price-button-contract
description: Contract for every in-game currency price button, card or unlock row (icon + price as one centred group, red when unaffordable, attention pulse, sold/owned state, top-up flow, no store component for soft currency). Use when building or fixing any shop, price button, card or unlock row.
triggers: price button, shop card, unlock button, buy button, currency price, gem button, nut mua, gia, cua hang, nut gia
---

# Price button contract (any game)

Every control that spends a currency satisfies ALL of these:
1. Look: icon + amount in ONE centred layout group (see `ui-icon-label-layout`, `ui-center-alignment` neighbour rule); abbreviated numbers (K/M/B/T) via the project's number formatter; no "$" on in-game currency (real-store prices keep their store text).
2. Affordability: amount turns red when the balance is below the price, normal otherwise; the data source exposes the numeric price so the UI can colour it (do not rely on a "can afford" flag that is deliberately true to open a top-up).
3. Motion: gentle attention pulse on buttons that should be pressed (gem/premium or real-money buttons slightly stronger), plus the standard press scale and click sfx (`ui-button-anatomy`); the pulse stops when the button is not interactable.
4. States: owned/sold = greyed, not interactable, label "Owned"; non-consumables never re-buyable.
5. Flow: not enough currency -> route to the top-up/currency shop, never a dead tap; all spends go through ONE project spend function (never subtract the balance in the button).
6. Components: soft-currency buttons must not carry the store/IAP purchase component; real-money buttons use the project's IAP component only.
7. Data: the item list, prices and rewards equal the design sheet row by row; remove template leftovers from the reference game (placeholder text, hidden prices, items the sheet does not list).
Verify in Play per screen: one script dump of counts/texts/colours/interactable/scale (twice, 0.3 s apart), a screenshot you look at, buy the cheapest item (balance drops by exactly the price), try an unaffordable one.
