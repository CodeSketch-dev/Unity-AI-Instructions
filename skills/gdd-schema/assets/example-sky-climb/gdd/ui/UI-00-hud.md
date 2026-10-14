---
id: UI-00-hud
type: ui_screen
kind: hud
fidelity: exact
priority: P0
captures: [CAP-004@00:02]
reference_canvas: {w: 1080, h: 1920, match: 0.5}
states: [default]
elements:
  - {n: 1, name: Joystick_Zone, anchor: bottom-left, pos: [200, 440], size: [360, 360], zone: bottom-left}
  - {n: 2, name: Btn_Jump, anchor: bottom-right, pos: [-170, 440], size: [200, 200], zone: bottom-right, behaviour: jump}
  - {n: 3, name: Coins, anchor: top-right, pos: [-190, -110], size: [320, 90], zone: top-right, text: {key: hud.coins}}
  - {n: 4, name: Floor, anchor: top-center, pos: [0, -110], size: [300, 90], zone: top-center, text: {key: hud.floor}}
  - {n: 5, name: Btn_Shop, anchor: mid-right, pos: [-100, 100], size: [160, 160], zone: right-mid, behaviour: open_shop}
---
