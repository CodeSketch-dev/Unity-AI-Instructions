---
name: ui-center-alignment
description: "Mandatory centring audit for any Unity UI work (bars, pills, buttons, icon+text, currency bars, popups, tabs). Use whenever you build or edit UI; verify by script that content is geometrically centred before finishing. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# UI centre alignment (always)

Read this for every UI task. A UI is not done until it is measured as centred, not only "looks fine".

## Rules
- Centre means the **visible content group** (icon + label + side buttons) is centred in its container on both axes. Compare the content's bounding-box centre to the container centre; tolerance <= 1 px.
- Do not centre one child and leave siblings offset. Overhanging art (icon sticking out of a plate, a "+" on the edge) counts toward the content bounds; the label centres in the free gap between its neighbours, or the whole group centres in the plate.
- Prefer layout groups (HorizontalLayoutGroup/VerticalLayoutGroup, MiddleCenter, control child size) over hand-typed offsets. Use anchors at 0.5/0.5 or stretch + symmetric insets; avoid asymmetric `sizeDelta`/`anchoredPosition` fudge (e.g. y = -8).
- Text: vertical centre uses `Midline` alignment with y offset 0. If the font baseline looks low, fix once in the shared text factory, never per prefab.
- Icon, label and buttons on the same row share the same y centre (0 relative to the row) and a consistent height.
- Parent placement: a bar inside a header/title strip has y = 0 against the strip centre (anchor 0.5 vertically), not a magic offset.
- Applies to prefab instances too: fix the source prefab, then check each popup instance for overrides.

## Verification (script, mandatory)
1. For each rect in the changed UI compute world-corner bounds of its children (`GetWorldCorners`); print container centre vs content centre (dx, dy).
2. Fail if |dx| or |dy| > 1 px, or if siblings on one row differ in y centre.
3. Screenshot the Game View (landscape) and eyeball it once after the numbers pass.
4. Record any non-obvious fix in `docs/skill-candidates.md`.

## Widget vs parent (header strips, plates, rows)
- A widget placed in a parent strip (e.g. a currency bar in a popup Title, a tab in a tab row) must be centred on the parent's visible art, not only on its rect: use anchor 0.5 on the cross axis with offset 0, then compare against the parent's rect AND the strip sprite/background bounds; if they differ, align to the visible art.
- Siblings in the same strip (back button, title, currency bar) share one y centre.
- Make this a reusable check in any project: when you add or move a child into a parent, run the bounds comparison before reporting done.

## Neighbour-relative centring (text next to icons / buttons) - the rule that was repeatedly missed
- A label is centred in the FREE GAP between its visible neighbours, never in the parent frame: gap = [rightEdge(left neighbour: icon/badge) + pad, leftEdge(right neighbour: "+" button, arrow, price icon) - pad]. If a side has no neighbour, that side is the parent frame's inner edge. Centre the rendered text (`textBounds`), not the RectTransform, in that gap.
- Cross axis: icon, label and buttons on a row share one y centre; in a stack they share left/right/top/bottom alignment (align every edge the design implies, never eyeball). Currency bars: icon left, "+" right, number centred in the gap between them.
- No overlap ever: text bounds must not intersect any sibling graphic's bounds (icons, badges, shadows, "+" buttons); keep >= 6 px clearance.
- Not too small: autosize may shrink text only to ~45% of the row height (never below a readable min such as 14 px at 1080p); if it still does not fit, widen the container or shorten the string instead of shrinking more. Report the resulting font size.
- Script (run on every bar/pill/button changed): per text collect sibling graphics' world rects (`GetWorldCorners`, active, alpha > 0.05, not a full-size background), compute gapMin/gapMax as above, print `dx = textBounds.center.x - (gapMin+gapMax)/2`, `dy = textBounds.center.y - row.center.y`, overlap yes/no, fontSize. Fail if |dx| or |dy| > 1 px, overlap, or font below the min.
- Fix in the layout, not per label: icon + label + button as a HorizontalLayoutGroup (label flexibleWidth 1, centred) so the gap logic holds for any value width.

## Containment and padding (never touch or cross the border)
- Every child (icon, text, badge, image, button) sits INSIDE its frame/button/plate with padding on all 4 sides (at least ~6 px at 1080p, more on big frames, equal left/right and equal top/bottom unless the art needs an optical correction). Text and icons never overflow or touch a button/frame edge; decorative overhang (a ribbon, a "NEW" tag) is the only exception and must be deliberate.
- ScrollRect/viewport/grid areas are never 100% of the board: leave a margin on all 4 sides inside the board art (about 3-5% of the board size, minimum 12 px) so cards and scrollbars do not hug the frame; list/grid content gets the same inner padding (layout group padding) so the first/last item is not glued to the edge.
- Measure it: for each child compute `padLeft/padRight/padTop/padBottom` against the frame's inner rect (`GetWorldCorners`), fail if any is below the minimum or left/right (top/bottom) differ by more than 1 px; for every ScrollRect compare its rect to the board rect. Fix in the layout (insets, layout group padding), not per label, then re-measure.

## Auto-fix loop (no asking, no waiting)
- Whenever ANY screenshot, Play capture, test dump or review shows text off-centre, overlapping an icon, clipped, too small, or edges not aligned: stop, load `ui-always` + this skill, fix the layout, re-measure, re-capture; repeat until the numbers pass. Do this even when the task was something else (QA, shop logic, balance). Never just list it as a finding for the user, unless the fix needs a design decision.

## Always-on
- This skill applies in every project and to every UI task (new popups, edits, clones), referenced from `AGENTS.md`; the user should never have to ask for centring.
