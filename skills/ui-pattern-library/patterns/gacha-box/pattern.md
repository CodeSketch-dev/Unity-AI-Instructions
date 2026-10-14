# Pattern: gacha-box

Source: report 07 sec 4 row 3 (`Gacha_Box_Popup`, item, reveal in the HUD canvas; sizes VERIFIED). Economy: `economy-progression-design`; odds are the designer's decision (user decision 2026-10-15), tuned by the balance loop. Contract: `spec.yaml`; wireframe `mockups/wireframe.png`.

## Regions
Board 1154x769 with a title, an inset scroll area (940x454) listing contents, a 347x116 open button (price or ad), close. Reveal overlay (state) shows the item name/title dropping in, then `Btn_Equip` and `Btn_NoThanks`.

## Reveal sequence (values from knife-tower)
Name and title `DOAnchorPos` 0.5 s OutBack from a 24 px top margin, lead delay 0.06; buttons scale 0 -> 1 in 0.28 s OutBack, start delay 0.1, stagger 0.08. Duplicate result shows a "duplicate" marker and converts to a currency reward (variant).

## Behavior and hooks
- Result is chosen BEFORE the animation (weights/pity in the factory) and persisted before showing, so a quit mid-animation cannot lose or re-roll it.
- Pay with currency or a rewarded ad (`ads-popup-flow`); spend only on success.
- Events: `Event_Gacha_Opened(item)`, equip posts the equip event of the item system (`recipe-add-skin-or-item`).

## Binding
Box asset (cost, currency, weights, pity counter), item registry, `Data_Gacha` (pity, opened counts), rarity colours from the theme.

## Variants
1. Cost: currency (default) / ad / both. 2. Show odds list: hidden (default, designer choice) / shown. 3. Duplicate handling: refund currency (default) / skip.

## Checks
Kill the app during the reveal: item still owned once; pity counter persists; Equip works for a fresh item; both reveal buttons reachable at 20:9; contract lints; `ui-validator` clean.
