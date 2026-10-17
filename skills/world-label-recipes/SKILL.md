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
