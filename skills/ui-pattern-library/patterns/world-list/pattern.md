# Pattern: world-list (select + teleport)

Source: report 07 sec 4 row 12 (`ME_World_Popup`, `ME_Teleport_Popup`; Board 1146x754 (y+22), title 700x90, ScrollRect inset (-79,-188), scrollbar 15 px, close 97x93; VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. List rules: `ui-scroll-board`; flow: `recipe-add-minigame`.

## Behavior and hooks
- Entries from a world list asset: unlock by currency or progress (typed numbers, no strings), coming-soon flag. A locked entry shows its requirement; tapping an unlocked entry posts `Event_Teleport(worldId)` (StaticBus) and closes the popup.
- The same data feeds the home-screen selection and the in-game popup (`mode-select-card`).
- Loading uses the project loader (`scene-flow` skills when added).

## Binding
`World_Asset` list (id, name, thumbnail, unlock cost/condition, scene), `Data_World` (unlocked ids, current).

## Variants
1. Entry style: row (default) / card grid. 2. Unlock: currency / progress / both. 3. Show current world marker.

## Checks
Locked entries never teleport; unlock spends once; scroll keeps last entry inside the board; contract lints; `ui-validator` clean.
