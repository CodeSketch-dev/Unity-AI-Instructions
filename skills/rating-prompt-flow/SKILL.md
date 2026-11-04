---
name: rating-prompt-flow
description: "Use when adding the store rating or review prompt: eligibility gate, trigger moments, good versus bad path, in-app review with store fallback, persistence, cooldown, per-session guard. Use before wiring any rate-us button or popup."
triggers: rating, review, rate us, rate popup, in-app review, store review, five stars, danh gia, danh gia ung dung, 5 sao, cham sao, kt style
---

# Rating prompt flow

Ask for a store rating at a good moment, once, without nagging, and never depend on the network. The in-app review API is quota-limited by the store: a pre-question ("Do you like the game?") decides who is sent to it.

## 1. Gate (one pure function)
`CanShow()` is true only when ALL hold:
- not already rated (persisted)
- not asked in this session (NOT persisted; recreate the flag on every data load, e.g. `new DataValue<bool>(false)` in `Init`, instead of the usual `??=`)
- the tutorial is completed (shared tutorial-done flag, `tutorial-phase-system`)
- studio improvement over the reference (it has none): a cooldown and a launch counter. Defaults: at least 3 sessions, at least 24 h since the last ask, at most 3 asks per app version, never within 2 minutes of an interstitial, never while a rewarded/IAP flow is open.

## 2. Trigger moments (call sites)
Only after a positive moment, two sites at most: tutorial completed, and a win/revive result. Never at launch, during gameplay, after a loss streak, or on top of another popup (queue through the popup manager). Check the gate inside the single `RatingHelper.Show()`; call sites do not repeat the checks.

## 3. Flow
```
trigger -> RatingHelper.Show -> CanShow? -> popup (pre-question or stars)
Good (>= 4 stars / "Yes") -> in-app review (store page fallback) -> persist RatingDone
Bad / dismiss              -> set the session flag only, optionally open a feedback mailto
```
- Android: SketchEngine `SketchEngine.AppStore.AppStore` (`Init()` pre-warms the review flow, `Review()` launches it and falls back to `OpenStore()` when the flow is unavailable). Needs the Play Review packages and the `SKETCHENGINE_APPSTORE` define; check the installed module and Android define list first.
- iOS: `AppStore.Review(appStoreId)` (system prompt, store page fallback). Implement the iOS branch; the reference left it commented out so iOS never rated.
- The in-app review dialog may silently not show (quota); persist `RatingDone` on the good path anyway, or count asks per version, to avoid a retry loop.

## 4. Offline-safe
No network call is needed to decide or to show the popup. The store call may fail offline: the fallback `OpenStore()` can fail too; swallow errors, do not block the game, and do not mark rated if the launch threw. Do not run the internet gate before rating.

## 5. Data and prefab
- `Data_Rating : DataBlock`: `RatingDone` (persisted), `RatingInThisSession` (session), `AskCount`, `LastAskUtc`, `LastAskVersion`. Fix the reference bug: a count field that nothing increments.
- Popup prefab registered in the prefab factory and spawned with `PopupManager.Create`; authored in Edit Mode ([tree](references/flow.md)). Press feedback and sfx on both buttons; text localized.

## 6. Done check
- EditMode test of `CanShow` over the matrix (tutorial not done, done, rated, asked this session, cooldown, version cap).
- Play with a fresh save: popup appears only after the tutorial at the trigger moment; Good path persists; relaunch does not ask again; Bad path asks again next session only after the cooldown.
- Real Android device with the Play Review package: review sheet opens (cannot be proven in the Editor).

## Pitfalls
- Asking twice in one session; asking before the tutorial; asking right after an ad.
- Persisting the session flag by accident (the "this session" trick relies on not persisting it).
- Declaring success from the Editor: the in-app review API only works on a store-installed build.
- Bad path that calls the review API: wastes quota and invites bad reviews.
