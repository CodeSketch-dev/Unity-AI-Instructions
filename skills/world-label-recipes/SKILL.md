---
name: world-label-recipes
description: "World-space and HUD text rules: one rich-text label with rarity/size/time languages, distance size cap, TMP sprite icons, calm count-up readouts, invisible restyled text, banner backing. Use when building nameplates, egg/pet labels, money/speed pills."
---

# World label and readout recipes

- One rich-text label carries three visual languages: rarity = saturated per-letter colour + gem bullets; size/mutation = dark `<mark>` chip with lit/dim pips; time/value = small icon line coloured by speed. Never rarity and size in the same colour/weight.
- Check the font has the glyphs (parse its cmap): round bullets usually exist, stars/diamonds often not.
- Cache built strings per key (rarity|size|mutation); rebuild only concatenates. Build strings with pure helpers (unit-testable).
- Icons: `<sprite name=...>` glyphs from the default TMP sprite asset plus the number (no currency symbol).
- Size cap by camera distance: `scale = clamp(dist / refDist, min, 1)`; apply only on > 1 % change; one shared pure helper for all labels.
- Count-up readouts: duration 0.25-0.8 s by relative delta, ease-out, punch only on gains >= 2 % with cooldown, scale <= 1.05 once, reset to rest scale before each punch, format only when a quantised key changes, auto-size + ellipsis. A yo-yo is almost always a looped pulse, not the number tween.
- HUD text banners over world labels need a >= 0.8 alpha backing (floor it in code).
- Restyled imported TMP text invisible: check `textInfo.characterCount` in Play; replace with a fresh UGUI text and rebind the owner's serialized reference.
- Squash/pop tweens target a child wrapper at scale 1, never an object another script rescales; stop tweens on pool release.
- Occlusion fade: give targets `SuspendUntil(time)` and call it on reveal/landing moments; only settled objects fade.
- Text centring: Capline alignment plus the sprite face offset, never a per-label nudge (`ui-text-tmp` Optical centring).

- World-to-screen HUD stickers: ScreenPointToLocalPointInRectangle returns coordinates relative to the canvas CENTRE: anchor the sticker at (0.5,0.5) and clamp it to a play zone that excludes both HUD rails, the top row and the bottom bar, or it lands on top of buttons.

## Many labels at once: separate in screen space (pattern)
- When one action can raise several world bars/labels at the same time (area swing, multi-hit), each is placed per target and they stack on one spot. Add ONE pass after placement: per active label keep its screen footprint (px width, px height incl. name, px-per-metre, centre) and push each later label straight up along the camera up vector until it clears the earlier ones (skip when already clear or the gap is huge). Keep the pool small (cap) so the pass is O(n^2) over a handful.
- Verify with a Play capture during a multi-target hit, plus the existing label tests; do not hide labels to avoid overlap.

## Order of label position passes: exclusion lift BEFORE overlap resolve (bug class)
- Pipeline for overhead labels: (1) lift out of HUD/exclusion zones, (2) separate the lifted labels from each other, (3) final offset = lift + separation. Doing the lift after the separation drags a label that was already separated back onto its neighbour (two names overlapped above the player, persisted, not a transient).
- Diagnose by dumping per-label screen positions and the per-label nudge: a big nudge that is NOT from the overlap resolver points at a later pass (exclusion lift, clamp, smoothing) undoing the separation. An estimate constant (label width) is the wrong first suspect when the resolver is already running.
