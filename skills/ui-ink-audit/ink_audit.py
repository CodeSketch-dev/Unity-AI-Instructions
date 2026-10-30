"""Pixel audit of UI text/icon layout from a Play screenshot + Qa_InkDump json (skill ui-ink-audit).
Usage: python ink_audit.py shot.png dump.json [--tol 2]
Per icon+label button : HLG present, ink pair centre vs button MEDIUM-face centre (dx, dy; outline, light and shadow bands excluded),
                        ink leaving the face, overlap with other buttons.
Per title             : title ink centre vs header colour-band centre (colour edges in a probe column).
Prints FAIL lines with the correction in canvas units (px / scale); exit code 1 if any FAIL.
"""
import json
import sys
from PIL import Image

args = sys.argv[1:]
tol = 2.0
if "--tol" in args:
    i = args.index("--tol"); tol = float(args[i + 1]); del args[i:i + 2]
im = Image.open(args[0]).convert("RGB")
data = json.load(open(args[1]))
W, H = im.size
px = im.load()


def dist(a, b):
    return sum(abs(p - q) for p, q in zip(a, b))


def cx_(x): return max(0, min(W - 1, int(x)))
def cy_(y): return max(0, min(H - 1, int(y)))


def q(p): return tuple(v // 12 * 12 for v in p)


def face_box(r):
    """MEDIUM face = most common colour of the central area. Extent: vertical run in a column just inside the left edge, horizontal run in a row
    just below the top of the face. Outline (dark), light highlight and shadow lip differ in colour, so they are never part of the run."""
    x0, y0, x1, y1 = r
    counts = {}
    for yy in range(cy_(y0 + (y1 - y0) * .2), cy_(y0 + (y1 - y0) * .8), 3):
        for xx in range(cx_(x0 + 6), cx_(x1 - 6), 3):
            c = q(px[xx, yy]); counts[c] = counts.get(c, 0) + 1
    if not counts: return None
    face = max(counts, key=counts.get)

    def isface(p): return dist(q(p), face) <= 40
    col = cx_(x0 + 8)
    ys = [y for y in range(cy_(y0 - 6), cy_(y1 + 6)) if isface(px[col, y])]
    if not ys: return None
    row = cy_(ys[0] + 5)
    xs = [x for x in range(cx_(x0 - 6), cx_(x1 + 6)) if isface(px[x, row])]
    if not xs: return None
    return xs[0], ys[0], xs[-1], ys[-1], face


def ink_bbox(parts, face):
    """White text fill (min channel > 235) + the VISIBLE pixels of each icon (colour differs from the face; transparent sprite margins ignored)."""
    boxes = []
    for p in (p for p in parts if p["type"] == "icon"):
        x0, y0, x1, y1 = p["rect"]
        xs, ys = [], []
        for yy in range(cy_(y0), cy_(y1)):
            for xx in range(cx_(x0), cx_(x1)):
                if dist(q(px[xx, yy]), face) > 80 and sum(px[xx, yy]) > 120: xs.append(xx); ys.append(yy)
        if xs: boxes.append([min(xs), min(ys), max(xs), max(ys)])
    for p in (p for p in parts if p["type"] == "text"):
        x0, y0, x1, y1 = p["rect"]
        xs, ys = [], []
        for yy in range(cy_(y0 - 2), cy_(y1 + 2)):
            for xx in range(cx_(x0 - 2), cx_(x1 + 2)):
                if min(px[xx, yy]) > 235: xs.append(xx); ys.append(yy)
        if xs: boxes.append([min(xs), min(ys), max(xs), max(ys)])
    if not boxes: return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


fails, oks = [], []
buttons = [i for i in data["items"] if i["kind"] == "button"]
for it in buttons:
    parts = it["parts"]
    has_icon = any(p["type"] == "icon" for p in parts); has_text = any(p["type"] == "text" for p in parts)
    if not (has_text or has_icon): continue
    sc = it["scale"] or 1.0
    tag = it["path"]
    if has_icon and has_text and not it["hlg"]:
        fails.append(f"{tag}: icon + label without a HorizontalLayoutGroup -> wrap in ONE HLG (icon first, label Capline)")
    fb = face_box(it["rect"])
    if not fb: continue
    box, face = fb[:4], fb[4]
    ink = ink_bbox(parts, face)
    if not ink: continue
    dx = (ink[0] + ink[2]) / 2 - (box[0] + box[2]) / 2
    dy = (ink[1] + ink[3]) / 2 - (box[1] + box[3]) / 2
    msg = f"{tag}: pair centre vs medium face dx={dx:+.1f} dy={dy:+.1f}px"
    if abs(dx) > tol or abs(dy) > tol:
        fix = []
        if abs(dy) > tol: fix.append(f"HLG padding {'bottom' if dy > 0 else 'top'} +{abs(dy) * 2 / sc:.1f} units")
        if abs(dx) > tol: fix.append(f"HLG padding {'right' if dx > 0 else 'left'} +{abs(dx) * 2 / sc:.1f} units")
        fails.append(msg + " -> " + "; ".join(fix))
    else:
        oks.append(msg)
    if ink[0] < box[0] + 2 or ink[2] > box[2] - 2 or ink[1] < box[1] + 1 or ink[3] > box[3] - 1:
        fails.append(f"{tag}: ink {ink} leaves the button face {list(box)} (shrink text / widen button)")
    for o in buttons:
        if o is it or not o["parts"]: continue   # plain backgrounds / dimmers never count as overlapping controls
        a, b = it["rect"], o["rect"]
        if a[0] < b[2] - 2 and b[0] < a[2] - 2 and a[1] < b[3] - 2 and b[1] < a[3] - 2 and o["path"] not in tag and tag not in o["path"]:
            fails.append(f"{tag}: overlaps button {o['path']} by {min(a[2], b[2]) - max(a[0], b[0]):.0f}x{min(a[3], b[3]) - max(a[1], b[1]):.0f}px")
            break

for it in (i for i in data["items"] if i["kind"] == "title"):
    x = cx_(it["probeX"]); x0, y0, x1, y1 = it["rect"]
    base = cy_(max(0, y0 - 140)); top_y = cy_(y1 + 140)
    edges = [y for y in range(base + 1, top_y) if dist(px[x, y], px[x, y - 1]) > 90]
    top = next((y for y in edges if max(px[x, y]) - min(px[x, y]) > 120), None)
    body = next((y for y in edges if top is not None and y > top + 30 and min(px[x, y]) > 215), None)
    lip = next((y for y in edges if top is not None and y > top + 40 and px[x, y][2] > px[x, y][1] + 40 and px[x, y][1] < 140), None)
    bottom = lip or body
    if top is None or bottom is None:
        oks.append(f"{it['path']}: band not found at x={x} (probe column crosses an icon?)"); continue
    c = (top + bottom) / 2; ty = (y0 + y1) / 2
    msg = f"{it['path']}: title ink centre vs band centre dy={ty - c:+.1f}px (band {top}-{bottom})"
    if abs(ty - c) > tol:
        fails.append(msg + f" -> move title {'up' if ty > c else 'down'} {abs(ty - c) / (it['scale'] or 1):.1f} units")
    else:
        oks.append(msg)

for o in oks: print("OK  ", o)
for f in fails: print("FAIL", f)
print(f"{len(oks)} ok, {len(fails)} fail")
sys.exit(1 if fails else 0)
