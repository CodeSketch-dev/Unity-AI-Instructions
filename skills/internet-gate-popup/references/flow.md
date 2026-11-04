# Flow and prefab tree

## Flow
```
Idle loop every 15 s (unscaled) -> CheckOnlineAsync
RequestCheck() (static)  <- called by the ads facade before ShowBanner / ShowInterstitial / ShowRewarded
   skip if popup showing or a check running
CheckOnlineAsync:
   IsCheckEnabled? (remote flag && !AdsRemoved && !VIP)   else => online
   internetReachability == NotReachable                   => offline (no network call)
   GET primary (captive-portal endpoint, 5 s)  ok         => online
   else GET fallback (anycast DNS trace, 5 s)  ok         => online ; else offline
offline => cover active, Warning state, Try Again enabled
Try Again => Reconnecting state for a minimum 5 s,
             then online => cover off, else back to Warning (button greyed while busy)
```

## Prefab tree
```
Internet_Popup (child of the popup canvas in the persistent root)   script: manager (root stays active)
 +- _root (toggled)
     +- Board
         +- Frame
         +- Text_Title            localized
         +- State_Warning         Text_Desc, Icon
         +- State_Reconnecting    Text_Desc, Icon + spinner
         +- Btn_TryAgain          Text (localized), grey material while busy
```

## Where it is wired
- ads facade: `InternetGate.RequestCheck()` before each show call
- remote config class: `bool isInternetRequiredEnabled = true`
- paid-user rule: `!AdsHelper.IsAdsRemoved && !Vip.IsActive`
- localization: title, description (two states), button = 3 keys
