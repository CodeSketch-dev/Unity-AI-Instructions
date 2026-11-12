"""Render a numbered wireframe PNG from a rects JSON (stdlib only).

Usage: py -I wireframe.py <rects.json> <out.png> [--scale 0.5]
rects.json comes from `ui_spec_tool.py rects spec.yaml --out rects.json` (canvas px, origin bottom-left).
Containers are dim outlines, leaf elements are filled boxes carrying their element number `n`, state
alternatives are drawn with an orange outline. It is a layout placeholder, not art: use it to compare the
contract with a built screenshot and to give a pattern a mockup before a real capture exists.
"""
import json
import struct
import sys
import zlib

BG = (24, 24, 32)
GLYPHS = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}


def _color(n):
    h = ((n or 0) * 47) % 360
    # simple HSV(h, 0.45, 0.75) -> RGB
    c, x = 0.75 * 0.45, 0.75 * 0.45 * (1 - abs((h / 60.0) % 2 - 1))
    m = 0.75 - c
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return tuple(int((v + m) * 255) for v in (r, g, b))


def render(data, scale=0.5):
    cw, ch = data["canvas"]
    w, h = int(cw * scale), int(ch * scale)
    img = [[BG] * w for _ in range(h)]

    def box(r):
        x0, x1 = int(r[0] * scale), int(r[2] * scale)
        y0, y1 = int(h - r[3] * scale), int(h - r[1] * scale)
        return max(0, x0), max(0, y0), min(w - 1, x1), min(h - 1, y1)

    def outline(b, col):
        x0, y0, x1, y1 = b
        for x in range(x0, x1 + 1):
            img[y0][x] = img[y1][x] = col
        for y in range(y0, y1 + 1):
            img[y][x0] = img[y][x1] = col

    def glyphs(text, cx, cy, px):
        gw = len(text) * 4 * px - px
        x = cx - gw // 2
        y = cy - 5 * px // 2
        for ch_ in text:
            for ry, row in enumerate(GLYPHS.get(ch_, GLYPHS["0"])):
                for rx, bit in enumerate(row):
                    if bit == "1":
                        for dy in range(px):
                            for dx in range(px):
                                yy, xx = y + ry * px + dy, x + rx * px + dx
                                if 0 <= yy < h and 0 <= xx < w:
                                    img[yy][xx] = (255, 255, 255)
            x += 4 * px

    els = data["elements"]
    for e in els:                                     # containers first, so leaves draw on top
        if e.get("container"):
            b = box(e["rect"])
            for y in range(b[1] + 1, b[3]):
                for x in range(b[0] + 1, b[2]):
                    img[y][x] = (34, 34, 46)
            outline(b, (96, 96, 120))
    for e in els:
        if e.get("container"):
            continue
        b = box(e["rect"])
        col = _color(e.get("n"))
        for y in range(b[1] + 1, b[3]):
            for x in range(b[0] + 1, b[2]):
                img[y][x] = col
        outline(b, (255, 150, 40) if e.get("state") else (235, 235, 235))
        if e.get("n") is not None:
            px = max(1, min(4, (b[3] - b[1]) // 8, (b[2] - b[0]) // (4 * len(str(e["n"])) + 1)))
            glyphs(str(e["n"]), (b[0] + b[2]) // 2, (b[1] + b[3]) // 2, px)
    seen = {}
    for e in els:                                     # number tags for containers (top-left corner, shifted when corners coincide)
        if e.get("container") and e.get("n") is not None:
            b = box(e["rect"])
            k = seen.get((b[0], b[1]), 0)
            seen[(b[0], b[1])] = k + 1
            glyphs(str(e["n"]), b[0] + 8 + k * 16, b[1] + 8 + k * 2, 2)
    return img


def write_png(path, pixels):
    h, w = len(pixels), len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    scale = 0.5
    if "--scale" in argv:
        scale = float(argv[argv.index("--scale") + 1])
    pos = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--scale")]
    if len(pos) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    with open(pos[0], encoding="utf-8") as f:
        data = json.load(f)
    write_png(pos[1], render(data, scale))
    print("wrote %s" % pos[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
