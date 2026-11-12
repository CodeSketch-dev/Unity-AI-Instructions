---
name: settings-pause-offline
description: "Settings screen, pause popup and app pause/resume handling: toggles, language, quality, restore, privacy rows, timeScale and audio group, offline earnings stamp. Use when building settings or pause."
triggers: settings, setting popup, pause popup, pause menu, resume, restore purchases, privacy row, vibration toggle, music toggle, offline earnings, welcome back, cai dat, tam dung, thu nhap offline
---

# Settings, pause, resume

## Settings screen
Target rows: music, sound, vibration (haptics throttled), language, home (hidden when already home), quality (maps to the project's URP tier and target fps, default from `device-tier-policy`), notifications, restore purchases, privacy policy and terms, manage consent, rate, contact, version. Hide destructive reset unless the GDD asks.
- The reference game ships only the first five rows (music and sound are on/off switches, not sliders). The legal and store rows (restore, privacy, terms, consent, rate, contact, version) are **studio additions** that stores expect; the restore row must call the real store restore. List: `app-services-bootstrap/references/absent-in-reference.md`.
Data: SketchEngine `DataSettings` (check the installed `Settings` module first: `SoundVolume`, `MusicVolume`, `Vibration`) or a project `Data_Settings` DataBlock; one binder applies values at boot (the `AfterSceneLoad` hook) and on change (`DataValue.OnValueChanged`): audio volumes and the haptics enable flag.
- A loading screen that mutes volume must not overwrite the persisted value (restore in `finally`, or keep the mute separate): a kill mid-load otherwise saves volume 0.

## Pause
`Pause_Popup` sets `Time.timeScale = 0`, pauses the SFX group (music ducks), buttons Resume / Settings / Home. Popup tweens must ignore time scale. Do not allow pause while a rewarded ad is showing. GDD says which screens pause and whether income timers stop.

## App pause/resume
`OnApplicationPause(true)` saves data and stores last-active UTC; on resume re-sync UTC-based timers and refresh subscription state. Studio addition for idle genres (the reference game has no offline earnings): stamp last-active UTC on pause, cap the offline hours, show a welcome-back popup claimed by tap; details in `recipe-retention-timers`. Device-clock timers are spoofable; decide if server time is needed. Lifecycle table: `app-services-bootstrap/references/lifecycle-hooks.md`.
