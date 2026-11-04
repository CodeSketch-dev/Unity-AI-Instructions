#!/usr/bin/env python
"""Import-settings audit from .meta files. READ-ONLY. Stdlib only.

python -I import_audit.py --root <project> [--skip Assets/Plugins Assets/<VendorFolder>] [--tex-max 1024] [--top 12]
Reports (per top folder under Assets, vendor folders skipped):
  textures: count, maxTextureSize distribution, files whose default size exceeds --tex-max, mipmaps on sprites, no Android override
  audio:    loadType (0 DecompressOnLoad, 1 CompressedInMemory, 2 Streaming), compression format, mono vs stereo candidates by size
  models:   meshCompression off, isReadable on, animation import on (no clips) - the usual RAM and size leaks
Numbers are file-level facts from .meta, not runtime RAM; say so in the report.
"""
import argparse, os, re
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--skip", nargs="*", default=["Assets/Plugins", "Assets/StreamingAssets"])
ap.add_argument("--tex-max", type=int, default=1024)
ap.add_argument("--top", type=int, default=12)
a = ap.parse_args()
ROOT = Path(a.root).resolve()
ASSETS = ROOT / "Assets"
skip = tuple(s.strip("/") + "/" for s in a.skip)
TEX = {".png", ".jpg", ".jpeg", ".tga", ".psd", ".tif", ".tiff", ".exr", ".hdr", ".bmp"}
AUD = {".wav", ".mp3", ".ogg", ".aif", ".aiff", ".flac"}
MOD = {".fbx", ".obj", ".blend", ".dae", ".3ds"}


def val(txt, key):
    m = re.search(r"^\s*" + re.escape(key) + r":\s*(-?\d+)", txt, re.M)
    return int(m.group(1)) if m else None


tex = defaultdict(list)
aud = defaultdict(list)
mod = defaultdict(list)
for dp, dn, fn in os.walk(ASSETS):
    for f in fn:
        ext = os.path.splitext(f)[1].lower()
        if ext not in TEX | AUD | MOD:
            continue
        p = Path(dp) / f
        r = p.relative_to(ROOT).as_posix()
        if r.startswith(skip):
            continue
        mp = Path(str(p) + ".meta")
        if not mp.exists():
            continue
        txt = mp.read_text(encoding="utf8", errors="ignore")
        top = "/".join(r.split("/")[:3])
        size = p.stat().st_size
        if ext in TEX:
            android = re.search(r"buildTarget:\s*Android\s*\n\s*maxTextureSize:\s*(\d+)", txt)
            tex[top].append(dict(path=r, size=size, max=val(txt, "maxTextureSize"), mips=val(txt, "enableMipMap"),
                                 sprite=val(txt, "textureType") == 8, android=int(android.group(1)) if android else None))
        elif ext in AUD:
            aud[top].append(dict(path=r, size=size, load=val(txt, "loadType"), comp=val(txt, "compressionFormat"),
                                 mono=val(txt, "forceToMono"), ext=ext))
        else:
            mod[top].append(dict(path=r, size=size, comp=val(txt, "meshCompression"), readable=val(txt, "isReadable"),
                                 anim=val(txt, "importAnimation")))

print("# Import audit (from .meta; file-level facts, not runtime RAM)")
print("\n## Textures\n\n| folder | files | MB on disk | max size histogram | > %d | no Android override | sprites with mipmaps |" % a.tex_max)
print("|---|---|---|---|---|---|---|")
for k, v in sorted(tex.items(), key=lambda kv: -sum(x["size"] for x in kv[1]))[:a.top]:
    hist = Counter(x["max"] for x in v)
    print(f"| {k} | {len(v)} | {sum(x['size'] for x in v) / 1048576:.1f} | {dict(sorted(hist.items(), key=lambda t: -(t[0] or 0)))} | "
          f"{sum(1 for x in v if (x['max'] or 0) > a.tex_max)} | {sum(1 for x in v if x['android'] is None)} | {sum(1 for x in v if x['sprite'] and x['mips'])} |")
print("\n## Audio (loadType 0 DecompressOnLoad, 1 CompressedInMemory, 2 Streaming)\n\n| folder | files | MB | loadType histogram | forceToMono=0 |")
print("|---|---|---|---|---|")
for k, v in sorted(aud.items(), key=lambda kv: -sum(x["size"] for x in kv[1]))[:a.top]:
    print(f"| {k} | {len(v)} | {sum(x['size'] for x in v) / 1048576:.1f} | {dict(Counter(x['load'] for x in v))} | {sum(1 for x in v if x['mono'] == 0)} |")
big_dec = sorted((x for v in aud.values() for x in v if x["load"] == 0 and x["size"] > 200_000), key=lambda x: -x["size"])[:10]
if big_dec:
    print("\nLargest clips decompressed on load (>200 KB; short SFX should be CompressedInMemory, music Streaming):")
    for x in big_dec:
        print(f"- {x['size'] / 1024:.0f} KB {x['path']}")
print("\n## Models (meshCompression 0 = off; isReadable 1 = CPU copy kept in RAM)\n\n| folder | files | MB | compression off | readable | importAnimation on |")
print("|---|---|---|---|---|---|")
for k, v in sorted(mod.items(), key=lambda kv: -sum(x["size"] for x in kv[1]))[:a.top]:
    print(f"| {k} | {len(v)} | {sum(x['size'] for x in v) / 1048576:.1f} | {sum(1 for x in v if x['comp'] == 0)} | {sum(1 for x in v if x['readable'])} | {sum(1 for x in v if x['anim'])} |")
