---
name: revive-result-flow
description: "Revive and result flow: timed revive popup, rewarded ad revive, give-up interstitial, result routing and rewards. Use for death, fail and win screens."
---

# Revive and result flow

- Death opens a timed revive popup; the timer pauses while an ad plays.
- Revive button: rewarded ad (VIP or entitlement may skip it if the GDD says so). Success revives at the last checkpoint after the popup closes; failure resumes the timer and shows a toast.
- Give up or timeout: interstitial at this natural break (via `ads-layer-generic`), then the result screen.
- Result screen: rewards granted to Data first, spread FX, double-reward ad, continue; events from the taxonomy.
- Revive posts one event consumed by checkpoint logic (`checkpoint-respawn`).
