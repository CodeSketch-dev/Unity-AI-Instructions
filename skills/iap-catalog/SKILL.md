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
