---
name: codex-ui-sprite-brief
description: "Use when asking Codex (or any image model) to generate UI sprites: the ready brief template with the binding quality rules (image_generation only, constant outline, rounded rect, corner-cap 9-slice, size cap, no clipping, name-colour match) and the acceptance loop with sprite_audit.py."
triggers: codex gen, gen art, generate sprite, image generation, brief codex, texture ui, button icon art, tao anh ui, gen texture
---
# Brief template (paste, fill the list)
```
# Task: GENERATE <names> with the image_generation tool (no resampling of any old PNG; if the tool is unavailable STOP)
Owned output: <folder>/ only. Report: <report path> (state which generation call made each image).
Reference (attached): the approved sprite = shape/colours/highlight to keep. KEEP the current bright style; only make it sharper and better shaped.
Rules: 1 exact rounded rectangle, radius ~30% of height (Knife Tower look), never pill/hexagon/diamond/chamfer; 2 ONE constant outline thickness all round, >= 7% of sprite height, same dark colour on all variants; 3 vector-smooth anti-aliased edges, no stair-steps/wobble/noise/blur; 4 9-slice friendly: all detail (gloss, lip curve, outline) inside the four corner caps, middle cross plain vertical gradient, gloss highlight small and inside the corner cap; 5 dark bottom lip follows the rounded shape; 6 canvas: flat magenta #FF00FF, 40 px margin, nothing cut at the edges, no magenta in the sprite; 7 size <= 512 px wide for buttons (boards larger only if needed); 8 verify each saved file's colour matches its name.
```
## Acceptance loop (director)
1. Run `ui-sprite-audit/sprite_audit.py` on every output; FAIL -> send back the failing lines with numbers (max 2 rounds), then rebuild the silhouette/outline analytically with `art-direction-asset-pipeline/ideal_rounded_button.py` (the model supplies fill/gloss only).
2. Derive variants (pressed x0.88, disabled desaturate), import through the project's kit manifest (per-sprite ppu + border), Play screenshot at real size, look at an 8x crop of a corner.
3. Update this skill when a new failure class appears.

## Traps (measured 2026-11-13)
- Model name: pass the exact slug from `~/.codex/models_cache.json` ("slug"); bare `luna` or an invented version returns 400 model_not_found on a ChatGPT account. Cheap art run: `-m <luna slug> -c model_reasoning_effort=low --disable hooks --disable codex_hooks`.
- Magenta cut: FLOOD-FILL from the canvas edges (distance to #FF00FF (255-r)+g+(255-b) < 70 clear, < 200 edge fade); never key the whole image: pink gems / purple plates sit at distance 60-110 and get holes (owner saw the background through a gem). Enclosed pockets (inside a ring): clear only regions >= 400 px under distance 30. Crop the bbox on alpha > 200. Check every cut on a contrasting background (blue) before import.
- Shop / pack card frames: follow `ui-shop-card-frame-gen` (owner-approved sunburst family).
