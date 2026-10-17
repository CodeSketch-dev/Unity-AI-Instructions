---
name: pooled-ranked-fx
description: "Per-object quality/rarity effects and cues on many world objects without a particle system each: register sources, one manager ranks at 5 Hz, lends pooled views to the top N for the device tier. Use for auras, glows, best-pick markers on large populations."
---

# Ranked, capped, pooled per-object FX

- Objects only REGISTER as lightweight sources (position, rarity, flags). No per-object particle system or light.
- One manager ticks at ~5 Hz: rank by rarity desc, distance asc, in view, max distance; incumbent bonus (hysteresis) stops flicker at the cut-off.
- Lend the top `Cap(deviceTier)` a pooled view; far entries get a single glow quad (LOD); only the few active views move per frame.
- Keep ranking, caps and night/day maths in one pure static class; unit-test ordering, cap per tier, hysteresis.
- Initial state is "off" so the first Evaluate really applies it.
- Best-pick cue (no arrow object): at 5 Hz rewrite the existing label of the single best candidate (ribbon, 1.1x scale, small bob). Gate it off while carrying, chased, or when a tutorial step already points somewhere. Pure comparer: value wins, tie goes to nearest.
- Per-object caps for materials: precompute plain/overlaid material arrays per entry, swap arrays for the nearest N (distance-ranked, sticky bias ~0.9).
