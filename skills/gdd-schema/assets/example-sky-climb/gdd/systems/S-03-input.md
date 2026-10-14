---
id: S-03-input
type: input
title: Touch input
priority: P0
fidelity: faithful
evidence: [CAP-002@00:08]
recipe: mobile-input-controls
scheme: {move: virtual_joystick_left, look: drag_right_half, buttons: [jump, interact]}
joystick: {region: "left 0.35w x 0.6h", type: floating}
features:
  - id: F-03.1
    name: Joystick, look drag, jump button
    priority: P0
    acceptance:
      - "[play] joystick moves the character and jump is one jump per press"
      - "[shot] HUD controls do not overlap at 3 aspect ratios"
---
