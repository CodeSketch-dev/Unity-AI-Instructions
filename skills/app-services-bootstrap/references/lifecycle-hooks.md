# App lifecycle hooks

| Hook | Owner | Effect |
|---|---|---|
| `OnApplicationPause(true)` | framework callback component -> every `DataBlock` | save all data blocks (NOT on focus loss: extra disk writes/ANR) |
| `OnApplicationPause(false)` | ads app-open manager | try an app-open ad |
| `OnApplicationPause(false)` | subscription refresher | re-read subscription state from the store |
| `OnApplicationFocus(true)` | input owner | clear stuck joystick/touch state |
| `OnApplicationFocus(true)` | local push module | cancel scheduled notifications |
| `OnApplicationQuit` | framework callback component | save; Unity calls it BEFORE `OnDestroy`, so write values to the `DataValue` before quit or the file keeps the old value |
| `Time.timeScale = 0` | pause facade | gameplay pause (add auto-pause on background if the genre needs it) |

Studio additions: stamp last-active UTC on pause (offline earnings), re-sync UTC timers on resume, `Screen.sleepTimeout = NeverSleep` during active play only if the genre needs it (the reference leaves the default).

Pitfall: a loading screen that mutes volumes through the saved settings must restore them in `finally`; a kill mid-load can leave the saved volume at 0. Keep the mute separate from the persisted value.
