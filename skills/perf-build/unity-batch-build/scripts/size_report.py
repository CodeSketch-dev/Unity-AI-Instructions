"""Size report for an Android build artifact (AAB or APK are zip files): total size, largest entries, budget and regression gates.

  py -I size_report.py --artifact Builds/game.aab [--gates qa/gates.json] [--previous Builds/previous-size.json] [--out Builds/size.json]

gates.json keys used: {"size": {"max_mb": 150, "target_mb": 80, "max_regression_pct": 5}}. The number is the compressed artifact
size, an upper bound for the store download estimate (the store serves split APKs, usually smaller). Exit 1 on a gate failure.
"""
import argparse
import json
import os
import sys
import zipfile

MB = 1024.0 * 1024.0


def analyse(path, top=15):
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
    entries = sorted(((i.compress_size, i.filename) for i in infos), reverse=True)
    groups = {}
    for size, name in entries:
        key = name.split("/")[0] if "/" in name else "(root)"
        if "/lib/" in "/" + name:
            key = "native libs"
        elif name.endswith((".obb", ".bundle", ".unity3d")):
            key = "content bundles"
        groups[key] = groups.get(key, 0) + size
    return {
        "artifact": os.path.basename(path),
        "size_mb": round(os.path.getsize(path) / MB, 2),
        "entries": len(infos),
        "top": [{"name": n, "mb": round(s / MB, 2)} for s, n in entries[:top]],
        "groups_mb": {k: round(v / MB, 2) for k, v in sorted(groups.items(), key=lambda kv: -kv[1])[:10]},
    }


def gate(report, gates, previous):
    notes, failed = [], False
    cfg = (gates or {}).get("size", {})
    mx, target, reg = cfg.get("max_mb"), cfg.get("target_mb"), cfg.get("max_regression_pct", 5)
    if mx is not None and report["size_mb"] > mx:
        notes.append("FAIL size %.2f MB is over the hard budget %.1f MB" % (report["size_mb"], mx))
        failed = True
    elif target is not None and report["size_mb"] > target:
        notes.append("WARN size %.2f MB is over the target %.1f MB" % (report["size_mb"], target))
    if previous and previous.get("size_mb"):
        grow = (report["size_mb"] / previous["size_mb"] - 1) * 100
        if grow > reg:
            notes.append("FAIL size grew %.1f%% (allowed %.1f%%)" % (grow, reg))
            failed = True
        else:
            notes.append("ok growth %+.1f%%" % grow)
    return notes, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--gates")
    ap.add_argument("--previous")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rep = analyse(a.artifact)
    gates = json.load(open(a.gates, encoding="utf-8")) if a.gates and os.path.isfile(a.gates) else {}
    prev = json.load(open(a.previous, encoding="utf-8")) if a.previous and os.path.isfile(a.previous) else None
    notes, failed = gate(rep, gates, prev)
    rep["gate"] = {"failed": failed, "notes": notes}
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rep, f, indent=1)
    print("%s: %.2f MB, %d entries" % (rep["artifact"], rep["size_mb"], rep["entries"]))
    for k, v in rep["groups_mb"].items():
        print("  %-18s %.2f MB" % (k, v))
    for t in rep["top"][:8]:
        print("  top %-60s %.2f MB" % (t["name"][:60], t["mb"]))
    for n in notes:
        print(n)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
