---
name: settings-pause-offline
description: "Settings screen, pause popup and app pause/resume handling: toggles, language, quality, restore, privacy rows, timeScale and audio group. Use when building settings or pause."
---

# Settings, pause, resume

## Settings screen
Rows: music, sound, vibration (haptics throttled), language, quality (maps to the project's URP tier and target fps, default from `device-tier-policy`), notifications, restore purchases, privacy policy and terms, manage consent, rate, contact, version. Hide destructive reset unless the GDD asks.
Data: `Data_Settings` DataBlock; one binder applies values at boot and on change (`DataValue.OnValueChanged`).

## Pause
`Pause_Popup` sets `Time.timeScale = 0`, pauses the SFX group (music ducks), buttons Resume / Settings / Home. Popup tweens must ignore time scale. Do not allow pause while a rewarded ad is showing. GDD says which screens pause and whether income timers stop.

## App pause/resume
`OnApplicationPause(true)` saves data and stores last-active UTC; on resume re-sync UTC-based timers and refresh subscription state. Offline earnings: `recipe-retention-timers`.
