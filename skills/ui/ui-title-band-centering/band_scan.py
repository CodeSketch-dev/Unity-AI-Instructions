"""Find the header band of a popup from a screenshot by colour change.
Usage: python band_scan.py shot.png X [Ymax]
X = a pixel column that crosses only the board (no text/icons), e.g. between title and close button.
Prints the band top, face bottom, lip bottom and the face centre (top-origin y). Centre the title ink on it.
"""
import sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
x = int(sys.argv[2])
ymax = int(sys.argv[3]) if len(sys.argv) > 3 else 400
rows = [im.getpixel((x, y)) for y in range(ymax)]

def d(a, b):
    return sum(abs(p - q) for p, q in zip(a, b))

edges = [y for y in range(1, ymax) if d(rows[y], rows[y - 1]) > 90]
print("colour edges (y):", edges)
# band top = first edge into a saturated colour; body start = first edge into a light cream (all channels > 220)
top = next((y for y in edges if max(rows[y]) - min(rows[y]) > 120), None)
body = next((y for y in edges if min(rows[y]) > 220 and (top is None or y > top)), None)
lip = next((y for y in edges if top is not None and y > top + 40 and rows[y][2] > rows[y][1] + 40 and rows[y][1] < 140), None)
face_bottom = lip if lip else body
print("band top", top, "face bottom", face_bottom, "body start", body)
if top is not None and face_bottom is not None:
    print("FACE CENTRE y =", (top + face_bottom) / 2, "(top-origin; screen y bottom-origin = 1080 - this)")
