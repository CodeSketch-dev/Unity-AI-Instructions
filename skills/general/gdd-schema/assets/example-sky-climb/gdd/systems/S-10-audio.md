---
id: S-10-audio
type: audio
title: Music and sfx
priority: P1
fidelity: free
evidence: []
bgm: [{id: bgm_main, scope: global, source: free-pack}]
sfx: [{id: sfx_coin, event: coin_collected}, {id: sfx_buy, event: purchase_ok}]
features:
  - id: F-10.1
    name: Audio events
    priority: P1
    acceptance:
      - "[inspect] every GDD event has an sfx"
---
