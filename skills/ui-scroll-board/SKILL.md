---
name: ui-scroll-board
description: "Rules for scroll lists/grids (shop, inventory, collections) and list+preview popups: inset ScrollRect, rounded mask, slim scrollbar, spacing, state colours. Use when creating/fixing a ScrollRect list or its preview."
---

# UI scroll boards and list + preview popups

A scroll list looks professional only when the clipped area, the frame and the neighbours each keep their distance. These rules come straight from corrections on a real shop: a ScrollRect that filled the whole board spilled the last row over the frame border, tight cells and a fat scrollbar handle looked cheap, and a preview on a bright panel made portraits blend in.

## Anatomy (copy the reference, do not improvise)
```
Frame (thick sliced border)
 └─ Board            background panel, inset from the frame (>= 20 px) and from the neighbour panel (>= 10 px each side)
     └─ ScrollRect   INSET from the board: 25 px on every side, wider band (~45 px) on the scrollbar side. Never = the board.
         ├─ Viewport  stretches the ScrollRect, rounded Mask (sliced UIMask-style sprite, graphic hidden) = soft clipped corners
         │   └─ Content grid: spacing ~18-20 % of the cell, padding top 12-16, bottom 60-100 (last row can scroll clear of the edge)
         └─ Scrollbar slim (12-16 px) living in the right band
```
reference's measured values: scroll inset 25 px, grid cell 266 x 267 with spacing 49 / 55, bottom padding 100, scrollbar 22 px wide, elastic movement 0.1, inertia deceleration 0.135, auto-hide bar. Reproduce the proportions, scaled to the new cell size.

## Rules
1. **Scroll area smaller than the board, always.** A sliced frame has a thick border: content clipped at the frame edge draws over the border. Verify the bottom row in a screenshot.
2. **Mask for the board look** (rounded clip). Use RectMask2D only when the mask's stencil cost matters or a hard rectangle is wanted.
3. **Do the width maths before building**: `columns x cell + (columns - 1) x spacing + paddingLeft + paddingRight <= scroll width`. Run `scripts/grid_fit.py` with the real numbers; it flags overflow, cramped gaps (< 15 % of the cell), and a ScrollRect that is not inset.
4. **Breathing room**: gap between cells ~18-20 % of the cell width; frame -> board >= 20 px; board -> neighbouring panel >= 20 px in total; card inner padding so icon, name and button never touch each other or the card border.
5. **Scrollbar**: slim, inside the inset band, >= 8-10 px from the last column and >= 20 px from the board edge, shorter than the list (inset 40-50 px top and bottom so it never touches the rounded corners), auto-hide. Its handle must fill the sliding area on the cross axis (stretch it); otherwise a fat block appears next to the list. Use the project's bar track/handle sprites.
6. **Mobile feel**: elastic movement, inertia on, scroll sensitivity ~40, drag works on empty space between cells (transparent raycast image on the ScrollRect), cards are buttons with a pressed look, selection = a clear coloured outline.
7. **Sort so the useful items come first**: equipped, owned, then purchasable, then watchable/store-only; keep registry order inside each group.

## List + preview popups (shops, collections)
- A **windowed popup** (not full screen) unless the reference is full screen: list board on the left (~64 % of the width), preview panel on the right.
- The **preview has a dark stage**: a black rounded backdrop behind the portrait, portrait inset 14-16 px, `preserveAspect` on. Bright avatar art on a bright panel looks muddy.
- Order inside the preview: name at the top, stage, one-line hint, then the action button at the bottom. Nothing overlaps; the hint never touches the portrait.
- The preview shows the selected item; the action button shows what the item needs right now.

## State plates (cells and action button use the same colours)
| State | Colour / content |
|---|---|
| Equipped | cyan plate, "EQUIPPED", button disabled |
| Owned | blue plate, "OWNED" in the cell, "EQUIP" on the action button |
| Buy with money / gems | green plate with the currency icon and price; grey and red price when unaffordable |
| Reward (watch an ad) | **pink-purple plate with the ads icon and the word "FREE"** |
| Store / IAP | the store's localized price; grey when the product is not available, no action |
Locked items are dimmed (black ~40 %) so owned ones stand out. Remove states the game does not have (no daily system -> no "Daily" plate; sell only by reward and IAP).

## Verify (always, in the running game)
1. Open the popup from its real entry point and screenshot at the Game view resolution.
2. Check: last visible row stays inside the board; nothing touches the frame; scrollbar handle is slim and away from cells; preview text clear of the portrait; plate colours match the table.
3. Scroll to the end, select the last item, resize to a tall and a wide aspect (see `mobile-hud-layout`) and repeat.
4. If the item changes something in the world (a skin on the character), look at the world too: it must really change and be lit like the other characters.

`references/layout-example.md` has the full worked numbers of the skin shop this skill was written from.
