"""UI-CONTRAST (soft): text vs background luminance contrast measured from a screenshot, stdlib only.

Usage: py -I ui_contrast.py <screenshot.png> <texts.json> [--min 3.0] [--strict]
texts.json comes from `ui_validator.py --dump-rects texts.json` (canvas units, origin bottom-left).
For each text rect the pixels are split into two luminance clusters (2-means); the ratio is
(L_light + 0.05) / (L_dark + 0.05) on WCAG relative luminance. Below --min (default 3.0) prints WARN;
--strict turns warnings into exit 1. A flat region gives 1.0 (no visible text or invisible text).
The screenshot must show the same screen/aspect the rects were computed for.
"""
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from image_diff import read_png  # noqa: E402


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(p):
    return 0.2126 * _lin(p[0]) + 0.7152 * _lin(p[1]) + 0.0722 * _lin(p[2])


def contrast_ratio(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def region_contrast(img, box):
    x0, y0, x1, y1 = box
    vals = [luminance(img[y][x]) for y in range(max(0, y0), min(len(img), y1)) for x in range(max(0, x0), min(len(img[0]), x1))]
    if not vals:
        return 1.0
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-6:
        return 1.0
    c0, c1 = lo, hi
    for _ in range(8):
        a = [v for v in vals if abs(v - c0) <= abs(v - c1)]
        b = [v for v in vals if abs(v - c0) > abs(v - c1)]
        if not a or not b:
            break
        c0, c1 = sum(a) / len(a), sum(b) / len(b)
    return contrast_ratio(c0, c1)


def to_pixels(rect, canvas, image_size):
    sx, sy = image_size[0] / canvas[0], image_size[1] / canvas[1]
    x0, y0, x1, y1 = rect
    return (round(x0 * sx), round(image_size[1] - y1 * sy), round(x1 * sx), round(image_size[1] - y0 * sy))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in argv
    minimum = 3.0
    if "--min" in argv:
        minimum = float(argv[argv.index("--min") + 1])
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--min")]
    if len(pos) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    w, h, img = read_png(pos[0])
    with open(pos[1], encoding="utf-8") as f:
        data = json.load(f)
    warns = 0
    for t in data["texts"]:
        ratio = region_contrast(img, to_pixels(t["rect"], data["canvas"], (w, h)))
        level = "WARN" if ratio < minimum else "OK"
        warns += level == "WARN"
        print("%s UI-CONTRAST [%s] %.2f:1 (min %.1f)" % (level, t["path"], ratio, minimum))
    return 1 if strict and warns else 0


if __name__ == "__main__":
    sys.exit(main())
