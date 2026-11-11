#!/usr/bin/env python3
"""UI sprite audit: PASS/FAIL per criterion, exit 1 on any FAIL. Usage:
  python -I sprite_audit.py FILE.png [FILE2.png ...] [--max-long 512] [--min-outline-pct 6.5] [--kind button|board|icon]
Criteria (see skills/ui-art-quality-gate): not clipped at the canvas edge, no magenta fringe, size cap, outline thickness uniform
(p90-p10 <= 1 px) and thick enough, silhouette = exact rounded rectangle (edge deviation of the straight middle strips <= 0.6 px,
corner radius 20-36% of height), corner cap <= 36% of the short side, dominant colour reported (compare with the file name)."""
import sys, os, argparse, colorsys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
LUM = np.array([.3, .59, .11], dtype=np.float32)

def audit(path, a):
    r = []
    im = Image.open(path).convert('RGBA'); w, h = im.size
    x = np.asarray(im, dtype=np.float32) / 255; al = x[..., 3]; rgb = x[..., :3]
    solid = al > .5
    def add(name, ok, info): r.append((name, bool(ok), info))
    add('size cap', max(w, h) <= a.max_long, f'{w}x{h} (cap {a.max_long} px long side)')
    corners_solid = int(al[0, 0] > .3) + int(al[0, -1] > .3) + int(al[-1, 0] > .3) + int(al[-1, -1] > .3)
    add('not clipped (canvas corners transparent = rounded, not cut)', a.kind == 'icon' or corners_solid == 0, f'{corners_solid} canvas corners are solid')
    mag = ((rgb[..., 0] > .75) & (rgb[..., 2] > .75) & (rgb[..., 1] < .35) & (al > .3)).sum()
    add('no magenta fringe', mag < 8, f'{int(mag)} magenta-ish pixels')
    if a.kind == 'icon':
        return r
    ys, xs = np.where(solid)
    if len(ys) == 0: add('has content', False, 'empty'); return r
    H = ys.max() - ys.min() + 1; W = xs.max() - xs.min() + 1
    lum = rgb @ LUM; dark = (lum < .28) & solid
    inner = solid & ~dark
    d_in = ndi.distance_transform_edt(~inner)
    edge = solid & ~ndi.binary_erosion(solid)
    v = d_in[edge]; spread = np.percentile(v, 90) - np.percentile(v, 10); med = float(np.median(v))
    add('outline uniform (p90-p10 <= 1.2 px)', spread <= 1.2, f'median {med:.1f} px, spread {spread:.1f} px')
    units = med / (a.ppu / 100.0)
    add(f'outline in CANVAS units {a.units_min}-{a.units_max} (px / (ppu/100); same value for every family)', a.units_min <= units <= a.units_max, f'{units:.2f} units ({med:.1f} px at ppu {a.ppu:g})')
    if a.min_outline_pct > 0: add(f'outline >= {a.min_outline_pct}% of height', med / H * 100 >= a.min_outline_pct, f'{med / H * 100:.1f}%')
    # silhouette: straight middle strips (top & bottom edge rows over the central third) must not wave
    cols = np.arange(xs.min() + W // 3, xs.min() + 2 * W // 3)
    top = np.array([np.argmax(solid[:, c]) for c in cols], dtype=float)
    bot = np.array([h - 1 - np.argmax(solid[::-1, c]) for c in cols], dtype=float)
    dev = max(top.max() - top.min(), bot.max() - bot.min())
    add('straight middle strips (<= 1.0 px deviation)', dev <= 1.0, f'{dev:.1f} px')
    # corner radius from the top-left corner: first solid column on the top row
    row0 = solid[ys.min()]; c0 = np.argmax(row0) - xs.min()
    rad = c0 / H * 100
    if a.kind in ('button', 'tile'):
        lo = 15 if a.kind == 'tile' else 20
        add(f'corner radius {lo}-36% of height', lo <= rad <= 36, f'{rad:.0f}%')
    cap = max(c0, 0) + med
    add('corner cap <= 36% of short side', cap <= .36 * min(W, H) + 1, f'cap ~{cap:.0f}px of {min(W, H)}')
    m = inner & (al > .9)
    if m.any():
        c = rgb[m].mean(axis=0); hh, ss, vv = colorsys.rgb_to_hsv(*c)
        add('dominant colour (compare with file name)', True, f'hue {hh * 360:.0f} sat {ss:.2f} val {vv:.2f}')
    return r

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('files', nargs='+'); p.add_argument('--max-long', type=int, default=512)
    p.add_argument('--min-outline-pct', type=float, default=0.0); p.add_argument('--kind', default='button'); p.add_argument('--ppu', type=float, default=100.0); p.add_argument('--units-min', type=float, default=3.0); p.add_argument('--units-max', type=float, default=4.2)
    a = p.parse_args(); bad = 0
    for f in a.files:
        res = audit(f, a); fails = [n for n, ok, _ in res if not ok]; bad += len(fails)
        print(('PASS ' if not fails else 'FAIL ') + os.path.basename(f))
        for n, ok, info in res: print('   ', 'ok ' if ok else 'XX ', n, '-', info)
    sys.exit(1 if bad else 0)
