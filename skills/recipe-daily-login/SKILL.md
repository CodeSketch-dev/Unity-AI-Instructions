---
name: recipe-daily-login
description: "Daily login reward recipe: cycle config assets, claim states, unlock window, clock-tamper guard, missed-day handling, red dot. For daily login popups and streak rewards."
---

# Recipe: daily login

## Parts
- `Daily_Login_Asset[]` (reward type, amount, frame kind) registered in `Factory_DailyLogin`.
- `Data_DailyLogin`: start day or last claim time, claimed flags, last seen UTC max.
- Popup with per-day cells in states Locked / Today / Missed / Claimed; red dot on the HUD button while a claim is available.
- Reward receiver reuses the shop/currency grant path and the spread FX.

## Decisions the GDD must state
Cycle length, reset rule (calendar versus streak), unlock window (a bit under 24 h lets players claim slightly earlier each day), missed-day behavior (reset, skip, or recover by rewarded ad), and that the first popup appears after the tutorial.

## Clock guard (local-only)
Keep `lastSeenUtcMax`; if now is earlier by more than a few minutes the clock was moved back, so freeze claiming until it catches up. Cross-check with monotonic elapsed time in the session. Details in `recipe-retention-timers`.

## Wiring
Popup opened from the HUD button and optionally at session start; claim posts a stat event for quests; analytics `daily_claim`. Debug cheat to advance days in Editor only.
