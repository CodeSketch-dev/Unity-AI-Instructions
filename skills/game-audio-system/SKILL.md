---
name: game-audio-system
description: "Mobile audio layer: BGM crossfade, pooled SFX, config assets, factory, event-driven sounds, volume channels, provenance. Use when the game lacks sound, adding BGM/SFX, or audio causes memory/perf issues."
---

# Game audio system

Audio is a large share of perceived polish and a classic source of mobile memory spikes. Build it on the project's installed audio framework instead of a new manager.

## Design
1. **Inspect the installed audio stack** (pooled manager, config asset type, mixer factory, volume settings). Reuse it; do not port a reference project's older audio framework (parallel stacks double the bugs). Note API differences between the framework versions (see the house style notes) and translate deliberately.
2. **Inventory sounds by domain and event**: UI click; economy (purchase, upgrade, collect, sell); core loop (hit, break, hatch/open, reveal by rarity, pick up, place, deposit); character (jump, footsteps, impact reactions); danger (detect, warning, chase loop); zone/ambience; BGM tracks. Transfer only sounds that match features that exist.
3. **Config assets** per sound/group in the audio config folder; a **registry/factory** exposes read-only references and small helpers (`PlayPurchased`, `PlayUpgrade`); null clips are handled safely.
4. **BGM helper**: current + default/fallback track, crossfade with cancellation, ignore replays of the same track, loop or random-continuous playback, restore default, apply the user's music volume (crossfade must not bypass it), reset static state on subsystem registration for domain-reload-off sessions. A kick-off component on the always-loaded singleton prefab starts BGM.
5. **Gameplay listeners**: one focused component subscribes to existing domain events (symmetrical unsubscribe) and plays sounds; avoid scattering `Play` calls in unrelated logic. Success sounds only on successful outcomes (not on rejected purchases, full-slot deposits, zero-value collections).
6. **Mix**: Music and Sound channels are independent; muting one never mutes the other; per-category volume offsets in config; vary pitch +-5% for frequently repeated sounds.
7. **Mobile budgets**: long BGM uses streaming load type; short SFX decompress-on-load or compressed-in-memory per length; bounded concurrency and cooldown for high-frequency sounds (auto-hit, footsteps, repeated UI presses); never instantiate/destroy audio sources in gameplay loops.
8. **Importer settings** applied by an idempotent editor installer (`editor-tool-authoring`) so reruns are safe: load type, compression, force-mono for 3D sfx, preload.
9. **Provenance**: for reference-derived or external sounds, keep original `.meta`/GUIDs (`asset-transfer-closure`) and log source + licence in `Assets/_Game/Audios/THIRD_PARTY_NOTICES.md` (`clone-ip-safety`). External/generated additions need a clear reusable commercial licence; no ambiguous rips.
10. **Gap audit** after the first pass: play the loop with sound on and note silent moments (zone entry, reward, danger, UI popups, purchases).

## Verify
EditMode tests for the helper logic (same-track ignore, fallback, channel scaling, cooldowns, null-safety); Play Mode from the real entry flow: BGM starts, crossfades, respects mute/volume, key SFX trigger once per event, no Console errors, memory/active-source count bounded after 2 minutes of rapid actions.
