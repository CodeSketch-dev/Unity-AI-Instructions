---
id: S-01-character
type: character
title: Player character
priority: P0
fidelity: faithful
evidence: [CAP-003@00:12]
depends_on: [S-03-input]
recipe: kcc-character-controller
rig: humanoid-r15
speed_mps: 4.5
jump_height_m: 2.0
states: [idle, run, jump, fall, land, dead]
health: {max: 1, respawn: checkpoint}
death_causes: [fall_below_y, kill_brick]
features:
  - id: F-01.1
    name: Walk, run and jump
    priority: P0
    acceptance:
      - "[play] character reaches the first platform in at most 3 jumps from spawn"
      - "[edit] jump apex between 1.8 and 2.2 m"
  - id: F-01.2
    name: Death and respawn at checkpoint
    priority: P0
    evidence: [CAP-005@00:20]
    acceptance:
      - "[play] falling below the kill plane respawns at the last checkpoint after 2 s"
---
