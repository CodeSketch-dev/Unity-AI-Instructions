---
name: recipe-add-skin-or-item
description: Add a character skin or item entry (asset, factory registration, unlock type, events, shop, save check). Use when adding purchasable or unlockable cosmetics or items.
not: localization, language, translate, ngon ngu
---

# Recipe: add a skin or item

Use the target framework profile and active GDD to identify its asset, registry, persistence, shop and event contracts. Reference evidence may validate an explicitly selected cosmetic capability but must not supply type names, paths, unlock currency, event names, or fallback behavior.

1. **Reference prefab**: use the GDD-selected render/rig contract. Share mesh/material resources only when skeleton/render compatibility is verified by the target importer.
2. **Asset**: create the target-defined config entry with a stable unique persisted ID, GDD-selected unlock channel, and only the required presentation references.
3. **Register** in the target registry and build/cache lookup through its normal initialization hook. Reject duplicate IDs (`config-registry-audit`); extend type/category definitions only when the target architecture and GDD require it.
4. **Persistence**: use the target persistent-data API for owned/equipped state; do not introduce a parallel save path (`data-block-template`).
5. **Presentation**: surface entries only through GDD-enabled UI/catalog flows.
6. **Events**: post target-defined unlock/equip state changes; the target switcher applies the compatible visual state. Entitlement expiry/fallback follows the GDD and platform policy.
7. **Verify**: no missing refs, listed in the shop, unlock -> equip -> mesh swaps, equipped skin survives restart, default fallback works. Do this in the Editor via Unity MCP before reporting done.

Items use the same integration chain, with concrete data shape determined by the target framework profile and active GDD.
