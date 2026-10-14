# Worked example: Skin Shop popup (1500 x 780 window, reference canvas 1920 x 1080)

Contents: Body split, Board numbers, Cell anatomy, Preview panel, Scrollbar, What the first (rejected) version did wrong.

## Body split (body = window minus header, about 1480 x 642)
| Part | Anchors / offsets |
|---|---|
| Board | left 0 .. 64 % of the body; margins: left 22, bottom 22, top 22, right 12 |
| Preview | 64 % .. 100 %; offsets: left 12, bottom 22, top 22, right 22 |
| Gap board <-> preview | 12 + 12 = 24 px |

## Board
- Board width 913 px -> ScrollRect inset 25 (left, top, bottom) and 46 (right, scrollbar band) -> scroll width 842 px -> grid inner 822 px with 10 px side padding.
- Grid: 4 columns, cell 180 x 236, spacing 32 x 38 (gap = 18 % of the cell), padding top 14, bottom 70.
- `grid_fit.py --body 1480 --list-share 0.64 --board-margin-left 22 --board-margin-right 12 --inset-left 25 --inset-right 46 --pad-left 10 --pad-right 10 --columns 4 --spacing 32 --cell 180` -> slack 6 px, gap 18 %, OK.

## Cell (180 x 236)
Name strip at the top (34 px text), portrait stretched 14 px from the sides with room for the name above and the plate below, dim overlay on locked items, selection outline over everything, state plate at the bottom (14 px margins, 60 px high, 34 px text).

## Preview panel (about 503 x 598)
Name 60 px at the top; black rounded stage stretched 26 px from the sides, 90 px below the top and 182 px above the bottom; portrait inside the stage with 16 px margin; hint line (34 px) above the action button; action button 400 x 96 with 22 px bottom margin.

## Scrollbar
Slim 14 px bar, anchored to the right edge of the ScrollRect and pushed 10 px outwards into the 46 px band (about 22 px from the board edge), length = list height - 90 px, track and handle sprites from the project art, handle stretched on the cross axis, auto-hide.

## What the rejected first version did
ScrollRect equal to the board (no inset) so the last row was clipped over the frame border; cell gap 14 px (7 % of the cell); scrollbar handle left at its default size so a large pale block hung over the list; preview portrait on the bright cyan panel and the hint text overlapping the portrait's feet.
