---
name: ui-design-tokens
description: Quantized UI sizes, spacing, insets and design principles mined from reference prefabs, to build consistent screens from a spec alone. Use when choosing sizes or spacing for any new UI element and no mockup supplies them.
---

# UI design tokens and principles

Why tokens: vibe-coded UI drifts into near-identical or uneven screens when sizes are guessed. Mined values come from reference prefabs on a 1920x1080 Expand canvas (handoff UI findings + report 07, VERIFIED counts). They are soft defaults: when the project's reference shows other values, the reference wins and the token set is regenerated (`tools/ui_miner` task, planned).

## Principles
1. Sizes are **quantized**: button heights 80-120, widths 100 / 280 / 350, close buttons 97x93 or 100x100. Pick from the scale instead of inventing values.
2. **ScrollRect is always inset** from its board (about 20-40 px at the sides, 40-90 at top and bottom); never equal to the board (`ui-scroll-board`).
3. Image layers fill their parent (inset 0); TMP inset ~10 px per side; the group icon+text is centred (`ui-icon-label-layout`).
4. Selected frames are ~9 px larger per side than the cell.
5. Per-state sibling buttons or child objects, not conditional sprites (`ui-button-anatomy`).
6. Anchor to the owning edge or corner, never to centre-based absolute coordinates; every element sits inside the safe area; no overlap including conditional elements (`unity-ui`).
7. Spacing is proportional to the element: gaps ~18-20% of the cell; consistent margin per screen.

## Tokens (reference, 1920x1080)
| Token | Value |
|---|---|
| Large board | 1146x754 or 1154x768 |
| Medium / small board | 800x650, 665x512, 528x435 |
| Skin shop | board 1095x700 + preview 435x700 |
| Grid cell / spacing | 266x267, 49x55, 3 columns |
| Close button | 97x93 or 100x100, inset ~65-70 top-right |
| Page title bar | ~175 high, back button ~103x107 |
| Notify dot | ~40x41 at (-10,-6.5) |
| HUD bars | top-center y -87..-150, 484x39 or 834x83 |
| Spacing in HLG | 5 / 10 / 15 |
| TMP autosize | min 18, max 36-72 |

For checking the numbers use `ui-popup-from-demo/dump_prefab.py` (read reference sizes) and `ui-scroll-board/scripts/grid_fit.py` (grid maths); for patterns see `ui-pattern-library`.

## Regenerate tokens from a reference project
`py -I <skills>/ui-design-tokens/scripts/ui_miner.py <unity-project> --root Assets/_Game --out tokens.json` (read-only, stdlib, a few seconds). It reports canvas modes/sort orders/scalers, fixed-size button sizes and the scripts co-attached to buttons (resolved from `.cs.meta`), TMP autosize/min/max/raycast ratios, Image raycast ratio, ScrollRect insets, linear-layout spacing, grid cells, and name prefixes. Check on knife-tower: 451 TMPs, 80% autosize, min 18 on 328, 82% raycast off, 786 images (39% raycast off), top button size 347x116, which match report 07. Limits: only objects directly inside a prefab are read (nested prefab-instance overrides are not resolved, so counts run a little below report 07); non-UI prefabs that contain a RectTransform add noise to the name prefixes; sizes with stretched anchors are skipped. Treat the output as observations; the reference game of the current task wins over any mined default.
