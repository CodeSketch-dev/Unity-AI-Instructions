# Pattern: mode-select-card

Source: report 07 sec 4 row 7 (`Minigame_Selection_Item` + `_Large`; sizes VERIFIED, thumbnail anchors (0.06,0.09)-(0.94,0.82)). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Registration chain: `recipe-add-minigame`.

## Regions
Card 488x357 (a button): thumbnail inset in anchors, a top title strip with the name on the left (0.03-0.72) and a status group on the right (0.76-0.975), `Frame` overlay for selection, `CommingSoon` full overlay. The Large variant is the same prefab bigger for the featured entry.

## States
default; selected (frame); locked (dark overlay + lock/requirement, tap shows a toast); coming soon (overlay, not interactive).

## Behavior and hooks
Entries come from the factory list in saved sort order (remote-config can reorder with aliases). Tap loads the scene through the loader (`recipe-add-minigame`); status icons come from data (new, best score, locked).

## Binding
`Minigame_Selection_Asset` (type, title, thumbnail, load type, coming-soon flag), `Data_Minigame` (entered, completed).

## Variants
1. Layout: one large + N small (default) / uniform grid. 2. Status: icon row / text. 3. Lock reason shown: toast (default) / on card.

## Checks
Tap target >= 88 px; selected frame never clipped; coming-soon cards ignore taps; long names autosize (`ui-text-tmp`); contract lints.
