---
name: art-direction-asset-pipeline
description: "Art-direction pipeline for cohesive icons, UI, skyboxes and 3D props: style card, hero target, family batches, deterministic cleanup, in-engine check, provenance. Use when generating or sourcing a set of game art with Codex image tools or Blender."
triggers: art direction, style bible, style card, icon set, cohesive art, skybox set, ui kit art, asset manifest, hero asset, drift, codex image, imagegen, blender props, asset family, phong cach, bo icon, dong bo hinh, tao anh, tao icon, skybox, icons, generate icons, generate art, sprite sheet, tao skybox
---

# Art-direction asset pipeline

Source: third-party example. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/create-game-assets. Adapted to our Codex image + Blender + Unity flow.

Generated art is a draft until it passes technical checks and looks right inside the real game. The goal is one coherent family, not a pile of attractive one-offs.

## Workflow
1. **Inspect first.** Screenshot the real game at native resolution; list existing sprites, fonts, palettes, import settings. Keep a working direction unless told to redesign.
2. **Style card** (write once, reuse in every prompt): shape language, outline weight, palette roles (accent / reward / danger / neutral), light direction, detail density, material cues. Concrete properties only; never "beautiful" or an artist name.
3. **Technical frame:** target size and aspect, transparency, camera/view, texture budget, color space, atlas plan, platform (low-end Android).
4. **Manifest:** a table of every asset (id, state, size, pivot, source, status, licence). Mark greybox placeholders separately from production.
5. **One hero first.** Make one asset, judge it at game scale on a real background (thumbnail, working size, in context). Approve it, then batch.
6. **Family batches** (4-12 items): pass the approved hero as the reference, keep the invariant block identical, vary only the subject block. Change one variable per edit pass. If drift appears, go back to the hero; never edit a drifted copy.
7. **Normalize by script, not by eye:** crop, resize, pad, chroma-key or alpha-check, slice, name. Verify alpha is real (not a baked checkerboard) and sizes are exact.
8. **Import natively:** sprite mode, mipmaps off for UI, sRGB, compression, atlas membership; 3D: scale, pivot, normals, shared materials.
9. **Validate in context:** contact sheet over light and dark backgrounds, then the live game screenshot. Fix the source asset, not a runtime workaround.
10. **Record provenance** next to the manifest: tool, prompt card, edit history, licence.

## Prompt blocks
Five blocks, invariant first: PURPOSE, SUBJECT, VIEW, ART DIRECTION (from the style card), LOCKS (what must not change), EXCLUDE (text, frames, scenery, duplicates, cropped edges). Template and QA checks: `references/prompt-and-qa.md` (read when writing the first prompt of a batch).

## Choose the path
| Need | Path |
|---|---|
| Change an existing asset | Edit the original; state what stays fixed |
| Icon / UI family | Sheet on flat key color, cut by script, install through the project UI kit manifest |
| Skybox / panorama set | Same palette roles and horizon height across all; check seam and 2:1 ratio; preview in the real scene |
| 3D prop | Concept as reference, build in Blender with shared palette/material, check scale and pivot, bake or vertex-color per project rules |
| No generator available | Brief + manifest + licensed source; keep labeled greybox |

## Gates (all must pass)
- Cohesion: same outline, palette roles, light direction, density across the family.
- Read: silhouette and state clear at native size and in motion.
- Technical: exact size, real alpha, correct pivot, no clipped content, no stray text.
- Budget: texture memory and atlas count within the project budget.
- Rights: every shipped file has recorded provenance (see `clone-ip-safety` for clones).

## Pitfalls
- Beautiful alone, wrong as a set: compare against the hero side by side.
- Palette growth (near-duplicate colors): quantize to the style card palette.
- Trusting generated grids or transparency: always script-verify.
- Skipping the in-game screenshot.

