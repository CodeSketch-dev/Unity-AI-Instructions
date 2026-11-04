# Ads gate facts from the reference game

Reference facts to seed a policy; every number is a default that must be remote-configurable. The data-driven matrix and its test live in `ads-layer-generic/references/ads-gate-matrix.md`.

## Interstitial gate order (first failing gate returns "do not show")
1. remove-ads flag (purchase or VIP)
2. per-placement block (placement config `enable == false`)
3. store-review build gate (a remote value that hides ads while a version is in store review; the app version is parsed from `Application.version`, so keep it in a fixed `1.N` shape)
4. session gate (minimum session count)
5. time since first install >= start delay (default 60 s), ALWAYS checked, even when a caller asks to skip the cooldown
6. time since last interstitial >= spacing (default 60 s), skipped only when the caller passes skipTime
7. provider reports ready

## Other formats
- **Rewarded**: flag-skipped grants success at once; else internet check; not ready -> localized toast and `callback(false)`; remove-ads does NOT remove rewarded. The Editor mock always succeeds.
- **App open**: on resume and once at cold start; blocked within 30 s of an interstitial, before the start delay, with remove-ads.
- **Banner**: deferred until the start delay since first install; shown at scene start, minigame selection, home return, death/revive; hidden when VIP starts.
- **Native**: shared cooldown (15 s) and start delay (60 s); in-rect variant only; popups shift to make room; closing a popup hides the native inside a guard window (300 s, remote); blocked until the tutorial is done.
- **Ad loading cover**: optional 2 s "loading ad" cover before an interstitial, remote-switchable per placement.
- **Retry**: ad load retry with exponential backoff `2^min(6, attempt)` s.

## Remote-configurable timings (all of them)
Start delays (banner, app open, native, interstitial), spacing (interstitial, native), native close guard, ads-break enable, per-placement overrides, store-review gate value, internet-required flag.

## Dev kill switches
A free-ads flag honoured only in the Editor or Development builds; debug toggles for banner/inter/reward skip. Never ship a kill switch that works in release.

## Real-device-only behaviour
Native ads need a real device (JNI). One reference bug ("native does not close") worked in the Editor mock and failed on device. Treat ads, native and consent as device-tested features.
