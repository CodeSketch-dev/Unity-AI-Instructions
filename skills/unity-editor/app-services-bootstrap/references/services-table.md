# Services table

Legend. Tag: R = Reference (shipped by the reference game), A = Studio addition (not in the reference), O = Optional module. Location: G = child of the persistent root prefab, St = static class initialized by the boot hook, P = popup prefab spawned by the popup manager from a prefab factory. "Order" = step in [install-order](install-order.md).

| Service | Tag | Location | Order | SketchEngine piece to check first | Leaf skill | Exit criterion |
|---|---|---|---|---|---|---|
| Save (atomic, warmup) | R | St | 1 | `DataBlock`, `DataValue`, data warmup | data-persistence-facts, save-and-crash-safety | old save loads; kill during write keeps a valid file |
| Persistent root prefab | R | G itself | 2 | `MonoSingleton` | persistent-root-prefab | one root + one EventSystem after boot -> Home -> minigame -> Home |
| Popup manager + popup root | R | G | 2 | `Popup` module | ui-popup-anatomy | popup opens from any scene, destroyed on close |
| Toast / warning banner | R | G | 2 | notification text component | ui-feedback-toasts | one toast class, localized text only |
| Boot hook (fps, device policy, settings bind, debug) | R | St | 3 | `FpsUnlock`, `DataSettings` | boot-sequence-setup, device-tier-policy | frame rate set once (min(refresh,60)), vSync 0 |
| Debug / cheat menu | R | St + P | 3 | `Modules/Debug` | debug-cheats-menu | stripped or gated in release builds |
| Localization + fonts | R | St | 4 | Unity Localization + facade | localization-pipeline | switch language, restart, still set; no raw UPPER_KEY on screen |
| Loading screen / scene flow | R | G | 5 | game layer | scene-flow-loading | all scene loads go through one facade; repeated flow test passes |
| Settings (music, sound, vibration, language, home) | R | P | 6 | `DataSettings`, `Setting*Button` | settings-pause-offline | change, restart, value kept |
| Settings legal rows (privacy, terms, restore, rate, contact, version) | A | P | 6 | - | settings-pause-offline | each row works; restore calls the real store restore |
| Remote config + local defaults | R | St | 7 | studio SDK / Firebase | [remote-config-priority](remote-config-priority.md) | game correct offline on first launch |
| Consent (UMP) / ATT | R | St | 8 | - | ads-layer-generic | one `StartAdsInit(reason)`; init runs even if consent fails |
| Ads facade + gates | R | St | 9 | - | ads-layer-generic, ads-popup-flow | every placement has call site, fallback, log; gate matrix test green |
| Banner service | R | St | 9 | - | ads-popup-flow | banner shown at scene start / home return / after native closes |
| Native ads slot | O | G | 9 | - | native-ad-beside-popup | device test only (Editor uses a mock) |
| Internet gate + popup | R | G | 10 | `SketchEngine.Internet` | internet-gate-popup | airplane-mode test, Try Again, bypass for ads-removed/VIP |
| Analytics facade | R | St | 11 | - | analytics-events-taxonomy | one `LogHelper`; no direct SDK call outside it |
| IAP + catalog + restore | R (restore partly) | G | 12 | Unity IAP | iap-catalog, unity-iap-port | buy grants once; restore re-grants non-consumables |
| Subscription / VIP | O | G | 12 | - | iap-catalog | refresh on resume; expiry handled |
| Rating prompt | R | P | 13 | `SketchEngine.AppStore` | rating-prompt-flow | fires once per eligibility, never in the tutorial |
| Daily reward / retention | R | P | 14 | - | recipe-daily-login, recipe-retention-timers | states Claimed/Today/Missed/Locked |
| Offline earnings (idle genres) | A | P | 14 | - | recipe-retention-timers | welcome-back popup, capped, claim by tap |
| Haptics | R | St | 15 | `Taptic` module | game-feel-polish | one enable flag bound to `DataSettings.Vibration` |
| Audio / BGM | R | St (lazy) | 15 | `AudioManager` | game-audio-system | no AudioListener/source in the root |
| Tutorial-done flag read by monetization | R | data | 16 | - | tutorial-phase-system | rating, native, IAP entry wait for the flag |
| Lifecycle hooks (pause/focus/quit) | R | mixed | 16 | `MonoCallback` | [lifecycle-hooks](lifecycle-hooks.md) | save on pause; resume refreshes subscription and timers |
| Force update / min version | O | P | 17 | - | [absent-in-reference](absent-in-reference.md) | blocks below min version; fail-open without config |
| Crash / error reporting | O | St | 17 | `SketchEngine.Diagnostics` | [absent-in-reference](absent-in-reference.md) | a forced exception shows in the dashboard |
| Local push | O | G | 17 | `SketchEngine.Notification` | [absent-in-reference](absent-in-reference.md) | scheduled on pause, cancelled on focus |
| Cloud save / server time / share | O | - | 17 | - | [absent-in-reference](absent-in-reference.md) | decided per genre |
