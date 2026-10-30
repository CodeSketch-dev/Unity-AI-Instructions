---
name: ui-9slice-buttons
description: "How to cut sprite 9-slice borders (TextureImporter spriteBorder) for UI buttons, tabs and plates so Image Type=Sliced stretches with no notch, seam, dark line or broken outline at any size. Use when importing, restyling or fixing any button/tab/plate sprite, when a button shows artifacts at some size, or when a button sprite has zero borders. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# 9-slice buttons (cut borders from pixels, never by eye)

Symptom this prevents: a button looks fine at native size but at another size shows a dark notch, a step/dividing line, a broken or thinner outline, or a squashed highlight. Cause: a border that is too small, asymmetric, or zero, so detail lands in the stretched centre.

## Rules
1. **Borders must contain the whole non-flat art**: outline + corner radius + highlight (gloss ellipse, top rim light) + bottom shadow lip + any outer drop shadow. All of it lives inside the four fixed corner/edge areas.
2. **The stretched centre must be flat**: only a smooth gradient or solid colour. No step line, gloss shape, icon, text or detail may fall in the centre band. Text/icons baked into the sprite (for example a GET plate) cannot be sliced: border 0, use Simple, or re-export a clean plate.
3. **Symmetric L = R** for symmetric art. B is usually larger than T (bottom lip + shadow); never copy asymmetric guesses.
4. **Never border L+R >= width or B+T >= height.** Keep at least about 8 px of centre. Very large borders also make small sizes squash: Unity scales borders down when the Image is smaller than L+R / B+T.
5. **Every button/tab sprite used as Sliced has a border.** Zero border plus Sliced equals a stretched whole sprite (outline gets distorted).
6. **Keep GUID, pivot and PPU unchanged.** Only change spriteBorder (Sprite Editor or TextureImporter.spriteBorder + SaveAndReimport).
7. **Same art as Knife Tower (KT) = copy KT's spriteBorder** (read via the KT MCP, read-only). Equal art means equal borders; only re-cut when it is wrong or missing.

## Measure (script, not eyeballing)
- Read the PNG bytes (`Texture2D.LoadImage` on the file; the importer need not be Read/Write).
- Columns: find the longest run of adjacent columns that are identical (max channel diff <= 6 over all rows) -> `lo` = run start, `hi` = W-1-run end. L >= lo, R >= hi. Same for rows (Unity pixel y starts at the bottom): B >= lo, T >= hi.
- Pick border = measured value + 1-3 px safety, use the larger of the two for L and R, and confirm the centre band is gradient-only.
- Typical flat-style buttons (outline ~5 px, radius ~10-13 px, bottom lip ~22 px): L/R 12-18, B 24-30, T 14-22. Glossy plates with a light top half and a highlight ellipse need T about 55 and L/R about 37.

## Verify (mandatory, under the Unity lock if shared)
Render the sprite sliced at small (120x60), medium (220x70), wide (400x80) and tall (80x120) sizes (an offscreen CPU 9-slice into a Texture2D, or a temporary Canvas with Image Sliced, then screenshot; delete temp objects). Outline thickness must be uniform and corners smooth at every size, with no notch, seam or dark gap, as clean as a good round icon button. Fix the border and repeat until clean.

## Image settings
- Image Type = Sliced, Fill Center on, Preserve Aspect off.
- Keep `pixelsPerUnitMultiplier` as the prefab already has it (usually 1). Raising it shrinks the fixed corners, lowering it enlarges them; change it only when the corner looks too thick or thin at the target size, and then change it identically for all buttons of that style.
- Do not change prefabs just to fix borders: fix the sprite import, and all users improve at once.
- Report old -> new border per sprite.
