# Pattern: vip-pass (subscription / hero offer)

Source: report 07 sec 4 row 11 (`IAP_Subscription_VIP_Pass`; Board 1432x743, art 603x346, title 450x224, benefits VLG 667x382, button 525x135, close 100x100; VERIFIED). The spec compresses benefits (230 high, scrolls if longer) and title (190) so leaf rects never overlap: those two heights are INFERRED. Contract: `spec.yaml`; wireframe `mockups/wireframe.png`. Purchase: `unity-iap-port`.

## Behavior and hooks
- Benefits are rows from data (`IAP_VIP_Pass_BenefitText` style), each with icon + localized text.
- Buy starts the subscription/product purchase; entitlement checked on boot and refreshed (`IAP_Subscription_AutoRefresh`); expiry falls back to defaults (e.g. default skin) with a notice.
- Owned state replaces the button with "Active" and the renewal date if the store reports it.

## Binding
Product id, benefit list, entitlement data block, auto-refresh service.

## Variants
1. Offer type: subscription (default) / one-time pass. 2. Art: static / animated. 3. Trial text shown by store data only.

## Checks
Price and period text from the store; expiry flow tested with a mocked expiry; benefits readable at the smallest aspect; contract lints.
