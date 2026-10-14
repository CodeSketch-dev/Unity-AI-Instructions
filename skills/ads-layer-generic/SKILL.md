---
name: ads-layer-generic
description: "Provider-agnostic ads: adapter, policy and static facade layers, fake Editor provider, consent state, placement enum. Use when adding or porting ads to any game."
---

# Ads layer (generic)

Mechanism is shared by every app; only the keys differ per app. Extends `ads-popup-flow` (when to show) and `monetization-integration` (what to ask the human).

## Three layers
1. **Provider adapter** (`IAdsProvider`): `Init(consent)`, `Load/Show(format, placement)`, `IsReady(format)`, events shown/closed/rewarded/failed/paid. One adapter per SDK plus a fake one.
2. **Policy** (pure C#, unit-testable): remove-ads flags, cooldowns, session and level gates, per-placement enable. Inputs are a local config asset overlaid by remote config when the project has it; no provider types inside.
3. **Facade** `AdsHelper` (static): the only API gameplay may call. `ShowRewarded(placement, Action<bool>)`, `ShowInterstitial(placement, onClosed)`, `ShowBanner/HideBanner`, `IsRewardReady`, `IsInterstitialOkToShow`, `IsAdsRemoved`.

## Rules
- The rewarded callback fires exactly once. Not ready: `false` plus a localized "no ads" toast.
- Remove-ads removes banner and interstitial, not rewarded.
- Placement is a stable int enum; the enum name is what is logged and configured.
- Interstitials only at natural breaks (death, result, popup close). Never during the first-time tutorial, never on top of a rewarded.
- Keys live in a per-app config asset, never in code. Reuse the project's existing SDK wrapper if one is installed before writing adapters.

## Fake provider (Editor and tests)
A full-screen overlay with Reward, Close, "simulate no-fill" and "simulate fail" controls, so no-fill and closed-early paths are exercised. Add debug-menu rows through `debug-cheats-menu`.

## Consent
`IConsentService` with `Unknown/Granted/Denied/NotRequired`; denied passes limited-ads to the provider. Kids audience or region rules are a human decision.

## Done means
Every placement in the GDD has a call site, a fallback when no ad, and a logged event (`analytics-events-taxonomy`).
