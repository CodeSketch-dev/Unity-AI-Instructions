---
name: ui-popup-from-demo
description: Build popups/HUD buttons that match demo screenshots 1:1 via an idempotent editor builder and screenshot compare loop, generating only missing icons. Use when given demo images or "match the demo exactly".
---

# UI popup from demo

Extends `ui-clone` and `reference-port` with a repeatable build/compare loop.

## Loop
1. Open every demo image (`spec-pdf-extract`). Write the element list: window frame, header colour + icon + title, close X, columns, rows/cells and their states, big value text, glow, buttons (AD tag, label, badge), helper text.
2. Find art in this order: project atlases -> reference project atlases (copy the whole atlas with its `.meta` GUID) -> older art folders (lock, check) -> generate. Generate only when nothing exists, in the same style: thick dark outline, gold gradient fill, saved as a sprite under the generated-UI folder by the builder (a procedural polygon + signed-distance outline works for bolt/star shapes).
3. Write an editor builder as a `partial` of the project UI builder so it reuses its helpers (window, outlined text, buttons, scroll helpers). Rules: idempotent, saves prefabs + wires serialized refs + creates the factory asset; fix the builder, never hand-edit the output.
4. Dynamic content comes from config: instantiate row/cell prefabs from the array length.
5. Run the builder, enter Play Mode, open each popup through a script (with the countdown stretched so the screenshot catches the first state), screenshot the Game view, compare with the demo element by element, list the deltas, fix, rebuild. Crop-zoom small details before judging them (downscaled screenshots hide rings and badges).

## Style rules learned
- The demo has an AD tag icon on every ad button, a countdown badge, text centred inside the button (shift right only to clear the tag), outlined white labels, a dark navy body and a coloured header strip.
- The ad icon pokes slightly OUTSIDE the button edge (user rule), never over the button icon/label; see `ui-style-rules`.
- Lock/check/play markers are right-aligned with equal margins; shrink labels (auto size) so a long label never touches a marker.
- A gray secondary button = the pack neutral frame sprite, not a tinted blue.
- HUD additions must not cover existing widgets (currency, speed slider): place, screenshot, adjust.

## Done
Screenshots match the demo at the same size; AD tags, badges and helper text present; no missing sprites; Console clean; re-running the builder gives the same result.

## Reading a reference prefab without Unity
`python -I dump_prefab.py <reference.prefab> <guid-cache.json>` prints the RectTransform tree (anchors, sizes, sprite names, scripts) of a reference prefab. Port the hierarchy and numbers of rows/cells from it instead of guessing. Also see `ui-style-rules` for the standing visual rules.
