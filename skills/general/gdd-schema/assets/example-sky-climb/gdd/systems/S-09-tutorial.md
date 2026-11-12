---
id: S-09-tutorial
type: tutorial
title: First-time tutorial
priority: P1
fidelity: faithful
evidence: [CAP-002@00:08]
steps:
  - {id: T1, trigger: first_spawn, text: "Drag to move", advance: moved_3m, forced: true}
  - {id: T2, trigger: coins_ge_50, text: "Open the shop", advance: shop_opened, forced: false}
features:
  - id: F-09.1
    name: Three step tutorial
    priority: P1
    acceptance:
      - "[play] the tutorial completes and does not show again after restart"
---
