---
name: ui-row-layout-budget
description: "Use when a UI row of siblings (icon chips, frames, buttons) needs resizing or re-spacing, or one fix keeps breaking its neighbour: size it by a width budget and guard it with a gap test over every prefab of the family."
triggers: chip, reward row, khung dinh nhau, cach nhau, gap giua, sua cai nay hong cai kia, layout budget, overhang, spacing
---

# UI row layout budget

Why: in a row (gift icon | chip | chip | button) the numbers are coupled: chip width, gap, how far a frame overhangs its chip, label inset, free span. Tuning ONE constant by eye from a screenshot fixes that spot and breaks the next one (owner 2026-11-13: "fix this and that breaks"; six rounds on one reward row: tiny text, then frames touching, then a chip touching the icon).

## Steps
1. Write the budget first, in numbers: free span = left neighbour's right edge .. right neighbour's left edge (measure it from the prefab, not from memory). Row width = sum of chip widths + gaps + the overhang of every frame (a frame that overhangs its chip by N px eats N px per side). Row width must be <= free span minus 2 x the minimum margin.
2. Derive the constants from that budget in ONE place (the fixer tool). Never tweak a single constant alone: change chip width, gap and position together and re-check the budget.
3. Guard the INVARIANT, not the numbers: one EditMode test per row family that loads every prefab of the family and asserts each visible gap (neighbour -> chip frame -> chip frame -> neighbour, measured on the real frames with GetWorldCorners) is >= 10 px, plus label padding >= 8 px and a minimum readable font. Prove red-then-green: run it before the fix and watch it fail with the real number.
4. Sweep the whole family (every minigame/prefab that shares the row), not only the one the owner screenshotted; check each once in Play at the end with a screenshot.
5. Report numbers (gaps in px, free span, row width), not "looks fine".

## Exceptions
A one-off row with a single prefab and no siblings sharing the layout can skip step 4. Never skip step 3: it is what stops regressions.
