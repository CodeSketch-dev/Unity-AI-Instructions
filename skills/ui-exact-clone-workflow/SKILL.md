---
name: ui-exact-clone-workflow
description: "Clone a reference UI screen exactly: capture the reference, extract sprites and fonts, build prefabs, compare by pixels at several aspect ratios. Use when a screen must match a reference game or mockup."
triggers: ui clone, exact clone, reference screen, mockup, match reference, pixel compare, sprites, fonts, giong y chang
---

# Exact UI clone workflow
1. Capture the reference at 1920x1080 (and other aspects when available); list regions, sizes, margins.
2. Reuse real sprites/fonts (check `clone-ip-safety`); generate only what is missing in the same style.
3. Build with the project builder (`ui-builder`, `ui-clone`), then `ui-validator` and `ui-visual-qa` pixel diff.
4. Apply the UI gate (`ui-always`): centring, autofit, press anim.
5. Fix named regions and repeat with an iteration cap.

## NO-INVENTION LAW (owner 2026-11-12, repeated corrections; the reference is hand-written and is the standard)
- The reference project (Knife Tower Speed Keyboard) is 100% hand-coded by the owner: it is the standard for code style, structure AND UI. Read its prefab YAML/scripts directly (read-only), never from memory or screenshots.
- Before building a screen, list EVERY element of the KT counterpart (hierarchy, sprite GUIDs, font + material, sizes, positions, texts, colours, which buttons live on which screen, e.g. where the Shop/Skins button sits: Home vs HUD vs Settings) and reproduce exactly that list. Add nothing KT does not have (no extra rows, scroll views, own sliders/knobs/icons, own fonts or colours); remove what KT lacks. Where our game has no KT counterpart, list it as a question, do not invent.
- Every UI report ends with an element-by-element KT-vs-ours diff table (identical / difference + why) and a Play capture next to the KT reference. No table = REWORK.
- Entry points (Shop/Skins, Settings, Home, Ads buttons) are placed where KT places them; never move a feature into another popup to save work.

## Effective on-screen size check (lesson 2026-11-12: copied popup rendered at 22% of screen width instead of KT's 33%)
- A matching element list is not enough: compare EFFECTIVE size = sizeDelta x the full localScale chain (container, board, tween end scale) / canvas reference resolution, per aspect, against the reference. A reference board may be authored small and scaled (e.g. 528x435 at localScale 1.5); copying only the rect loses the scale.
- Assert it in a test (effective size within 2% of the reference) and look at a capture on a phone-like aspect; tap targets >= 48 dp.
- A global TMP material change (e.g. outline width) affects every label: re-capture the screens after it, not only the one that prompted it.
- Camera clones: compare the character's on-screen height fraction (KT ~0.32), not just FOV/distance; scaling the world without scaling the character changes the fraction, so re-derive distance from measured capture.
