# ui-spec schema (layout contract)

Source: report 21 section 1.4. YAML subset or JSON.

```yaml
id: UI-10-skin-shop                 # required, stable
type: ui_screen                     # required
kind: popup_fullscreen|popup_modal|hud|world_board|toast|banner
fidelity: exact|faithful|free       # exact needs a capture per state
pattern: ui-pattern-library/skin-shop   # builder pattern or "custom"
opened_by: [btn_shop@UI-00-hud, event:shop_requested]
closes_on: [btn_back, esc, backdrop_if_modal]
reference_canvas: {w: 1080, h: 1920, match: 0.5}   # required: capture resolution (w,h > 0)
captures: [CAP-031@00:00]
elements:                           # required; one row per node
  - {n: 1, name: BtnBack, anchor: top-left, pos: [92, -87], size: [179, 161], sprite: A-040, behaviour: close}
  - {n: 3, name: ItemList, anchor: stretch-bottom, rect: {top: 958, bottom: 223}, kind: scroll_grid, cell: {size: [250, 300], columns: 3, spacing: 16}}
  - {n: 4, name: BtnBuy, anchor: bottom-center, pos: [0, 110], size: [811, 141], text: {key: ui.buy, auto_size: true}}
states: [default, item_owned]
animation: {open: {kind: scale_outback, from: 0.3, t: 0.1}, press: {scale: 0.9, t: 0.1}}
```

## Anchors
`top-left top-center top-right mid-left center mid-right bottom-left bottom-center bottom-right` (fixed: need `pos` and `size`); `stretch stretch-top stretch-bottom stretch-left stretch-right` (need `rect` insets).

## Lint codes
`missing-key`, `bad-canvas`, `missing-name`, `duplicate-name`, `duplicate-number`, `bad-anchor`, `missing-pos`, `missing-size`, `missing-rect`, `text-no-key`, `unknown-child` (children are element names defined in the same list).

## Conversion
`scale = (gameW/capW)^(1-match) * (gameH/capH)^match`; positions, sizes and insets are multiplied by it. Stretch output: `offsetMin = (left, bottom)`, `offsetMax = (-right, -top)`.
