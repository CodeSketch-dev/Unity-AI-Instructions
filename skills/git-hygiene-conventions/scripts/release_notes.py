#!/usr/bin/env python
"""Release notes from commit subjects since the previous tag. Read-only git. Stdlib only.

python -I release_notes.py --repo <path> [--from v1.21] [--to HEAD]
Groups '[vX.Y]: Area: subject' and 'type(area): subject' commits by area/type; prints markdown.
Without --from it uses the latest tag (git describe --tags --abbrev=0) or the whole history.
"""
import argparse, re, subprocess
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=".")
ap.add_argument("--from", dest="frm", default=None)
ap.add_argument("--to", default="HEAD")
a = ap.parse_args()


def git(*args):
    return subprocess.run(["git", "-C", a.repo, *args], capture_output=True, text=True, encoding="utf8", errors="replace").stdout


frm = a.frm or git("describe", "--tags", "--abbrev=0", a.to).strip()
rng = f"{frm}..{a.to}" if frm else a.to
groups = defaultdict(list)
for line in git("log", rng, "--no-merges", "--pretty=%h\t%s").splitlines():
    h, _, s = line.partition("\t")
    m = re.match(r"^\[v[\d.]+\]: ([^:]+): (.+)$", s) or re.match(r"^(\w+)(?:\(([^)]+)\))?: (.+)$", s)
    if m and len(m.groups()) == 2:
        groups[m.group(1)].append((h, m.group(2)))
    elif m:
        groups[m.group(2) or m.group(1)].append((h, m.group(3)))
    else:
        groups["other"].append((h, s))
print(f"# Changes {rng}\n")
for g in sorted(groups, key=lambda k: (k == "other", k)):
    print(f"## {g}")
    for h, s in groups[g]:
        print(f"- {s} ({h})")
    print()
