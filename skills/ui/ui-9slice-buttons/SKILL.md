---
name: ui-9slice-buttons
description: "Cut sprite 9-slice borders (spriteBorder) for buttons, tabs and plates so Sliced images stretch with no notch, seam or broken outline. Use when importing or restyling a button sprite, or one shows artifacts at some size. Part of the ui-always set."
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

## Adding sprites to a registry-backed kit (trap)
- Add new art under NEW keys first (never overwrite a live key until a pilot popup is reviewed). Names with a sliced-family prefix (board_, card_, ribbon_, btn_...) need a non-zero border; ribbons with folded tails must not be sliced, so give them a non-sliced prefix (title_, badge_, fx_).
- A sprite-factory/registry rebuild menu only shows new keys after `AssetDatabase.SaveAssets()` plus a script reload; until then kit audits report "failed to load". Check the factory with a one-line probe before running tests.
- Source art authored at 1x must be upscaled to the kit's pixels-per-unit convention before measuring borders; scan only the header band reliably, derive other borders from corner radius and verify in the sprite preview.

## Shape rule + squeeze trap (owner 2026-11-10)
Buttons are rectangles/squares with smooth moderate corner radius (~20-25% of height); never pill, hexagon, octagon or diamond. If a sliced Image is shorter than 2 x the vertical border in canvas units (border_px / (spritePPU/100)), Unity squeezes the corner caps vertically and the ends turn pointed (hexagon look). Fix at the sprite: small corner radius, border = corner cap only, PPU high enough that the cap in canvas units <= half the shortest button height.
