---
name: night-lighting-mobile
description: "Readable, pretty night for mobile scenes: moonlit ambient and fog, sun kept above horizon at low intensity, fake glow lights, tier-gated fireflies, no extra realtime lights. Use when a day/night cycle looks too dark or flat."
---

# Night lighting for mobile

Companion to `mobile-urp-lighting-baseline`. Night fails because it is physically correct: sun below horizon, ambient near black, fog dark. Make it readable, not realistic.

## Recipe (no extra realtime lights or post passes)
1. **Ambient**: night ambient is a lifted cool blue (moonlit), not near-black; keep luminance at least ~35-45% of day. Fog colour moves to the same blue, not black, or distant objects vanish.
2. **Sun**: keep the directional light above the horizon (never negative elevation; pitch ~35-45 deg); at night lower intensity (~0.3-0.5 of day) and tint cool. Keeps shading and shadows alive for free.
3. **Contrast**: warm base/points of interest vs cool surroundings. Draw the eye with fakes:
   - additive glow quads or sprite halos at lamps, gates, spawn pads (unlit, billboard, shared material); or ONE stationary particle system filled once with SetParticles (huge lifetime) at night start and cleared at day: one draw call, zero per-frame cost, tier-gated;
   - emissive accents on shared materials (colour bumped, no new lights);
   - optional ground pools of light as decal quads.
4. **Fireflies**: one particle system, at most 40 particles, small, additive, slow drift; enable on Medium/High tier only (`device-tier-policy`), pooled, off by day.
5. **Transition**: lerp ambient, fog, sun colour and glow alpha together over seconds; no pop at the boundary. Sky/skybox must follow.
6. **Budget**: no added realtime lights, no new post-processing, no extra shadow cascades; glow quads count toward draw calls (batch by material).

## Verify
Screenshots day vs night at 3 aspect ratios from the same spots (`playmode-driver-recipes`): the player, interactables and HUD must stay readable at night. Compare render stats before/after (`profiling-evidence`); say plainly if not measured on low-end hardware.
