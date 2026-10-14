---
name: sfx-variation-ducking
description: Add pitch/clip variation, per-config cooldowns and music ducking to the audio system. Use when repeated sound effects feel robotic, stack up, or voice lines drown in music.
---

# SFX variation and ducking

A gap in the reference projects (report 09): none of them vary pitch or clip, or duck music. Extend the existing `AudioConfig` and `game-audio-system`; do not load clips ad hoc.

1. **Variation**: add a `Vector2 pitchRange` (e.g. 0.95-1.05) to the config or play call; optional clip array picked without repeating the last clip.
2. **Cooldown**: per-config minimum interval (and a max concurrent voices) so rapid events (coins, hits) do not stack.
3. **Ducking**: Voice/important bus lowers Music through a mixer snapshot transition (or sidechain) with short attack and longer release.
4. **Defaults** (soft): SFX volume 1, BGM 0.4-0.6; SFX decompress-on-load mono, BGM streaming (`import-presets`).
5. Keep the volume `DataValue`s bound to settings at boot (`boot-sequence-setup`); the framework API keeps the "Volumn" spelling.
Verify by ear in a Play Mode run via Unity MCP where available and say when it was not listened to.
