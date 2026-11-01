# Prompt blocks and raster QA

Source: third-party example (ideas), rewritten. Inspired by: gamedev-skills/awesome-gamedev-agent-skills skills/disciplines/create-game-assets/references.

## Prompt card template
```
PURPOSE:  production asset for <gameplay role>
SUBJECT:  <object, pose/state>
VIEW:     <orthographic | three-quarter | top-down>, facing <dir>
STYLE:    <paste style card: shape, outline, palette roles, light, density>
OUTPUT:   <WxH or sheet NxM>, flat key color background, no ground shadow
LOCKS:    keep proportions, outline weight, palette of the hero
EXCLUDE:  text, labels, frames, scenery, duplicates, cropped edges, signatures
```
For edits state both what changes and what stays.

## Drift signals
Outline width changes; highlights imply another light; head/body ratio shifts; palette gains near-duplicates; texture noise grows with later batches; camera angle changes in an isometric set; icon fill styles mix (flat vs bevel vs painterly).

## Script checks for every batch
- Exact dimensions and aspect; RGBA with real transparent pixels (reject all-opaque).
- Color count vs palette; edge halo from chroma key (erode 1 px).
- Contact sheet at 100% and 50% over light and dark checkerboards.
- Tileables: 3x3 repeat, seam check.
- File naming per manifest; no spaces.

## Three viewing distances
Thumbnail (native game size), working size (edges, seams), in context (real gameplay capture with UI and effects). An asset that only works zoomed in is not game art.

## Acceptance
Native-scale look in the live game, then contact sheet, then pixel checks. A prompt result alone is never "approved".
