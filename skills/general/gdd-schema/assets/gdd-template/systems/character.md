---
id: S-NN-character
type: character
title: ?
priority: P0
fidelity: faithful
evidence: []
depends_on: []
recipe: kcc-character-controller
rig: humanoid-r15
speed_mps: ?
jump_height_m: ?
states: [idle, run, jump, fall, land, dead]
health: {max: ?, respawn: checkpoint}
death_causes: [fall_below_y]
features:
  - id: F-NN.1
    name: ?
    priority: P0
    acceptance:
      - "[play] ?"
---
## Notes
## Open questions
