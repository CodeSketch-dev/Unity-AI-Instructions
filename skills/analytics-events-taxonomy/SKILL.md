---
name: analytics-events-taxonomy
description: "Analytics event taxonomy: naming rules, parameter limits, standard event groups, funnels, per-game docs/analytics-events.md. Use before adding any logged event."
---

# Analytics events taxonomy

Edit the game's `docs/analytics-events.md` first; code only logs events listed there.

## Rules
- lower_snake_case names and params, at most six params, no personal data.
- Log through one facade (the project's analytics wrapper); Editor builds log to console only.
- Persisted "once" milestones use a persisted max so they never refire.
- Aggregate high-rate events (earn per 30 s, not per tick).
- Payer flag comes from the IAP data and is attached as a user property.

## Standard groups
Session (`session_start`), tutorial (`ftue_step`, `ftue_complete`), progress (`level_start/win/lose`, `zone_unlock`), economy (`currency_earn/spend`, `upgrade`), ads (`ad_offer/show/complete/fail`, `ad_revenue`), IAP (`iap_view/click/success/fail`), meta (`daily_claim`, `wheel_spin`, `quest_claim`, `code_redeem`, `offline_claim`, `rating_ask`), settings (`setting_change`), health (`user_drop`, `save_recovered`).

## Funnels
Tutorial steps to first level; ad offer to complete per placement; IAP view to success; retention from `session_start`.

## user_drop
Mark a check on disk when a risky moment starts (ad, attack), clear it after a short delay; log pending checks on next launch to detect kills and rage-quits.

A GDD feature lists the events it needs; add them to the doc, then code.
