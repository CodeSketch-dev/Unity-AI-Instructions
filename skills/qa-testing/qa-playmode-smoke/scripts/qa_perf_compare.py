"""Compare a perf capture against a stored baseline (structural counters, regression ratios). Stdlib only.

  py -I qa_perf_compare.py --capture capture.json --baseline qa/perf-baseline.json [--update-baseline]

capture/baseline JSON: {"measured_on": "editor|device|build", "scenarios": {"<name>": {"batches": n, "setpass": n,
"gc_bytes_per_frame": n, "frame_p95_ms": x, "memory_mb": x}}}. The report is always labelled with measured_on; Editor numbers
are indicative of structure, not of device milliseconds. The allowed growth is a soft default; a project may widen it per scenario
with "tolerance": {"batches": 0.2, ...} inside the baseline entry.
"""
import argparse
import json
import sys

DEFAULT_TOL = {"batches": 0.10, "setpass": 0.10, "frame_p95_ms": 0.15, "memory_mb": 0.10}
GC_ABS = 256  # bytes per frame above baseline


def compare(capture, baseline):
    rows, failed = [], False
    for name, cur in capture.get("scenarios", {}).items():
        base = baseline.get("scenarios", {}).get(name)
        if not base:
            rows.append((name, "-", "no baseline", "NEW"))
            continue
        tol = dict(DEFAULT_TOL, **base.get("tolerance", {}))
        for key, t in tol.items():
            if key in cur and key in base and base[key] > 0:
                grow = cur[key] / base[key] - 1
                bad = grow > t
                failed = failed or bad
                rows.append((name, key, "%.1f -> %.1f (%+.0f%%, allowed %+.0f%%)" % (base[key], cur[key], grow * 100, t * 100), "FAIL" if bad else "ok"))
        if "gc_bytes_per_frame" in cur and "gc_bytes_per_frame" in base:
            bad = cur["gc_bytes_per_frame"] > base["gc_bytes_per_frame"] + GC_ABS
            failed = failed or bad
            rows.append((name, "gc_bytes_per_frame", "%d -> %d (allowed +%d)" % (base["gc_bytes_per_frame"], cur["gc_bytes_per_frame"], GC_ABS), "FAIL" if bad else "ok"))
    return rows, failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capture", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--update-baseline", action="store_true")
    a = ap.parse_args(argv)
    with open(a.capture, encoding="utf-8") as f:
        cap = json.load(f)
    try:
        with open(a.baseline, encoding="utf-8") as f:
            base = json.load(f)
    except OSError:
        base = {"scenarios": {}}
    rows, failed = compare(cap, base)
    print("measured_on: %s (%s)" % (cap.get("measured_on", "unknown"), "not a low-end device measurement" if cap.get("measured_on") != "device" else "device"))
    for r in rows:
        print("%-4s %s %s %s" % (r[3], r[0], r[1], r[2]))
    if a.update_baseline:
        with open(a.baseline, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cap, f, indent=1)
        print("baseline updated (needs the human's approval to keep)")
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
