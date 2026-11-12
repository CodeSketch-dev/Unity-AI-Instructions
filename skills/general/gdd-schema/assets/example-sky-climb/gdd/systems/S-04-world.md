---
id: S-04-world
type: world
title: Tower zones
priority: P0
fidelity: faithful
evidence: [CAP-006@00:05, CAP-007@00:10]
depends_on: [S-01-character, S-05-interactables]
recipe: zone-level-design
zones:
  - {id: Z1, name: Meadow, index: 0, floors: 12, checkpoints: 3, hazards: [kill_brick, moving_platform]}
  - {id: Z2, name: Cloud, index: 1, floors: 12, checkpoints: 3, hazards: [kill_brick, spinner]}
  - {id: Z3, name: Sun, index: 2, floors: 12, checkpoints: 3, hazards: [spinner, moving_platform]}
size_budget: {renderers_max: 350, materials: 1}
features:
  - id: F-04.1
    name: Zone 1 greybox with checkpoints
    priority: P0
    acceptance:
      - "[play] the path from spawn to floor 12 is reachable"
      - "[inspect] renderers within the size budget"
  - id: F-04.2
    name: Zones 2 and 3
    priority: P1
    acceptance:
      - "[play] floor 36 is reachable"
---
