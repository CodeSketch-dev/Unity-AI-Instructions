---
id: S-05-interactables
type: interactable
title: Pickups and hazards
priority: P0
fidelity: faithful
evidence: [CAP-008@00:03]
recipe: platform-kit
kinds:
  - {id: coin, trigger: touch, effect: {currency: coins, amount: 1}}
  - {id: checkpoint, trigger: touch, effect: {set_respawn: true}}
  - {id: kill_brick, trigger: touch, effect: {kill: true}}
  - {id: moving_platform, trigger: stand, effect: {carry: true}}
  - {id: spinner, trigger: touch, effect: {knockback: true}}
placement_rule: "coins every 4-6 m along the path"
features:
  - id: F-05.1
    name: Coin, checkpoint, kill brick
    priority: P0
    acceptance:
      - "[edit] a coin trigger fires once per pickup"
      - "[play] touching a checkpoint changes the respawn point"
  - id: F-05.2
    name: Moving platform and spinner
    priority: P1
    acceptance:
      - "[play] a moving platform carries the character without sliding"
---
