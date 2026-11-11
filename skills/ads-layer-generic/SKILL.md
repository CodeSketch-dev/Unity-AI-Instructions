---
name: ads-layer-generic
description: "Provider-agnostic ads: adapter, policy and static facade layers, data-driven gate matrix, fake Editor provider, consent, placement enum, real-device test rule. Use when adding or porting ads to any game."
triggers: ads, rewarded, interstitial, banner, native ad, app open, ads gate, gate matrix, consent, ump, att, placement, quang cao, chan quang cao, remove ads
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

## Gate matrix (data, not scattered ifs)
Specify the gates up front as a table, scene x tutorial x level x popup x time since install/last ad/last native, and keep it in config: [ads-gate-matrix](references/ads-gate-matrix.md). The policy reads the table; remote config overlays the numbers from the first commit. A table-driven EditMode test walks every row. Reference facts (gate order, default timings): `app-services-bootstrap/references/ads-gates.md`.

## Consent
Design target (a studio addition: the reference game keeps consent inside its ad-network manager and has no consent interface): `IConsentService` with `Unknown/Granted/Denied/NotRequired`; denied passes limited-ads to the provider. Kids audience or region rules are a human decision.
- Every consent outcome (granted, denied, error, not required) converges on ONE guarded `StartAdsInit(reason)`; never call the SDK init from several branches, and init even if consent failed.
- Init and show calls on the main thread; retry load after 2 s; refresh native about every 30 s.
- iOS: read the tracking status inside the request callback; right after the request it is still "not determined".

## Real-device rule
The Editor fake provider cannot prove native ads, consent, app-open or close behaviour. Test them on a real Android device before calling ads done; one reference bug ("native does not close") passed in the Editor and failed on a phone. Keep SDK keys in ignored per-app config assets; never copy keys from another app or a repo.

## Done means
The gate-matrix test is green and the real-device checklist ran. Every placement in the GDD has a call site, a fallback when no ad, and a logged event (`analytics-events-taxonomy`).


## Call chain (owner law)
Game decision layer (e.g. `Dig_Ads`: WHEN) -> game adapter `AdsHelper` (the only file that references the SDK) -> shared SDK facade (`SketchSdk`: mechanism, providers, pure policy / fit helpers, Editor fake provider). The SDK never knows popups, shops or currencies; the decision layer never calls the SDK directly.

## Editor fake provider contract (owner 2026-11-10)
- In the Editor EVERY format is ready (`IsReady` true) and rewarded completes immediately with `true` (Knife Tower AdsHelper parity), otherwise reward buttons are disabled or grant nothing and the whole reward flow cannot be played.
- The fake native in-rect panel (label with its pixel size + close button with the real countdown) must appear in BOTH the Game view and the Device Simulator: find the window by type name `GameView` OR `SimulatorWindow` (the Simulator is a different type), prefer the focused/visible one. Break and Steal ships the same fake (`NativeHalf_FakeProvider`/`FakeView`); read it before porting.
- Verify with a Play script (`Dig_Ads.ShowRewarded` returns started + granted) because the IMGUI overlay is not captured by ScreenCapture.
