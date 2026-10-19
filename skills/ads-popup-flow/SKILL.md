---
name: ads-popup-flow
description: Implement an ad/monetization sheet (interstitial/rewarded popups, boosters, show-conditions, placements) on top of the project ads SDK wrapper. Use when given an ad placement sheet or asked for inter/reward popups or boosters.
---

# Ads popup flow

Class names (`AdsHelper`, `Ads_Flow`, `Factory_<Monet>`) are the team's common pattern; map them to the project's real ads wrapper found in step 1. The behavior rules in section 3 are defaults from past sheets: the current spec/user message overrides them.

Use with `spec-pdf-extract` (read the sheet + demo first), `monetization-integration` (guardrails), `ui-popup-from-demo` (art), `playmode-script-testing` (verification), `done-means-wired`.

## 1. Inspect before writing
- The SDK wrapper (`AdsHelper`: ShowRewarded / ShowInterstitial(onClosed) / banner), the placement enum, `Ads_Flow`-style schedulers, the popup base class, the toast mechanism, the persistent-data pattern and the factory pattern. Reuse them; never add a parallel ads layer.
- What the SDK already does (App Open / resume / banner timing from remote config). Do not re-implement AOA; only expose the "from the 2nd launch" rule through the SDK config.
- Existing generic interstitials (popup-close, purchase) that the sheet does not ask for: put them behind config flags, default off.

## 2. Architecture (one feature = the full chain)
1. `Factory_<Monet>` ScriptableObject singleton: every time and amount of the sheet as editable fields (ladder arrays, intervals, countdown seconds, quiet-after-input seconds, booster tiers/duration, multipliers) plus the popup prefab refs. Static read-only accessors.
2. `Data_<Monet>` DataBlock: ladder tier indexes, booster tier + remaining seconds (written about once per second, not per frame).
3. Static runtime state (`Boost`): active / multiplier / next tier / grant / tick, events for the UI; reset statics on SubsystemRegistration.
4. `Flow` MonoBehaviour created per gameplay scene: one Update ticking timers; show-conditions in ONE function (no other popup open, not chased by a boss, not ragdolled, quiet N seconds after joystick/jump input, not carrying when tense). Add a static `LastInputTime` to the player control for the quiet rule.
5. Popups derive from the project popup base; ladder rows/cells are prefabs instantiated from the config array length (never hard-code 6 or 8).
6. New `AdsPlacement` entries per ad moment (claim, auto, close, rewarded, booster, real speed).
7. Multipliers hook at the single GDD-selected gain site, player only.
8. An editor builder (partial class) generates popups, HUD buttons, the factory asset and wires all refs; re-runnable.

## 3. Behavior rules that were easy to get wrong
- "AD PLAYS IN 3S" under a button = a countdown that ALWAYS ends with an interstitial (+ native fullscreen when loaded, `ShowInterstitialWithNative`). Default (confirm with the spec/user): after the countdown the inter plays, then the popup closes, the cash is granted and flies to the wallet (Currency Spread); Claim only locks the button. The popup is opened ONLY when `AdsHelper.IsInterstitialOKToShow` is true.
- A rewarded button never also shows the countdown interstitial on top of the rewarded ad: pause the countdown while it runs.
- X / No thanks on a rewarded offer = interstitial immediately, then close.
- A popup left unanswered a whole interval = destroy and re-call (new countdown + inter). At the max booster tier the offer switches to the cash popup.
- Booster ladder: each view while active = next tier and timer reset; after expiry the next view restores the last reached tier (no restart).
- Ladder UI states: done (check) / current (gold) / locked (lock); the offer shown = the next tier.
- Ads removed: skip the inter, keep rewards free, hide the countdown UI.

## 4. Traps found in practice
- A notification helper whose prefab is null throws and aborts the reward callback: use the project toast event inside ad paths.
- `Popup.Close()` is ignored while the open animation plays: close through a retry helper or the popup stays stuck with its buttons disabled.
- Do not edit generated HUD prefab output by hand; fix the builder and re-run it.
- In the Editor rewarded/inter return immediately (mock), so test timing by overriding the countdown, not by waiting.

## 5. Report
List what was verified in Play Mode (claim path, unclaimed path, rewarded path, decline path, booster grant, UI screenshots vs the demo), what needs a device with real ad IDs, and every sheet row not implemented (with the reason).
