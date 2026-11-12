"""Check (or solve) a grid inside a scroll board so cells never overflow the viewport.

Layout model (all numbers in the Canvas reference pixels):
  body width -> board (body minus board margins) -> ScrollRect (board minus insets) -> grid inner width (scroll minus left/right padding)
  grid width needed = columns * cell + (columns - 1) * spacing

Examples
  python -I grid_fit.py --body 1480 --list-share 0.64 --board-margin-left 22 --board-margin-right 12 \
      --inset-left 25 --inset-right 46 --pad-left 10 --pad-right 10 --columns 4 --spacing 32 --cell 180
  python -I grid_fit.py ... --columns 4 --spacing 32           # no --cell: prints the largest cell that fits
"""
import argparse


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--body", type=float, required=True, help="width of the area that holds the board and its neighbours")
    p.add_argument("--list-share", type=float, default=1.0, help="share of the body used by the board (0..1)")
    p.add_argument("--board-margin-left", type=float, default=22)
    p.add_argument("--board-margin-right", type=float, default=12)
    p.add_argument("--inset-left", type=float, default=25, help="ScrollRect inset from the board, left")
    p.add_argument("--inset-right", type=float, default=46, help="ScrollRect inset from the board, right (scrollbar band)")
    p.add_argument("--pad-left", type=float, default=10)
    p.add_argument("--pad-right", type=float, default=10)
    p.add_argument("--columns", type=int, required=True)
    p.add_argument("--spacing", type=float, required=True)
    p.add_argument("--cell", type=float, help="cell width to verify; omit to solve for the largest cell that fits")
    p.add_argument("--min-gap-ratio", type=float, default=0.15, help="spacing / cell below this feels cramped")
    a = p.parse_args()

    board = a.body * a.list_share - a.board_margin_left - a.board_margin_right
    scroll = board - a.inset_left - a.inset_right
    grid = scroll - a.pad_left - a.pad_right
    max_cell = (grid - (a.columns - 1) * a.spacing) / a.columns
    print(f"board {board:.0f}px -> scroll area {scroll:.0f}px -> grid inner {grid:.0f}px")
    print(f"largest cell that fits {a.columns} columns with spacing {a.spacing:g}: {max_cell:.1f}px")

    cell = a.cell if a.cell is not None else max_cell
    used = a.columns * cell + (a.columns - 1) * a.spacing
    slack = grid - used
    ratio = a.spacing / cell if cell else 0
    print(f"cell {cell:.1f}px uses {used:.0f}px, slack {slack:.1f}px, gap/cell = {ratio:.0%}")
    problems = []
    if slack < 0:
        problems.append("OVERFLOW: cells are wider than the grid area (they will be clipped or pushed over the frame)")
    if ratio < a.min_gap_ratio:
        problems.append(f"CRAMPED: gap is under {a.min_gap_ratio:.0%} of the cell (Knife Tower uses ~18-20%)")
    if min(a.inset_left, a.inset_right) < 20:
        problems.append("FULL-BOARD SCROLL: the ScrollRect must be inset >= 20px from its board on every side (Knife Tower: 25px)")
    if min(a.board_margin_left, a.board_margin_right) < 10:
        problems.append("BOARD TOO CLOSE: keep the board >= 10px from the frame / the neighbouring panel")
    for line in problems:
        print(line)
    print("OK" if not problems else "FIX THE LAYOUT BEFORE BUILDING")


if __name__ == "__main__":
    main()
