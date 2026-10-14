---
id: S-08-monetization
type: monetization
title: Ads and purchases
priority: P1
fidelity: faithful
evidence: [CAP-014@00:10]
recipe: monetization-integration
ads:
  rewarded:
    - {id: ad_revive, placement: revive_popup, reward: revive, ui: UI-11-revive}
    - {id: ad_double, placement: floor_bonus, reward: "x2 coins", ui: UI-00-hud}
  interstitial: {every_n_deaths: 4, min_interval_s: 120}
iap:
  - {id: gems_100, price_usd: 0.99, grants: {gems: 100}}
consent: {gdpr_flow: true}
features:
  - id: F-08.1
    name: Rewarded revive and mock SDK
    priority: P1
    acceptance:
      - "[play] a mock rewarded ad grants a revive and a failed ad never blocks play"
---
