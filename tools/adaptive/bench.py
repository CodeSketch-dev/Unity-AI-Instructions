"""Reproducible REAL micro-benchmark of deterministic methods (no model, so tokens stay UNKNOWN).

Task category `bench.count_skills`: count skill folders by three methods; verified by comparing to the true count.
  py -I tools/adaptive/bench.py [--runs 15] [--persist]
By default uses a throwaway DB so your learning data is not polluted; --persist records into the real store.
Reports measured median/p90 latency and verified success per method, then what the selector chooses before/after.
"""
import argparse
import glob
import os
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from adaptive import loop, selector, store  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CAT, ENV = "bench.count_skills", "os=windows|app=repo|ver=bench1"


def m_glob(ctx):
    return len(glob.glob(os.path.join(REPO, "skills", "*", "*", "SKILL.md")))


def m_git(ctx):
    r = subprocess.run(["git", "-C", REPO, "ls-files", "skills/*/*/SKILL.md"], capture_output=True, text=True, timeout=30)
    return len([ln for ln in r.stdout.splitlines() if ln.count("/") == 3])


def m_powershell(ctx):
    cmd = "(Get-ChildItem -Recurse -Filter SKILL.md '%s').Count" % os.path.join(REPO, "skills")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=60)
    return int(r.stdout.strip())


METHODS = [("python_glob", m_glob), ("git_ls_files", m_git), ("powershell_gci", m_powershell)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=15)
    ap.add_argument("--persist", action="store_true")
    a = ap.parse_args()
    truth = len(glob.glob(os.path.join(REPO, "skills", "*", "*", "SKILL.md")))
    tmp = None
    if not a.persist:
        tmp = tempfile.mkdtemp(prefix="adaptive-bench-")
        os.environ["ADAPTIVE_HOME"] = tmp
    conn = store.connect()
    names = ["powershell_gci", "git_ls_files", "python_glob"]  # deliberately naive prior order: shows measured data overriding the prior
    before = selector.select(conn, CAT, names, ENV, explore=False)
    print("truth=%d skills | before: choose %s (%s)" % (truth, before["method"], before["source"]))
    for i in range(a.runs):
        for name, fn in METHODS:
            step = loop.Step(name, fn, verify=lambda r, c: r == truth, timeout_s=60)
            loop.run([step], CAT, ENV, conn=conn, max_attempts=1)
    for name in names:
        rows = store.scope_runs(conn, CAT, ENV, name)
        lat = sorted(r["latency_ms"] for r in rows)
        ok = sum(1 for r in rows if r["success"] and r["verified"])
        print("%-15s n=%d verified_ok=%d median=%.1fms p90=%.1fms tokens=UNKNOWN" % (
            name, len(rows), ok, statistics.median(lat), lat[int(0.9 * (len(lat) - 1))]))
    after = selector.select(conn, CAT, names, ENV, explore=False)
    print("after: choose %s (%s) | %s" % (after["method"], after["source"], after["reason"]))
    for m, s in after["stats"].items():
        print("  %-15s n_eff=%.1f p=%.2f lb=%.2f lat=%s" % (m, s["n_eff"], s["p"], s["lb"], None if s["lat_ms"] is None else round(s["lat_ms"], 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
