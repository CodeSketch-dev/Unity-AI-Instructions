---
name: recipe-retention-timers
description: "Retention timers: clock-tamper guard, offline earnings with cap, local notification table, redeem codes. Use for any feature that depends on real time away from the game."
---

# Recipe: retention timers

## Clock guard
Persist `lastSeenUtcMax`. If UTC now is earlier by more than a few minutes, freeze time-gated claims until now catches up. Cross-check with monotonic elapsed time within the session.

## Offline earnings
On pause/quit and periodically store `lastActiveUtc`. On launch `elapsed = clamp(now - lastActive, 0, capHours)`; ignore negative and below a minimum. Persist the pending gain before showing the popup (survives a kill). Popup after the tutorial, claim x1 or watch a rewarded ad for more. Rate, cap and multiplier are GDD values. Timers (eggs, crops) catch up by elapsed time in the same pass.

## Local notifications
A `Factory_Notification` table: reward ready, free spin ready, offline cap full, timer complete, comeback. Limits: few per day, quiet hours, localized text, permission asked after a first positive moment, settings toggle cancels all. Use the framework notification module only if installed.

## Codes
Ship hashed codes (hash of normalized code plus salt) with reward and expiry; keep a redeemed-hash set in data; throttle wrong attempts. Without a server codes cannot be revoked.

## Wiring
Analytics `offline_claim`, `notif_permission`, `code_redeem`. Test with the clock moved both ways (`playmode-script-testing`).
