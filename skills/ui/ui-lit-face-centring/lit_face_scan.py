"""Lit-face scan of one glossy button in a screenshot.
usage: python lit_face_scan.py shot.png x_left_inside y_top y_bottom x_ink0 x_ink1
 - x_left_inside: a column just inside the left edge of the button face (above the rounded corner)
 - y_top / y_bottom: rows bracketing the button (a few px outside the outline)
 - x_ink0 / x_ink1: horizontal range containing the label / icon ink (inside the face)
Prints colour steps, lit centre, ink centre and the vertical error."""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); x = int(sys.argv[2]); y0, y1 = int(sys.argv[3]), int(sys.argv[4]); a, b = int(sys.argv[5]), int(sys.argv[6])
steps = []; prev = None
for y in range(y0, y1):
    p = im.getpixel((x, y))
    if prev is None or sum(abs(i - j) for i, j in zip(p, prev)) > 28: steps.append((y, p))
    prev = p
print('colour steps:', steps)
dark = lambda p: sum(p) < 150
lit_top = next((y for y, p in steps if not dark(p) and y > y0 + 1 and steps and True), None)
# lit top = first bright step after the first dark outline; band start = last big step before the final dark outline
outline_rows = [y for y, p in steps if dark(p)]
lit_top = next((y for y, p in steps if y > outline_rows[0] and not dark(p)), steps[0][0]) if outline_rows else steps[0][0]
band_start = [y for y, p in steps if y < outline_rows[-1]][-1] if outline_rows else steps[-1][0]
lit_c = (lit_top + band_start) / 2
white = lambda p: min(p) > 235
ys = [y for y in range(y0, y1) if any(white(im.getpixel((xx, y))) for xx in range(a, b, 2))]
ink_c = (min(ys) + max(ys)) / 2 if ys else float('nan')
print('lit top', lit_top, 'band start', band_start, 'lit centre', lit_c, '| ink rows', (min(ys), max(ys)) if ys else None, 'ink centre', ink_c, '| error', round(ink_c - lit_c, 1))
