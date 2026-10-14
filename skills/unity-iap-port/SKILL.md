---
name: unity-iap-port
description: Port the reference project's IAP stack (manager, catalog json, buy button, receiver, restore) and verify with the Editor FakeStore. Use when IAP code is disabled, a sheet lists IAP products, or buy buttons do nothing.
---

# Unity IAP port

The reference project is whichever one `docs/clone-plan.md` lists as the IAP source (find it with `reference-index` query `IAPManager`). Class names below are those of the team's reference stack; confirm they exist before relying on them.

## Rule #1
Take the reference scripts as they are. Only translate framework names (namespace, text component, base-class lifecycle) and write the game-specific parts. Do not invent a mock purchase path: the Unity IAP **FakeStore** already shows a Buy/Cancel dialog in the Editor.

## Steps
1. Diff the project's IAP files against the reference (they usually differ only by namespace/`TMP`/`override`). Remove `#if false`, fix the diffs: base classes that no longer have virtual `OnEnable/OnDisable/Start` -> plain methods without `base.*`; missing helpers -> small shims (`GameUtils.FormatPriceTrailingSymbol`, `GameConstants` messages, trimmed `LogHelper` with only the IAP funnel); variant config the SDK build lacks -> `IAPVariantConfig.Empty`.
2. New `IAPProductCatalog.json` in `Resources` with the game's ids (`com.<studio>.<game>.<item>`), types (consumable/non-consumable), prices, payouts (`t`, `st` subtype, `q`, `d` data). Keep the old catalog out of the build.
3. `IAPConstants` payout subtypes + `IAP_Product_Receiver` that reads payouts from the CATALOG by base id (`ReceiveById`) and grants through the project's real Data APIs (Remove ads = banner + inter skip, not rewarded).
4. `IAPManager` + `IAPListener` as a child object of the persistent singleton prefab; the listener must reference the manager (`_listener`).
5. Buy button = `Button` + `CodelessIAPButton` + `IAP_Purchase_Button` (+ price text child). **`CodelessIAPButton.button` must be assigned** (it only hooks the Button it is given; default null = click does nothing). Product id must be set before the button's Awake (spawn cards under an inactive holder, bind, then reparent).
6. Entitlements: non-consumables become "Sold out" and persist via `Data_IAP`; consumables repeat. Subscription code stays untouched.
7. Verify in Play Mode: open the store, click a buy button, the **Fake Store dialog** appears (Buy/Cancel), Buy grants exactly once, second click on a non-consumable is blocked, restore button works, payment funnel events logged.

## Pitfalls
- Editor-only shortcuts that grant without the store hide wiring bugs: don't.
- Store products must be created by the user with the same ids; prices in the json are placeholders.
- Currency packs should use the Currency Spread (`currency-spread-fx`) from the buy button position.
