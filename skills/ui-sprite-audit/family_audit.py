#!/usr/bin/env python3
"""Family audit: outline thickness of EVERY sliced kit sprite in CANVAS units (px / (ppu/100)), grouped by name prefix; flags outliers.
python -I family_audit.py <UiKit folder> <kit_manifest.json> [--target 3.6] [--tol 0.8]
A kit whose plates differ in canvas-unit outline looks sloppy even if each sprite is fine on its own: run this before and after any art change."""
import sys, json, os, argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
def outline_px(path):
    a = np.asarray(Image.open(path).convert('RGBA'), dtype=np.float32) / 255; al = a[..., 3] > .5
    lum = a[..., :3] @ np.array([.3, .59, .11], dtype=np.float32); dark = (lum < .28) & al; inner = al & ~dark
    if not inner.any() or not dark.any(): return None
    d = ndi.distance_transform_edt(~inner); edge = al & ~ndi.binary_erosion(al); return float(np.median(d[edge]))
if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('manifest'); p.add_argument('--target', type=float, default=3.6); p.add_argument('--tol', type=float, default=0.8)
    a = p.parse_args(); m = json.load(open(a.manifest)); base = m.get('ppu', 200); rows = []
    for e in m['sprites']:
        b = e.get('border') or [0, 0, 0, 0]
        if not any(b): continue
        f = os.path.join(a.folder, e['name'] + '.png')
        if not os.path.exists(f): continue
        px = outline_px(f)
        if px is None: continue
        ppu = e.get('ppu') or base; rows.append((e['name'], ppu, px, px / (ppu / 100.0)))
    bad = [r for r in rows if abs(r[3] - a.target) > a.tol]
    for n, ppu, px, u in sorted(rows, key=lambda r: r[3]): print(('XX ' if abs(u - a.target) > a.tol else 'ok '), '%-28s ppu %-5g outline %5.1f px = %4.2f units' % (n, ppu, px, u))
    print('%d sliced sprites measured, %d outside %.1f +- %.1f units' % (len(rows), len(bad), a.target, a.tol)); sys.exit(1 if bad else 0)
