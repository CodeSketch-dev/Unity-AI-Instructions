---
id: UI-12-settings
type: ui_screen
kind: popup_modal
fidelity: faithful
priority: P2
opened_by: [event:settings_requested]
captures: []
reference_canvas: {w: 1080, h: 1920, match: 0.5}
states: [default]
elements:
  - {n: 1, name: Board, anchor: center, pos: [0, 0], size: [800, 650], container: true}
  - {n: 2, name: Row_Music, anchor: center, pos: [0, 100], size: [635, 80], text: {key: ui.music}}
  - {n: 3, name: Row_Sound, anchor: center, pos: [0, -8], size: [635, 80], text: {key: ui.sound}}
---
