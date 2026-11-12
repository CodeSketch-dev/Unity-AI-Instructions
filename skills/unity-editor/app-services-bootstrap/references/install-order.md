# Install order and exit criteria

Order matters: later steps read state created by earlier ones. Each step ends with its exit criterion; do not continue on a red step.

1. **Packages and defines.** Framework (SketchEngine), UniTask, TMP, Localization, IAP, tween library, store review packages if used. Exit: compiles, Console clean.
2. **Scenes and persistent root.** Boot scene index 0, Home index 1, one playable scene. Persistent root prefab (EventSystem, HUD canvas, popup canvas with popup root, loading screen, internet popup, toast, pool, IAP, manager) placed in the boot scene and in every scene that can be opened alone. Exit: play boot -> Home -> scene -> Home, one root.
3. **Boot hook.** One `AfterSceneLoad` class: frame rate `min(refreshRate, 60)`, vSync 0, device policy, settings binding (`DataSettings` -> audio, haptics), debug init. Exit: a settings change applies live.
4. **Localization.** Facade `Get(key, args)`, fonts per locale, initial locale detection AFTER the localization init operation completes (otherwise "en" can be saved permanently). Format first, right-to-left fix second. Exit: restart keeps the language.
5. **Loading screen / scene facade.** Heavy loads show progress, light loads fade. Exit: repeated scene-flow test.
6. **Settings.** Toggles, language, home; add legal rows (privacy, terms, restore, rate, contact, version). Exit: all rows work offline except links.
7. **Remote config.** Class with local defaults, fetch once at startup, event when loaded. Exit: first launch offline plays correctly.
8. **Consent / ATT.** Runs before ads init; every outcome converges on one guarded init call. Exit: fresh-install flow on a device.
9. **Ads.** Placement enum, adapter, policy, facade, banner service, fake provider. Exit: [gate matrix](../../ads-layer-generic/references/ads-gate-matrix.md) test green.
10. **Internet gate.** See `internet-gate-popup`. Exit: airplane mode shows the popup, bypass works.
11. **Analytics facade.** Event taxonomy first. Exit: no direct SDK calls outside the facade.
12. **IAP.** Catalog, receiver (the only place that grants), ownership data keyed by base id, funnel logs, restore. Exit: sandbox purchase grants once.
13. **Rating.** See `rating-prompt-flow`.
14. **Daily reward, retention, offline earnings** (if idle). Exit: day-advance cheat in the Editor; clock-forward behaviour decided.
15. **Haptics and audio.** One enable flag; audio created lazily.
16. **Tutorial hooks and lifecycle.** Tutorial-done flag read by gated services; save on pause/quit.
17. **Optional modules** from [absent-in-reference](absent-in-reference.md).
18. **Verification pass** (SKILL.md done check), then record the status table.
