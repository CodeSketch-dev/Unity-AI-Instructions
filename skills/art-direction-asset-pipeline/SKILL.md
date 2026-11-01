---
name: art-direction-asset-pipeline
description: "Art-direction pipeline for cohesive icons, UI, skyboxes and 3D props: style card, hero target, family batches, deterministic cleanup, in-engine check, provenance. Use when generating or sourcing a set of game art with Codex image tools or Blender."
triggers: art direction, style bible, style card, icon set, cohesive art, skybox set, ui kit art, asset manifest, hero asset, drift, codex image, imagegen, blender props, asset family, phong cach, bo icon, dong bo hinh, tao anh, tao icon
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

Related: `ui-always` (UI work gate), `blender-procedural-assets`, `vertex-color-baking`, `game-feel-polish`.
