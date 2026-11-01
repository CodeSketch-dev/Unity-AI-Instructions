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
