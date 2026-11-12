---
id: UI-10-skin-shop
type: ui_screen
kind: popup_fullscreen
fidelity: exact
priority: P0
pattern: skin-shop
opened_by: [Btn_Shop@UI-00-hud]
captures: [CAP-010@00:05, CAP-011@00:05, CAP-012@00:05, CAP-013@00:05]
reference_canvas: {w: 1080, h: 1920, match: 0.5}
states: [default, item_owned, item_selected, item_equipped]
elements:
  - {n: 1, name: Btn_Back, anchor: top-left, pos: [92, -87], size: [179, 161], behaviour: close}
  - {n: 2, name: Item_List, anchor: stretch-bottom, rect: {top: 400, bottom: 300}, container: true}
  - {n: 3, name: Preview, anchor: top-center, pos: [0, -420], size: [500, 500]}
  - {n: 4, name: Btn_Buy, anchor: bottom-center, pos: [0, 150], size: [600, 140], text: {key: ui.buy, auto_size: true}}
---
