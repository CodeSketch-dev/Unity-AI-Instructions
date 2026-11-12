---
name: internet-gate-popup
description: "Use when adding or fixing the no-internet popup and connectivity check: adapter check plus ping with fallback, check before ads, Try Again, remote switch, bypass for paid users. Covers the framework Internet module versus a custom manager."
triggers: no internet, internet check, internet gate, offline popup, connectivity, try again, captive portal, airplane mode, mat mang, kiem tra mang, popup mat ket noi, khong co mang, kt style
---

# Internet gate popup

A blocking "No internet / Try Again" cover shown when the device is really offline and the game is about to need the network (ads) or periodically. It is a cover, not a state flag: gameplay stays correct offline and paid users are never blocked.

## 1. Decide the implementation (check the installed package API first)
- SketchEngine ships `SketchEngine.Internet` (static `Internet`, auto-starts at `AfterSceneLoad`, 15 s unscaled monitor, popup prefab through the framework factory, `InternetPopupView` with `OnRetry`, `ShowWarning`, `ShowReconnecting`). When it is installed: assign the popup prefab in the factory, set `Internet.SkipCheck` (bypass rule), and place no second popup.
- It has no "check now" call and its `IsEnabled` is false until the first 15 s tick. If ads must request a check before showing, write a thin custom manager ([sample](references/InternetGate.cs.txt)) or add the on-demand method to the project-side wrapper. Never run both popups.
- If a vendor SDK ships its own no-internet popup, disable it (constant or flag) or you get two.

## 2. Flow ([diagram](references/flow.md))
1. Idle loop every 15 s on unscaled time; skip while the popup shows or a check runs.
2. `RequestCheck()` (static) is called by the ads facade before banner, interstitial and rewarded; skip if already checking.
3. `IsCheckEnabled = remoteFlag && !adsRemoved && !vip`; disabled means "online".
4. `Application.internetReachability == NotReachable` means offline with no request.
5. Otherwise `GET` a primary URL (a captive-portal endpoint), then a fallback URL; 5 s timeout each; ok = online.
6. Offline: show the cover with Try Again. Try Again shows "Reconnecting" for a minimum of 5 s so the tap visibly does something, then closes if online, else back to the warning.

## 3. Gating rules
- Ads: gate ad requests (cover appears, the ad simply does not show). Rewarded: failed check = localized toast and `callback(false)`.
- IAP: do not hard-gate the buy button; the store dialog reports failure itself. Studio recommendation: call `RequestCheck()` first so the player sees the same popup, but keep restore and ads-removed purchases working.
- Remote flag (`isInternetRequiredEnabled`, default true) turns the whole gate off without a build. Ship dark first if the store policy is uncertain.
- Bypass for users who removed ads or own VIP (they have no network-only features).

## 4. Prefab ([tree](references/flow.md#prefab-tree))
Child of the popup canvas inside the persistent root: Board with title, two state groups (Warning, Reconnecting), Try Again button. Three localized keys. Authored in Edit Mode; runtime only toggles states. Keep the root GameObject always active and toggle a child `_root`; disabling the root cancels the monitor token and the next outage is never detected.

## 5. Done check
- Airplane mode on a real device: popup appears; Try Again shows Reconnecting >= 5 s; turning the network on and tapping closes it.
- Wi-Fi with no WAN / captive portal: popup appears (adapter alone is not proof of internet).
- Ads-removed and VIP profiles: no popup offline.
- Remote flag off: no popup, ads still fail safe.
- Only one popup exists in the project (grep prefabs and SDK scenes).
- Popup does not stack with a native ad or banner; sort order above gameplay popups, below the transition.

## Pitfalls
- `internetReachability` reports an adapter, not working internet.
- Endpoint choice: the primary should not be blocked in your markets; keep a second provider; use GET (some endpoints return 405 to HEAD).
- Always call the guarded public `RequestCheck`, never the inner check (re-entrancy guard).
- Do not use scaled time; the popup must work while paused.
- A state-flag design ("isOnline") spread through gameplay is a bug source; keep gameplay offline-safe.
- Test on a device: the Editor reports online.
