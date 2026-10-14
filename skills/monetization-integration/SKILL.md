---
name: monetization-integration
description: "Monetization hooks behind interfaces: rewarded/interstitial ads, IAP, daily reward, offline earnings, consent/ATT/GDPR, kids constraints, Editor mocks. Use when adding ads, IAP, shop, boosters or store compliance."
---

# Monetization integration

Roblox-style games monetize through multipliers, convenience and cosmetics. Integrate the hooks early behind interfaces so gameplay code never depends on a specific SDK, and so everything is testable in the Editor.

## Placement ideas by genre loop
- **Rewarded ads** (opt-in, always with clear reward): 2x income for N minutes, free egg/spin, revive, skip wait, double offline earnings, extra daily reward.
- **IAP**: starter pack (one-time, early), permanent 2x pass, VIP, extra slots/auto features, cosmetic trails/skins, currency packs.
- **Interstitials**: sparingly at natural breaks (never mid-action, never during FTUE); cap frequency.
- **Daily reward / streaks / timed events**: retention drivers, server-independent where possible but guard against clock tampering if value is high.
- **Offers**: contextual (when the player hits a wall or lacks currency), limited by cooldown.

## Guardrails (agreed in past projects)
Monetization must reinforce the progression loop, never replace it: rewarded boosts are optional value (recovery, temporary acceleration), interstitials only at natural breaks with a cooldown, IAP is utility or cosmetic, and nothing is a forced paywall. Account for ad and IAP effects in the balance model (`economy-progression-design`).

## Architecture
1. `IAdsService`, `IPurchaseService`, `IAnalyticsService`, `IConsentService` interfaces with SDK-specific adapters and an **Editor mock** (simulated delays, success/failure toggles).
2. Gameplay requests via a small API (`ShowRewarded(placementId, onReward)`); rewards defined in config assets keyed by placement id.
3. Entitlements (passes, no-ads) in persisted data and re-validated on startup (restore purchases).
4. Feature flags/config for frequencies and prices so designers can tune without code.
5. Events for analytics: placement shown, accepted, completed, failed; purchase funnel. Define a taxonomy in `docs/analytics-events.md` before adding calls.

## Compliance (flag early; the human decides)
- Consent: GDPR/UMP prompt where required; iOS App Tracking Transparency only if tracking.
- Roblox-like games attract children. If the audience includes kids, store policies (Google Families, Apple Kids) restrict ad networks, personalized ads and tracking; choose SDKs/configurations accordingly and set the correct age/target declarations.
- Privacy policy, data safety/nutrition labels, in-app purchase disclosures.
- Always use SDK **test mode/test IDs** in development; never commit real app IDs/keys or secrets; load production ids from ignored config.
- Never auto-play paid flows in tests; use sandbox accounts.

## Verify
Editor mock flows (success, failure, cancel); rewards granted exactly once; entitlements persist after restart; no gameplay blocking when ads fail to load; no ads in the FTUE; `done-means-wired` wiring check for the buttons.
