---
id: S-06-economy
type: economy
title: Currencies and prices
priority: P0
fidelity: faithful
evidence: [CAP-009@00:15]
recipe: economy-progression-design
currencies:
  - {id: coins, display: Coins, icon: A-021, start: 0, sources: [coin, floor_bonus, ad_reward], sinks: [skin_shop]}
  - {id: gems, display: Gems, icon: A-022, start: 0, sources: [iap, daily], sinks: [premium_skins, revive]}
tables: [economy/prices.csv]
balance_targets: {first_purchase_s: 90}
income_per_s: 1.2
features:
  - id: F-06.1
    name: Wallet and events
    priority: P0
    acceptance:
      - "[edit] wallet add and spend raise one event each"
      - "[sim] first purchase happens within 90 s of play"
---
