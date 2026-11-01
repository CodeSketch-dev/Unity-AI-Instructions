---
name: game-feel-polish
description: "Juice for mobile games: reward fly-to-HUD, floating numbers, count-up, shake, hit-stop, haptics, rarity VFX, UI tweens. Use after the core loop works or when the game feels flat or dead."
---

# Game feel polish

Feel comes from immediate, proportional feedback to every meaningful event. Do it after the loop is playable and in a single pass per system, using pooled objects and the project's tween library.

## Feedback ladder (scale with importance)
| Event | Minimum | Better |
|---|---|---|
| Collect coin/item | pop SFX, small particle | item flies to the HUD counter, counter bumps and counts up |
| Damage/hit | flash + SFX | hit-stop 40-80 ms, small shake, floating number, knockback |
| Upgrade bought | button press anim + SFX | burst, stat counter animates old -> new, "level up" tag |
| Rare drop | color-coded text | camera focus, bigger FX by rarity, announcement banner |
| Zone entered | banner | banner + short shake/fx + music cue |
| Safe-zone/base entered | tint | full-screen flash vignette + shake (once, not repeated spam) |

## Rules of thumb
- **Proportional**: bigger consequence = bigger feedback. Frequent events must stay subtle; reserve spectacle for milestones.
- **Rarity-scaled FX**: color, size, particle count and sound escalate with rarity tier; the highest tiers get unique effects. Rainbow/special tiers must be readable (never black).
- **UI motion**: press scale 0.92-0.95 (0.08 s), popup scale-in 0.2-0.3 s ease-out-back, banners slide + fade, number count-up 0.4-0.8 s, subtle idle pulse on the one button you want pressed next (FTUE).
- **Camera**: shake amplitude small and decaying; hit-stop only on impact moments; never shake continuously.
- **Audio**: layer a short transient + a body; vary pitch +-5% to avoid repetition; limit simultaneous voices; separate SFX/BGM volume.
- **Haptics**: light tick on pickup, medium on hit/purchase, behind a settings toggle.
- **Do not annoy**: repeated celebratory FX for routine actions (e.g. every time a backpack item is carried back) quickly becomes noise. Trigger big FX only on first-time/meaningful transitions.
- **Reduce motion option** if the project has accessibility settings.

## Implementation
- Use the project's tween library (prefer one; do not mix) and pooling for particles, floating text and fly-to icons. Kill tweens on disable/destroy and return pooled objects.
- Fly-to-HUD: spawn in UI space at the converted world position, tween to the counter's RectTransform, bump the counter on arrival; batch 1-2 icons per burst, not one per unit.
- World text via the batched text system; no per-spawn string allocations in hot paths.
- Particle budgets for low-end Android: cap simultaneous systems, avoid large transparent overdraw, prefer sprite-sheet particles. Measure with `mobile-perf-audit`.

## Verify
Record or capture a short Play Mode sequence of the event and compare it with the reference clip at the same timing; confirm no leaked objects after 100 repeats and no Console errors.

Combat numbers (shake, punches, damage text, hit-stop proposal): `references/combat-feel.md`.

## Attention pulses stay subtle
- Looping attention pulses (reward/watch-ad/CTA buttons) scale at most +3% with >= 1 s per half cycle (sine in/out); stronger reads as nervous and annoying (user feedback). Clamp the limits inside the pulse component so serialized prefab values cannot exceed them, and measure min/max scale in Play (sample for ~5 s).

## Added from awesome-gamedev-agent-skills (2026-11-02)
Source: third-party example. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/game-feel.
- Shake from sampled noise times a decaying trauma value (amplitude = trauma squared), not a random offset per frame (buzzes like static). Shake the camera offset or a visual pivot, never the simulated transform.
- Hit-stop must wait in real time (WaitForSecondsRealtime or UniTask ignoring time scale) or it never resumes at timeScale 0; trigger once per impact and let only the newest call restore time scale.
- Ease almost everything; overshoot (back/elastic) for pops, ease-out for settle. Juice must return to rest; permanent exaggeration stops reading as feedback.
- Feedback must never block input: keep it short and let input buffer through it. Offer a reduce shake/flash option.
