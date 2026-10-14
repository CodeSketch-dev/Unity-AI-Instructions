# Pattern: side-tab-shop

Source: report 07 sec 4 row 8 (`Shop_All`, `Shop_All_Tab_Item`; sizes VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Tabs mechanism: `ui-tabs`; grids inside: `ui-scroll-board`; item entries: `skin-shop`.

## Regions
Page: title bar (~175) with back button, left `ScrollRect_Tab` 285x740 with tabs 222x82 (icon 101x81 left, label, notify dot top-right), content area to the right holding one stacked panel per tab (Speed, Trails, Offers, Sounds...).

## Behavior and hooks
- Tab click posts `Event_Shop_TabSelected(type)`; tabs swap on/off frames, panels toggle (`ui-tabs`). Default tab is explicit; remember the last tab per session.
- Notify dots from data events (new offer, free item); sold-out/owned items sort last; Offers tab hosts IAP cards (`iap-carousel`).
- Currency bar stays visible (HUD) while the page is open.

## Binding
Tab list (type, icon, label key, dot source), per-panel item registries, IAP catalog.

## Variants
1. Tabs: left strip (default) / top strip. 2. Panels built lazily on first show (default) / all at open. 3. Per-tab sort rules.

## Checks
Every tab opens its panel; dot clears when seen; strip scrolls with 8+ tabs; selected tab is visible without relying on colour; contract lints; `ui-validator` clean.
