---
name: iap-catalog
description: "Catalog-driven in-app purchases: product table, payout receiver switch, ownership data, restore, price text fallback. Use when adding products or shop packs to a clone."
---

# IAP catalog

Port details live in `unity-iap-port`; this skill is the design contract for a new game.

## Shape
- One catalog (JSON or asset) is the source of product id, type (consumable, non-consumable, subscription), price tier and payout. Prices shown to the player always come from the store with an "N/A" fallback and a refresh when products load.
- One receiver with a switch on payout subtype grants everything. Grant to Data first, then post the currency spread event (`currency-spread-fx`).
- Ownership data keyed by base product id: purchase counts, total purchases (payer flag), processed transaction ids (bounded).
- Dedupe by transaction id; never block a paid transaction because stock or state is odd.
- Restore is real: re-check entitlements for non-consumables and grant missing ones. A fake spinner is not restore.
- Local-only games have no server validation; treat purchases as unverifiable and keep payouts idempotent.

## From the GDD
Per product: id, type, tier, exact payout, one-time or repeat, where it is offered and the show-when rule (starter pack, remove ads, VIP). A tier ladder and pack values are the designer's numbers: never invent them.

## Checks
Every catalog id has a receiver case; every button product id exists in the catalog; every payout subtype is handled. Events `iap_view/click/success/fail/restore` come from the taxonomy.

## Added from Unity official guidance (2026-11-02)
Source: official (Unity-Technologies/skills/implement-in-app-purchases, Unity IAP 5), our wording. Check the installed IAP version first; v4 and v5 APIs differ.
- v5 flow: get the store controller, subscribe to ALL events before connecting, connect, fetch products on the connected event, show products on the fetched event. Initialize early (Awake) so IAP is ready before UI Start.
- Cached product list can be stale; refresh with a fetch when the shop opens.
- Two-step purchase: grant content, THEN confirm the pending order. An unconfirmed order is re-delivered on the next launch, so grant must be idempotent (dedupe by transaction id, see above).
- Restore: required on iOS (visible Restore button). Non-consumables and subscriptions re-deliver as pending orders; non-renewing Apple subscriptions cannot be restored through the store call.
- Receipt validation: Google supports local validation with obfuscated tangle data; Apple StoreKit 2 local validation does nothing, so use the JWS for server-side checks. Local-only games stay unverified: do not call them secure.