## Iterating a studio avatar or store icon
- Treat the user's supplied icon as the style anchor; infer neither flat branding nor realism from the word "logo". Record whether they want an emblem, mascot or full game-art avatar before rendering.
- Keep a compact approved/rejected ledger. Edit the latest approved composition, lock its accepted parts, and change only the requested parts; stop obsolete generations instead of presenting them after a correction.
- Judge anatomy and hard-surface geometry at full size (hands, saddle contact, weapon head/shaft, perspective), then inspect 48/64 px previews. A detailed glow cannot repair a broken silhouette or impossible grip.
- Assign distinct hue/value roles to character, mount, emblem and background. Blur and simplify the stylized background; concentrate bloom/FX at focal edges without erasing geometry or the face.
- Research current popularity before claiming a character is trending. Public visibility is not evidence of advertising spend; label that uncertainty and keep character provenance in the asset manifest.

Related: `ui-always` (UI work gate), `blender-procedural-assets`, `vertex-color-baking`, `game-feel-polish`.

## Codex art regeneration traps (owner correction 2026-11-10)
- A brief that says "regenerate at 3x" lets Codex just Lanczos-upscale the old PNG (it did): stair-steps and blur stay. Brief MUST say "call the image_generation tool for every sprite, do not resample/sharpen the old file; if the tool is unavailable STOP", and the report must list the generating call per image. Check the report/log for `resize|Lanczos` before accepting.
- Raster output still has chroma-key magenta fringe and stair-step contours: post-process with a contour smoother (supersample 2x, gaussian sigma ~15 px on the alpha mask and on a dark-outline mask, smoothstep AA, inpaint fill colour under the outline, recompose) so outlines read as pen-tool curves; look at an 8x nearest crop of a corner, not the full sprite.
- Swapping a sprite for a higher-res one: scale `spritePixelsToUnits` by new_w/old_w (so sliced borders keep their canvas size), set `spriteBorder` to the corner caps only, and raise the Android override `maxTextureSize` (a 1024 override silently downsizes 1500+ px sprites = blur).
- Full-screen dim/cutout panels (tutorial focus) must be 10000 units, never 3500: wide foldable aspects (2658x960) expose gaps.
- Verify icon aliases (`ic_ad` was mapped to a calendar icon) by looking at the Play screenshot of every button using them.
- When the owner says "keep the current texture, just sharper": super-resolve the OLD sprite (upsample + contour smoothing), never ask the image model to redraw a new design. Keep the old hand-tuned `spriteBorder` x (new_w/old_w) (model-estimated borders were 40% too small and broke tile buttons), derive `_pressed` (x0.88) / `_disabled` (lerp to luma 0.7, x0.94) variants from the new base, and keep sprites <= 1024 px (build size).
- Owner rule: outline thickness must be IDENTICAL everywhere (5 px black = 5 px at every point, never 2 px thin spots). Rebuild it, do not trust the generated one: `uniform_outline.py` smooths the silhouette (supersample 2x, gaussian), computes the signed distance to the edge and redraws the outline as a constant-width band (width = dark area / perimeter), fill inpainted under it. Prove it by measuring: distance from every edge pixel to the nearest non-dark pixel, p90-p10 spread must be <= 1 px (generated art measured 2 px, rebuilt 1 px, min 15.8 of 16.8).

## Senior art review of Codex batches (do this before any import; owner 2026-11-10)
Grade every sprite REWORK unless all hold: (1) same design/aspect as the reference (a near-square tile must stay near-square; a generated wide pill is a fail); (2) outline present on ALL colours and one colour family (yellow/orange/red labels often come back with no dark outline); (3) outline thickness spread p90-p10 <= 1 px measured, not eyeballed; (4) shape = rectangle with moderate corners, no pill/hexagon; (5) <= 1024 px; (6) report names the image_generation call. Contact-sheet captions can be shifted by one: map by file name, never by position. Send REWORK back with the failing numbers and one sharper line per sprite; never import a partial batch over working art, and keep the previous sprite when in doubt (revert smoothing experiments that blur rims).
