"""Compare a render-stats JSON against per-tier world budgets.

Usage: py -I world_budget_check.py <Low|Mid|High> <stats.json> [budgets.json]
stats.json example: {"batches": 80, "verts": 90000, "materials": 1, "measured_on": "editor"}
Exit 1 if any metric exceeds its budget. Unknown stat keys are ignored; budgets without
a stat are not reported. "measured_on" (device|build|editor) is echoed so an Editor
number is never mistaken for a device measurement.
"""
import json
import os
import sys
from collections import namedtuple

Result = namedtuple("Result", "metric value limit status")
DEFAULT_BUDGETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "world-budgets.json")


def load_budgets(path=None):
    with open(path or DEFAULT_BUDGETS, encoding="utf-8") as f:
        return json.load(f)["tiers"]


def check(stats, tier, budgets):
    limits = budgets[tier]
    out = []
    for metric, limit in limits.items():
        if metric in stats:
            value = stats[metric]
            out.append(Result(metric, value, limit, "FAIL" if value > limit else "OK"))
    return out


def measurement_note(stats):
    where = stats.get("measured_on")
    if not where:
        return "UNLABELLED: set measured_on to device, build or editor"
    return "measured_on: %s%s" % (where, "" if where == "device" else " (not a device measurement)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print("usage: world_budget_check.py <Low|Mid|High> <stats.json> [budgets.json]", file=sys.stderr)
        return 2
    tier, stats_path = argv[0], argv[1]
    budgets = load_budgets(argv[2] if len(argv) > 2 else None)
    if tier not in budgets:
        print("unknown tier %r; choose from %s" % (tier, ", ".join(budgets)), file=sys.stderr)
        return 2
    with open(stats_path, encoding="utf-8") as f:
        stats = json.load(f)
    results = check(stats, tier, budgets)
    for r in results:
        print("%s %s: %s / %s" % (r.status, r.metric, r.value, r.limit))
    print(measurement_note(stats))
    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
