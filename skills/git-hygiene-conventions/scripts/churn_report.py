#!/usr/bin/env python
"""Churn report: files changed most often in the last N commits (.meta excluded). Read-only git. Stdlib only.

python -I churn_report.py --repo <path> [--commits 500] [--top 20] [--tag-range v1.4..v1.5]
Reading the result: a scene or hub class near the top means conflicts and catch-all code; generated files
(font atlases, link.xml, solution files, localization tables) near the top should be ignored or isolated.
"""
import argparse, subprocess
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=".")
ap.add_argument("--commits", type=int, default=500)
ap.add_argument("--top", type=int, default=20)
ap.add_argument("--tag-range", default=None)
a = ap.parse_args()
rng = [a.tag_range] if a.tag_range else ["-n", str(a.commits)]
out = subprocess.run(["git", "-C", a.repo, "log", *rng, "--name-only", "--pretty=format:@@@"], capture_output=True, text=True, encoding="utf8", errors="replace").stdout
c = Counter()
for line in out.splitlines():
    line = line.strip()
    if line and line != "@@@" and not line.endswith(".meta"):
        c[line] += 1
subj = subprocess.run(["git", "-C", a.repo, "log", *rng, "--pretty=%s"], capture_output=True, text=True, encoding="utf8", errors="replace").stdout.splitlines()
low = sum(1 for s in subj if s.strip().lower() in (".", "update", "doing", "wip", "fix", "add", "tweak"))
print(f"commits analysed: {len(subj)}; low-information subjects: {low}")
print("| changes | file |\n|---|---|")
for f, n in c.most_common(a.top):
    print(f"| {n} | {f} |")
