---
id: S-07-skin-shop
type: shop
title: Skin shop
priority: P0
fidelity: exact
evidence: [CAP-010@00:05, CAP-011@00:05, CAP-012@00:05, CAP-013@00:05]
depends_on: [S-06-economy]
pattern: skin-shop
catalog_table: economy/prices.csv
item_states: [locked, owned, selected, equipped]
preview: 2d_image
ui: UI-10-skin-shop
persists: Data_Skins
features:
  - id: F-07.1
    name: Buy, equip and persist
    priority: P0
    acceptance:
      - "[edit] insufficient funds leaves state unchanged"
      - "[play] a bought skin stays equipped after restart"
      - "[shot] the shop matches the reference at 3 aspect ratios"
---
