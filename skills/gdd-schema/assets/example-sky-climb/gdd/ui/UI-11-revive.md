---
id: UI-11-revive
type: ui_screen
kind: popup_modal
fidelity: faithful
priority: P1
opened_by: [event:character_dead]
captures: [CAP-015@00:03]
reference_canvas: {w: 1080, h: 1920, match: 0.5}
states: [default]
elements:
  - {n: 1, name: Board, anchor: center, pos: [0, 0], size: [800, 600], container: true}
  - {n: 2, name: Btn_Revive, anchor: center, pos: [0, -60], size: [500, 130], text: {key: ui.revive}, behaviour: revive}
  - {n: 3, name: Btn_NoThanks, anchor: center, pos: [0, -240], size: [400, 100], text: {key: ui.no_thanks}, behaviour: decline}
---
