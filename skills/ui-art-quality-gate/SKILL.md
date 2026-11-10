---
name: ui-art-quality-gate
description: Use when generating, replacing or reviewing UI sprites (buttons, boards, tags, icons) with an image model or script: strict art-director review checklist, measurable pass criteria, the pipeline that produced smooth uniform-outline 9-slice buttons, and the traps that cost hours.
triggers: ui art, button sprite, 9 slice, outline, texture quality, codex image gen, blurry button, rang cua, vien deu, bo goc, nut, texture ui, art director review
---
# UI art quality gate (owner-approved conclusions, 2026-11-10)

## Act as an extremely strict artist
Any visible flaw = redo, no "good enough". Review every batch like a senior: look at an 8x nearest crop of a corner AND the in-game screenshot at the real size, then fill the scorecard; one failed line = REWORK.

## Pass criteria (measure, do not eyeball)
1. Silhouette is an EXACT rounded rectangle (moderate radius ~30% of height, Knife-Tower-like). No pill, hexagon, diamond, wavy or slightly bulging edges: a bulging middle strip turns wavy after 9-slice stretching.
2. Outline: identical thickness on every side and curve, thick enough to read in game (>= ~7% of sprite height; owner asked "a bit thicker" twice), same colour on all colour variants. Distance from each edge pixel to the nearest fill pixel: p90-p10 <= 1 px.
3. Edges anti-aliased vector-smooth, no stair-steps, no magenta fringe.
4. 9-slice: cuts at the corner caps only (cap = outline + radius, <= 36% of the short side); the middle cross is a plain vertical gradient. Gloss highlights must sit inside the corner cap, otherwise they smear when the button stretches. The dark bottom lip follows the rounded shape (derive it from a saturation mask of the source, never a straight row cut: square lip corners look wrong).
5. Size: author at ~2x the on-screen size (e.g. 448 px wide for a ~220 unit button); a 600-1000 px sprite minified 3-5x aliases (no mipmaps) and the outline looks thin/jagged. Keep the build light: buttons <= 512 px, only big boards larger.
6. Style stays the project's bright, saturated, vivid look; only the shape quality changes. Content on big buttons (text, icon) is large; icons carry the same thick outline family.

## Pipeline that worked
- Codex: image_generation ONLY (never resample the old PNG); brief carries the rules block; one approved base (blue) is generated, then colours are derived by hue/saturation/value mapping from each colour's old sprite (histogram/rank mapping of two different lip proportions speckles; use HSV with a lip mask instead). Verify names by dominant colour (batches came back shuffled and cut at the edges).
- Rebuild the silhouette and outline analytically (rounded-rect SDF at 4x supersample, outline band of constant width, downsample): guarantees pen-tool smoothness and exact uniformity. Script template: art-direction-asset-pipeline/uniform_outline.py (+ ideal rounded-rect variant described there).
- Derive `_pressed` (rgb x0.88) and `_disabled` (lerp to luma 0.7, x0.94) from the final base; keep each file's own guid.

## Project traps
- A kit importer (AssetPostprocessor + manifest json) overwrites .meta PPU/border: edit the manifest (per-sprite `ppu`), force reimport, re-read the .meta and dump the live Sprite in Play.
- Corner size in canvas units = border_px / (ppu/100). Pick ppu so the cap is ~22 units; a cap larger than half the shortest button squeezes into pointed ends.
- Never ship a smoothing experiment that blurs rims (revert to the original); never import a partial/unverified batch over working art.

## Round 2 conclusions (owner 2026-11-10, same day)
- One family: EVERY plate sprite the game uses (rail/tile plates, toggles, tags, buttons) must come from the same pipeline; a leftover old sprite (here a rail plate with an opaque drop shadow and a different outline) next to new buttons reads as broken ("ngao"). After replacing a family, grep the code for the remaining plate names (RAIL_PLATE etc.) and rebuild those too (ideal_rounded_tile.py = near-square tile with soft shadow).
- Shadow like Knife Tower: small offset (~6% of height), tight blur (sigma ~1.3 px at 4x supersample), alpha ~0.3, dark navy (not tan/grey, not wide soft). Fill colours must not be over-blurred (sigma <= 1): over-soft blends read cheap; KT has crisp light band, crisp lip.
- Icons: outline = same navy as the plate outline, opaque, thick (pad ~6% of the icon size per side), baked or follow-scaled; a translucent 4 px outline reads thin.
- Icon + amount rows (reward cards, currency, price) are a HorizontalLayoutGroup (icon LayoutElement preferred size, text flexible 0, childAlignment MiddleCenter, outline child ignoreLayout); never hand-placed offsets.
- When a project test hard-codes ppu 200 / compares to a staging manifest, update the TEST to honour the per-sprite `ppu` override instead of reverting art; keep tests green.
- The studio must use these skills by itself: art request -> ui-art-quality-gate + codex-ui-sprite-brief + ui-sprite-audit; UI change -> ui-always. The owner should never have to say "use the skills".
