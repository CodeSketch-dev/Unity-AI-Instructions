# Pattern: inventory

Source: report 07 sec 4 row 9 (`Item_Inventory`; Board 1154x800 at y+50, title h75, ScrollRect inset (-116,-205) y-62, close 97x93, dim 0.86, open 0.3 / close 0.2; VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Grid rules: `ui-scroll-board`; tool/item data: `tool-weapon-pipeline` (when added).

## States
| State | Visual |
|---|---|
| empty | centred hint text and a button to the source (shop) |
| item selected | frame ~9 px larger per side; detail strip appears (variant) |
| equipped | check marker; one equipped per slot type |

## Behavior and hooks
Items by `Item_Asset` id; counts in the data block; tap selects, a second action equips/uses (hotbar assignment variant). Use events for changes (`Event_Item_Changed`), no per-frame refresh. Locked/unowned entries are hidden or shown as silhouettes (variant).

## Binding
Item registry (`recipe-add-skin-or-item`), `Data_Item` counts, slot definitions.

## Variants
1. Detail: none (default) / bottom strip / right panel. 2. Categories: none / tabs (`ui-tabs`). 3. Sort: acquired / rarity.

## Checks
Last row stays inside the frame; empty state reachable; equip survives restart; contract lints; `ui-validator` clean.
