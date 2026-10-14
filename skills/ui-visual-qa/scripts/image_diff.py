"""Pixel diff of two PNG screenshots, stdlib only (no Pillow/numpy needed).

Usage: py -I image_diff.py <reference.png> <actual.png> [--mode mockup|golden] [--mask masks.json] [--out diff.png]
masks.json: list of [x0, y0, x1, y1] rectangles to ignore (timers, random rewards).
A pixel differs when any RGB channel differs by more than 12/255. Prints the differing %,
the verdict and the top regions (32 px blocks merged) so a fix can target exact areas.
Verdict thresholds (initial, report 17; tune on real screens): mockup PASS <= 1.5%, WARN <= 4%;
golden PASS <= 0.2%, FAIL > 1%. In mockup mode block-SSIM (8x8 grayscale) must also be >= 0.97 PASS, >= 0.93 WARN.
Edge maps (Sobel, 1 px tolerance, downscaled to ~480 px): mismatch <= 15% PASS, <= 30% WARN, else FAIL (initial).
Exit 1 on FAIL.
Images must have the same size. Reads 8-bit non-interlaced PNG (gray, RGB, palette, gray+alpha, RGBA).
"""
import json
import struct
import sys
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
CHANNEL_TOLERANCE = 12
BLOCK = 32


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != PNG_SIG:
        raise ValueError("not a PNG: %s" % path)
    pos, idat, plte = 8, b"", None
    w = h = depth = ctype = interlace = None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if depth != 8 or interlace != 0 or ctype not in (0, 2, 3, 4, 6):
        raise ValueError("unsupported PNG (need 8-bit, non-interlaced)")
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        ft = raw[i]
        cur = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = cur[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                cur[x] = (cur[x] + a) & 255
            elif ft == 2:
                cur[x] = (cur[x] + b) & 255
            elif ft == 3:
                cur[x] = (cur[x] + ((a + b) >> 1)) & 255
            elif ft == 4:
                cur[x] = (cur[x] + _paeth(a, b, c)) & 255
        rows.append(cur)
        prev = cur
    pixels = []
    for cur in rows:
        if ctype == 2:
            pixels.append([(cur[j], cur[j + 1], cur[j + 2]) for j in range(0, stride, 3)])
        elif ctype == 6:
            pixels.append([(cur[j], cur[j + 1], cur[j + 2]) for j in range(0, stride, 4)])
        elif ctype == 0:
            pixels.append([(v, v, v) for v in cur])
        elif ctype == 4:
            pixels.append([(cur[j], cur[j], cur[j]) for j in range(0, stride, 2)])
        else:
            pixels.append([plte[v] for v in cur])
    return w, h, pixels


def write_png(path, pixels):
    h, w = len(pixels), len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _masked(x, y, masks):
    return any(m[0] <= x < m[2] and m[1] <= y < m[3] for m in masks)


def _differs(p, q):
    return abs(p[0] - q[0]) > CHANNEL_TOLERANCE or abs(p[1] - q[1]) > CHANNEL_TOLERANCE or abs(p[2] - q[2]) > CHANNEL_TOLERANCE


def diff(a, b, masks=()):
    h, w = len(a), len(a[0])
    if (len(b), len(b[0])) != (h, w):
        raise ValueError("size mismatch: %dx%d vs %dx%d" % (w, h, len(b[0]), len(b)))
    count, considered = 0, 0
    blocks = {}
    for y in range(h):
        for x in range(w):
            if masks and _masked(x, y, masks):
                continue
            considered += 1
            if _differs(a[y][x], b[y][x]):
                count += 1
                k = (x // BLOCK, y // BLOCK)
                bx0, by0, bx1, by1, n = blocks.get(k, (x, y, x, y, 0))
                blocks[k] = (min(bx0, x), min(by0, y), max(bx1, x), max(by1, y), n + 1)
    merged = []
    for (kx, ky), (x0, y0, x1, y1, n) in sorted(blocks.items()):
        for m in merged:
            if abs(m["kx"] - kx) <= 1 and abs(m["ky"] - ky) <= 1:
                bx0, by0, bx1, by1 = m["box"]
                m["box"] = (min(bx0, x0), min(by0, y0), max(bx1, x1 + 1), max(by1, y1 + 1))
                m["pixels"] += n
                m["kx"], m["ky"] = kx, ky
                break
        else:
            merged.append({"kx": kx, "ky": ky, "box": (x0, y0, x1 + 1, y1 + 1), "pixels": n})
    merged.sort(key=lambda m: -m["pixels"])
    regions = [{"box": m["box"], "pixels": m["pixels"]} for m in merged[:5]]
    return {"differing_pct": round(100.0 * count / considered, 4) if considered else 0.0, "pixels": count, "regions": regions}


def ssim(a, b, masks=(), block=8):
    """Mean SSIM of the grayscale images over non-overlapping blocks (fast approximation of windowed SSIM)."""
    h, w = len(a), len(a[0])
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    total, n = 0.0, 0
    for by in range(0, h - block + 1, block):
        for bx in range(0, w - block + 1, block):
            if masks and any(_masked(bx + dx, by + dy, masks) for dx in (0, block - 1) for dy in (0, block - 1)):
                continue
            xs, ys = [], []
            for y in range(by, by + block):
                ra, rb = a[y], b[y]
                for x in range(bx, bx + block):
                    p, q = ra[x], rb[x]
                    xs.append((p[0] + p[1] + p[2]) / 3.0)
                    ys.append((q[0] + q[1] + q[2]) / 3.0)
            m = len(xs)
            mx, my = sum(xs) / m, sum(ys) / m
            vx = sum((v - mx) ** 2 for v in xs) / m
            vy = sum((v - my) ** 2 for v in ys) / m
            cov = sum((xs[i] - mx) * (ys[i] - my) for i in range(m)) / m
            total += ((2 * mx * my + c1) * (2 * cov + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))
            n += 1
    return total / n if n else 1.0


def _downscale(img, f):
    if f <= 1:
        return img
    h, w = len(img) // f * f, len(img[0]) // f * f
    out = []
    for y in range(0, h, f):
        row = []
        for x in range(0, w, f):
            r = g = b = 0
            for dy in range(f):
                line = img[y + dy]
                for dx in range(f):
                    p = line[x + dx]
                    r += p[0]
                    g += p[1]
                    b += p[2]
            n = f * f
            row.append((r // n, g // n, b // n))
        out.append(row)
    return out


def _edges(gray, w, h, thresh):
    pts = set()
    for y in range(1, h - 1):
        up, mid, dn = gray[y - 1], gray[y], gray[y + 1]
        for x in range(1, w - 1):
            gx = (up[x + 1] + 2 * mid[x + 1] + dn[x + 1]) - (up[x - 1] + 2 * mid[x - 1] + dn[x - 1])
            gy = (dn[x - 1] + 2 * dn[x] + dn[x + 1]) - (up[x - 1] + 2 * up[x] + up[x + 1])
            if abs(gx) + abs(gy) > thresh:
                pts.add((x, y))
    return pts


def edge_diff(a, b, masks=(), thresh=120, max_dim=480):
    """Sobel edge maps compared with 1 px tolerance (after downscaling to ~max_dim). Catches shifted frames
    when colours are similar. mismatch_pct = unmatched edge pixels of both images / all edge pixels."""
    h0, w0 = len(a), len(a[0])
    f = max(1, -(-max(w0, h0) // max_dim))
    if masks:
        a = [[(0, 0, 0) if _masked(x, y, masks) else a[y][x] for x in range(w0)] for y in range(h0)]
        b = [[(0, 0, 0) if _masked(x, y, masks) else b[y][x] for x in range(w0)] for y in range(h0)]
    a, b = _downscale(a, f), _downscale(b, f)
    h, w = len(a), len(a[0])
    ga = [[(p[0] + p[1] + p[2]) // 3 for p in row] for row in a]
    gb = [[(p[0] + p[1] + p[2]) // 3 for p in row] for row in b]
    ea, eb = _edges(ga, w, h, thresh), _edges(gb, w, h, thresh)
    if not ea and not eb:
        return {"mismatch_pct": 0.0, "edges": 0}

    def unmatched(src, dst):
        return sum(1 for (x, y) in src if not any((x + dx, y + dy) in dst for dx in (-1, 0, 1) for dy in (-1, 0, 1)))

    bad = unmatched(ea, eb) + unmatched(eb, ea)
    return {"mismatch_pct": round(100.0 * bad / (len(ea) + len(eb)), 3), "edges": len(ea) + len(eb)}


def verdict(pct, mode="mockup", ssim=None, edge=None):
    if mode == "golden":
        return "PASS" if pct <= 0.2 else ("FAIL" if pct > 1.0 else "WARN")
    order = ["PASS", "WARN", "FAIL"]
    levels = [("PASS" if pct <= 1.5 else ("WARN" if pct <= 4.0 else "FAIL"))]
    if ssim is not None:
        levels.append("PASS" if ssim >= 0.97 else ("WARN" if ssim >= 0.93 else "FAIL"))
    if edge is not None:
        levels.append("PASS" if edge <= 15.0 else ("WARN" if edge <= 30.0 else "FAIL"))
    return order[max(order.index(x) for x in levels)]


def overlay(a, b, masks=()):
    out = []
    for y, row in enumerate(b):
        line = []
        for x, q in enumerate(row):
            if (not masks or not _masked(x, y, masks)) and _differs(a[y][x], q):
                line.append((255, 0, 0))
            else:
                g = (a[y][x][0] + a[y][x][1] + a[y][x][2]) // 3
                line.append((g // 2 + 127, g // 2 + 127, g // 2 + 127))
        out.append(line)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    opts = {"--mode": "mockup", "--mask": None, "--out": None}
    pos, i = [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            pos.append(argv[i])
            i += 1
    if len(pos) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    masks = []
    if opts["--mask"]:
        with open(opts["--mask"], encoding="utf-8") as f:
            masks = [tuple(m) for m in json.load(f)]
    _, _, a = read_png(pos[0])
    _, _, b = read_png(pos[1])
    try:
        r = diff(a, b, masks)
    except ValueError as e:
        print("FAIL %s" % e)
        return 1
    sim = ssim(a, b, masks)
    edge = edge_diff(a, b, masks)["mismatch_pct"]
    v = verdict(r["differing_pct"], opts["--mode"], sim, edge)
    print("%s: %.3f%% pixels differ (%d), SSIM %.3f, edge mismatch %.1f%%, mode=%s" % (v, r["differing_pct"], r["pixels"], sim, edge, opts["--mode"]))
    for reg in r["regions"]:
        print("  region %s: %d px" % (reg["box"], reg["pixels"]))
    if opts["--out"]:
        write_png(opts["--out"], overlay(a, b, masks))
        print("wrote %s" % opts["--out"])
    return 1 if v == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
