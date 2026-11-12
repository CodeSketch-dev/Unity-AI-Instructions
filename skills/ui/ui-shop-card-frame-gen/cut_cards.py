# Cuts card frames generated on a flat #FF00FF canvas (skill ui-shop-card-frame-gen). Edit NAMES / W, H / BORDER for the target game.
# Cuts the Codex card_burst_* sheets off their magenta canvas, resizes to 404x562 and installs them in the UI kit + kit_manifest.json.
# Usage: python -I install.py <raw_dir> <kit_dir> [--dry]
import json, sys, os
from PIL import Image

W, H = 404, 562
BORDER = [44, 44, 44, 44]   # L, B, R, T: rounded corners + outline + lip inside the caps
NAMES = ["gold", "purple", "blue", "green", "coral", "teal", "rainbow"]

def key(img):
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = (255 - r) + g + (255 - b)   # distance to pure magenta #FF00FF (purple / pink card colours stay > 150)
            if d < 70: px[x, y] = (0, 0, 0, 0)
            elif d < 150:   # anti-aliased edge: fade + despill toward the dark outline
                t = 1 - (d - 70) / 80.0
                px[x, y] = (int(r * (1 - t)), g, int(b * (1 - t)), int(a * (1 - t)))
    bb = img.getchannel('A').point(lambda v: 255 if v > 200 else 0).getbbox()   # solid card only: stray soft pixels outside the card never widen the crop
    return img.crop(bb)

def main():
    raw, kit = sys.argv[1], sys.argv[2]
    dry = "--dry" in sys.argv
    man_path = os.path.join(kit, "kit_manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    names = {e["name"]: e for e in man["sprites"]}
    for n in NAMES:
        src = os.path.join(raw, "card_burst_%s.png" % n)
        if not os.path.exists(src): print("MISSING", src); continue
        im = key(Image.open(src)).resize((W, H), Image.LANCZOS)
        out = os.path.join(kit if not dry else raw, ("card_burst_%s.png" % n) if not dry else ("cut_%s.png" % n))
        im.save(out)
        e = {"name": "card_burst_" + n, "w": W, "h": H, "border": BORDER, "lips": [0, 18, 0, 0]}
        if "card_burst_" + n in names: names["card_burst_" + n].update(e)
        else: man["sprites"].append(e)
        print("ok", out)
    if not dry: json.dump(man, open(man_path, "w", encoding="utf-8"), indent=1)

main()
