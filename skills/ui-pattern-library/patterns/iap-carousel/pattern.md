# Pattern: iap-carousel

Source: report 07 sec 4 row 10 (`IAP_NoAds_Popup`; ScrollRect full width h631, Content = HLG + ContentSizeFitter of pack cards, close anchored near (705,375); VERIFIED). Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Purchase mechanics: `unity-iap-port`, `monetization-integration`.

## Behavior and hooks
- No board: dimmed backdrop, cards slide in. Each card is a codeless IAP button bound to a product id (store-localized price text), with a "best value" ribbon variant.
- Owned products show "Owned" and disable; restore purchases lives in Settings (`settings`).
- Grant only in the purchase callback; persist the entitlement (remove-ads, VIP) through the data block; fire `Event_IAP_Purchased(id)`.

## Binding
IAP catalog (product id -> reward, icon, ribbon), entitlement data, price strings from the store (never hard-coded).

## Variants
1. Cards: 3 (default) / 2 / scrolling list. 2. Ribbon: none / best value / most popular. 3. Entry: from shop Offers tab / HUD offer button / timed popup.

## Checks
Price text comes from the store; purchase cancel changes nothing; owned state after restart; close reachable at 20:9; contract lints.
