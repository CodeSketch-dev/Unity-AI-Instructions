#!/usr/bin/env python
"""Size baseline for a Unity project. READ-ONLY. Stdlib only.

python -I size_report.py --root <project> [--depth 2] [--top 30] [--big-mb 20] [--first-party Assets/_Game Assets/_Art]
Prints markdown tables: Assets by folder (MB, files), bytes by extension, biggest files, text-serialized (YAML)
.asset files above the threshold (generated meshes stored as text are the classic bloat), binary scenes,
tracked-generated suspects (if git is available), scenes size, Resources size, packages count.
Run it before and after each stage and paste both outputs into the lean report.
"""
import argparse, os, subprocess
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--depth", type=int, default=2)
ap.add_argument("--top", type=int, default=30)
ap.add_argument("--big-mb", type=float, default=20.0)
ap.add_argument("--first-party", nargs="*", default=[])
a = ap.parse_args()
ROOT = Path(a.root).resolve()
ASSETS = ROOT / "Assets"
MB = 1024 * 1024

files = []
for dp, dn, fn in os.walk(ASSETS):
    for f in fn:
        if f.endswith(".meta"):
            continue
        p = Path(dp) / f
        try:
            files.append((p.relative_to(ROOT).as_posix(), p.stat().st_size))
        except OSError:
            pass


def table(title, head, rows):
    print(f"\n## {title}\n\n| " + " | ".join(head) + " |\n|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")


tot = sum(s for _, s in files)
print(f"# Size report for {ROOT.name}\n\nAssets: {tot / MB:.0f} MB, {len(files)} non-meta files")

by = defaultdict(lambda: [0, 0])
for p, s in files:
    key = "/".join(p.split("/")[:a.depth])
    by[key][0] += s
    by[key][1] += 1
table(f"Folders (depth {a.depth})", ["folder", "MB", "files"],
      [(k, f"{v[0] / MB:.1f}", v[1]) for k, v in sorted(by.items(), key=lambda kv: -kv[1][0])[:a.top]])

if a.first_party:
    fp = sum(s for p, s in files if any(p.startswith(x.rstrip("/") + "/") for x in a.first_party))
    print(f"\nFirst-party ({', '.join(a.first_party)}): {fp / MB:.0f} MB")

ext = defaultdict(lambda: [0, 0])
for p, s in files:
    e = os.path.splitext(p)[1].lower() or "(none)"
    ext[e][0] += s
    ext[e][1] += 1
table("Extensions", ["ext", "MB", "files"], [(k, f"{v[0] / MB:.1f}", v[1]) for k, v in sorted(ext.items(), key=lambda kv: -kv[1][0])[:15]])

table(f"Biggest files (top {a.top})", ["MB", "path"], [(f"{s / MB:.1f}", p) for p, s in sorted(files, key=lambda x: -x[1])[:a.top]])

yaml_big, binary_scn = [], []
for p, s in files:
    ext_ = os.path.splitext(p)[1].lower()
    if ext_ in (".asset", ".unity", ".prefab") and s >= a.big_mb * MB * 0.25 or ext_ in (".unity",):
        try:
            head = (ROOT / p).read_bytes()[:16]
        except OSError:
            continue
        text = head.startswith(b"%YAML")
        if ext_ == ".unity" and not text:
            binary_scn.append((p, s))
        if ext_ == ".asset" and text and s >= a.big_mb * MB * 0.25:
            yaml_big.append((p, s))
table(f"Text-serialized .asset above {a.big_mb * 0.25:.0f} MB (candidates for binary/FBX/mesh-compressed)", ["MB", "path"],
      [(f"{s / MB:.1f}", p) for p, s in sorted(yaml_big, key=lambda x: -x[1])[:a.top]])
table("Binary-serialized scenes (not diffable)", ["MB", "path"], [(f"{s / MB:.1f}", p) for p, s in binary_scn])
table("Scenes", ["MB", "path"], [(f"{s / MB:.1f}", p) for p, s in sorted(files, key=lambda x: -x[1]) if p.endswith(".unity")][:20])

res = sum(s for p, s in files if "/resources/" in p.lower())
print(f"\nResources folders total: {res / MB:.1f} MB")
print("Prefab files over 2 MB:", sum(1 for p, s in files if p.endswith(".prefab") and s > 2 * MB))
print("Assets over %.0f MB: %d" % (a.big_mb, sum(1 for p, s in files if s > a.big_mb * MB)))

mf = ROOT / "Packages" / "manifest.json"
if mf.exists():
    import json
    deps = json.loads(mf.read_text(encoding="utf8")).get("dependencies", {})
    print(f"Manifest packages: {len(deps)} ({sum(1 for k in deps if k.startswith('com.unity.modules.'))} built-in modules)")

try:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "Assets"], capture_output=True, text=True, timeout=120).stdout.splitlines()
    sus = defaultdict(int)
    for line in out:
        parts = line.split("/")
        for seg in parts[1:-1]:
            low = seg.lower()
            if low in ("graphify-out", "library", "temp", "obj", "logs", "node_modules", "__pycache__", ".cache", "cache", "caches") or low.endswith("~"):
                sus["/".join(parts[:parts.index(seg) + 1])] += 1
                break
    table("Tracked generated/derived suspects inside Assets (git ls-files)", ["tracked paths", "folder"], [(v, k) for k, v in sorted(sus.items(), key=lambda kv: -kv[1])])
    print(f"\ngit tracked files under Assets: {len(out)}")
    cnt = subprocess.run(["git", "-C", str(ROOT), "count-objects", "-vH"], capture_output=True, text=True, timeout=60).stdout
    print("\n```\n" + cnt.strip() + "\n```")
except Exception as e:
    print("\n(git checks skipped:", e, ")")
