---
name: ambience-layers
description: "Per-zone ambience: crossfaded loops, safe vs danger music, budgeted 3D loops, random one-shots with cooldown, ducking, tier-gated particles, toggle obedience. Use when zones or biomes should feel alive after the audio system exists."
---

# Ambience layers

Builds on `game-audio-system` (channels, pools, config, provenance) and `sfx-variation-ducking`. Do not add a second audio manager.

1. **Zone profile asset** (config SO): bed loop, optional music pair (safe, danger), one-shot list with min/max interval, optional particle prefab. A zone-enter event selects the profile; the audio factory resolves clips.
2. **Crossfade** beds and music 0.5-0.6 s between zone profiles; ignore re-entry of the same profile; safe <-> danger music switches on the danger event, with a minimum hold to avoid chatter.
3. **3D loops** (sleeping/alert creatures, machines): spatial blend 1, short max distance, a global cap on simultaneous loops (e.g. 4-6) with nearest-wins; stop beyond range.
4. **Random one-shots**: timer with random interval and a per-clip cooldown, pitch variation, never stacked in the same frame, skipped during dense SFX.
5. **Ducking**: duck bed/music under big events (reveal, reward) and restore with the same fade; one owner of ducking state.
6. **Particles**: ambient particle prefab per zone, pooled, count-capped, enabled by device tier; stop emission, do not destroy, on zone exit.
7. **Settings**: obey music and sound toggles/volumes at all times, including after a load; muted means no playing source, not volume-0 loops burning CPU.
8. **Provenance**: record every clip's source and licence; mark placeholders in the config name and in the notes so they are replaced before release (`clone-ip-safety`).
