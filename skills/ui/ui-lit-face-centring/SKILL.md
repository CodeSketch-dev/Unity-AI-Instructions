---
name: ui-lit-face-centring
description: "Centre text and icons on the LIT face of glossy buttons (top of the button to the start of the dark bottom shade band), measured by a pixel column scan of a Play screenshot. Use whenever a button, pill, plate or price row is aligned or looks low / high."
triggers: lit face, button centring, text looks low, dark band, highlight, shade band, glossy button, can giua nut, chu bi lech, nut co bong
---

# Lit-face centring (owner convention)

Glossy kit buttons are layered top to bottom: outline, highlight, body (light), **dark shade band**, outline. Centring on the rectangle OR on the "medium body" alone leaves the content looking low. The owner's rule: the content centre is the middle of **[top of the button .. start of the dark band]** (highlight included, dark band excluded).

## Measure, never assume (script)
1. Capture a 1920x1080 Play screenshot (ScreenCapture via script-execute) with the screen open.
2. Column scan just inside the left edge of the button: print rows where the colour jumps (> ~28 summed channel delta). Typical result: outline (dark) -> highlight (bright) -> body -> darker band -> outline. `lit_top` = first row after the dark outline, `band_start` = first row of the darker band; `lit_centre = (lit_top + band_start) / 2`.
3. Ink rows: white text pixels (min channel > 235) and icon pixels inside the face: `ink_centre = (min + max) / 2`. Horizontal: same with the green/blue face extent.
4. Pass = |ink_centre - lit_centre| <= 2 px (aim <= 1) on both axes. Report the numbers.

`lit_face_scan.py` in this folder does steps 2-4 for a button rectangle.

## Fixing it (shared code, never per-label nudges)
- The vertical offset belongs in ONE shared place (the icon + label row padding of the button content layout / the label margin helper). Per-family tweaks (3 px, 6 px "lifts") rot: calibrate them against the lit face with the scan, then remove compensations that the scan shows are wrong. In the reference project the bright families (lips 16/11) needed NO extra vertical padding once the old lifts were removed; the old lifts had made rows 2.5-6.5 px too low.
- After changing the shared rule, refresh existing prefabs' content layout WITHOUT rebuilding them (hand edits stay), re-measure one text-only button, one icon+text button and one price button.
- The ink audit script must use the same face definition (body extended up through the highlight), otherwise it reports false failures.

## Lock-style compact buttons (owner rule 2026-11-11)
A label stretched over a button sprite with a dark bottom band sits low if the bottom inset is only the lip. Measure from a screenshot: caps centre vs lit-face centre (top edge .. start of dark band); raise the label rect bottom by 2 x the dx in UI units (the rect centre moves half of it). Do not report a label aligned from rect maths alone.
