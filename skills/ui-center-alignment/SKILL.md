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

## Always-on
- This skill applies in every project and to every UI task (new popups, edits, clones), referenced from `AGENTS.md`; the user should never have to ask for centring.
