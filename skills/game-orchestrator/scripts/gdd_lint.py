"""GDD completeness linter (read-only, stdlib only): the gate between human work and agent work.

Usage: py -I gdd_lint.py <gdd-dir> [--out _generated] [--state docs/orchestrator/state.json] [--no-fs] [--day-h 16]
Reads `gdd/` (00-index.md, systems/, ui/, economy/, assets/, captures/index.md, qa/golden-path.md), applies rules
L001-L015 (report 21 sec 2.3) and writes `<out>/lint-report.md`, `questions.md` (open `?` values) and, with no BLOCK,
`gdd.json` + a content hash. Exit 1 when any BLOCK remains. Severity: BLOCK stops the pipeline, WARN becomes a
recorded assumption, INFO is a hint. Nothing is invented: an unknown value must stay `?`.
"""
import csv
import hashlib
import json
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import miniyaml  # noqa: E402

Finding = namedtuple("Finding", "sev rule where message")

TYPES = {"character", "camera", "input", "world", "interactable", "economy", "shop", "inventory", "pets", "quests", "audio",
         "vfx", "monetization", "retention", "tutorial", "localization", "bots", "minigame"}
ENVELOPE = ("id", "type", "title", "priority", "fidelity")
VERIFIERS = ("[play]", "[shot]", "[edit]", "[inspect]", "[sim]")
P0_TYPES = ("character", "camera", "input", "world", "economy")
CAP_RE = re.compile(r"^(CAP-\d+)@")
ANCHORS = {"top-left", "top-center", "top-right", "mid-left", "center", "mid-right", "bottom-left", "bottom-center", "bottom-right",
           "stretch", "stretch-top", "stretch-bottom", "stretch-left", "stretch-right"}
BASE = {"top-left": (0, 1), "top-center": (0.5, 1), "top-right": (1, 1), "mid-left": (0, 0.5), "center": (0.5, 0.5), "mid-right": (1, 0.5),
        "bottom-left": (0, 0), "bottom-center": (0.5, 0), "bottom-right": (1, 0)}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_gdd(root):
    g = {"root": root, "index": {}, "systems": {}, "ui": {}, "prices": [], "assets": [], "captures": set(), "golden": "", "errors": []}
    p = os.path.join(root, "00-index.md")
    if os.path.isfile(p):
        g["index"], _ = miniyaml.split_front_matter(read(p))
    for kind, key in (("systems", "systems"), ("ui", "ui")):
        d = os.path.join(root, kind)
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(".md"):
                    try:
                        fm, _ = miniyaml.split_front_matter(read(os.path.join(d, name)))
                    except Exception as e:  # noqa: BLE001 - report as L001
                        fm = {}
                        g["errors"].append((kind + "/" + name, str(e)))
                    g[key][name[:-3]] = {"fm": fm, "file": kind + "/" + name}
    for name, key in (("economy/prices.csv", "prices"), ("assets/assets.csv", "assets")):
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8", newline="") as f:
                g[key] = list(csv.DictReader(f))
    cap = os.path.join(root, "captures", "index.md")
    if os.path.isfile(cap):
        g["captures"] = set(re.findall(r"\bCAP-\d+\b", read(cap)))
    gp = os.path.join(root, "qa", "golden-path.md")
    if os.path.isfile(gp):
        g["golden"] = read(gp)
    return g


def gdd_hash(root):
    h = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "_generated")
        for name in sorted(files):
            if name.endswith((".md", ".csv", ".yaml", ".json")):
                h.update(os.path.relpath(os.path.join(base, name), root).encode())
                h.update(read(os.path.join(base, name)).encode("utf-8", "replace"))
    return h.hexdigest()[:16]


def unknowns(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from unknowns(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from unknowns(v, "%s[%d]" % (path, i))
    elif isinstance(obj, str) and obj.strip().startswith("?"):
        yield path


TUNABLE_KEYS = {"price", "cost", "income", "reward", "amount", "multiplier", "boost", "damage", "cooldown",
                "range", "speed", "jump", "hp", "health", "interval", "duration", "growth", "target", "requirement",
                "cap", "weight", "odds", "chance", "radius", "lifetime", "count", "slots", "level", "value", "effect"}


def is_tunable_path(path):
    """Return true for numeric tuning fields that auto-balance may generate."""
    keys = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", path.lower())
    return any(k in TUNABLE_KEYS or any(k.endswith(s) for s in ("_price", "_cost", "_rate", "_multiplier", "_seconds")) for k in keys)


def features(fm):
    return [f for f in (fm.get("features") or []) if isinstance(f, dict)]


def effective(feature, fm, key, default=None):
    return feature.get(key, fm.get(key, default))


def _numeric(v):
    return isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)


def element_rects(fm):
    rc = fm.get("reference_canvas") or {}
    w, h = rc.get("w", 0), rc.get("h", 0)
    out = {}
    for e in fm.get("elements") or []:
        a = e.get("anchor")
        if a not in ANCHORS:
            continue
        if a.startswith("stretch"):
            r = e.get("rect") or {}
            out[e["name"]] = (r.get("left", 0), r.get("bottom", 0), w - r.get("right", 0), h - r.get("top", 0))
        elif _numeric(e.get("pos")) and _numeric(e.get("size")):
            bx, by = BASE[a]
            cx, cy = bx * w + e["pos"][0], by * h + e["pos"][1]
            out[e["name"]] = (cx - e["size"][0] / 2, cy - e["size"][1] / 2, cx + e["size"][0] / 2, cy + e["size"][1] / 2)
    return out


def lint(g, estimate_h=None, day_h=16, last_hash=None):
    F = []
    add = lambda sev, rule, where, msg: F.append(Finding(sev, rule, where, msg))  # noqa: E731
    idx = g["index"]
    docs = [(k, v["fm"], v["file"]) for k, v in g["systems"].items()] + [(k, v["fm"], v["file"]) for k, v in g["ui"].items()]
    # L001 schema
    for where, err in g["errors"]:
        add("BLOCK", "L001", where, "front-matter does not parse: %s" % err)
    for key in ("game", "genre", "systems", "priorities"):
        if key not in idx:
            add("BLOCK", "L001", "00-index.md", "missing key '%s'" % key)
    for key, fm, where in docs:
        if not fm:
            add("BLOCK", "L001", where, "no front-matter")
            continue
        if where.startswith("ui/"):
            for need in ("id", "type", "kind", "reference_canvas", "elements"):
                if need not in fm:
                    add("BLOCK", "L001", where, "missing key '%s'" % need)
        else:
            for need in ENVELOPE:
                if need not in fm:
                    add("BLOCK", "L001", where, "missing envelope key '%s'" % need)
            if fm.get("type") not in TYPES:
                add("BLOCK", "L001", where, "unknown type %r" % fm.get("type"))
    # L002 ids
    ids = {}
    for key, fm, where in docs:
        i = fm.get("id")
        if i in ids:
            add("BLOCK", "L002", where, "duplicate id %s (also %s)" % (i, ids[i]))
        ids[i] = where
        for f in features(fm):
            fid = f.get("id")
            if fid in ids:
                add("BLOCK", "L002", where, "duplicate feature id %s" % fid)
            ids[fid] = where
    for name in idx.get("systems") or []:
        if name not in ids:
            add("BLOCK", "L002", "00-index.md", "system %s listed but no file defines it" % name)
    graph = {}
    for key, fm, where in docs:
        deps = fm.get("depends_on") or []
        graph[fm.get("id")] = deps
        for d in deps:
            if d not in ids:
                add("BLOCK", "L002", where, "depends_on %s does not exist" % d)
        for o in fm.get("opened_by") or []:
            ref = str(o).split("@")[1] if "@" in str(o) else None
            if ref and ref not in ids:
                add("BLOCK", "L002", where, "opened_by %s does not exist" % o)
    state, stack = {}, []

    def visit(n):
        if state.get(n) == 2:
            return
        if state.get(n) == 1:
            add("BLOCK", "L002", n, "dependency cycle: %s" % " -> ".join(stack + [n]))
            return
        state[n] = 1
        stack.append(n)
        for d in graph.get(n, []):
            if d in graph:
                visit(d)
        stack.pop()
        state[n] = 2
    for n in list(graph):
        visit(n)
    # L003 evidence, L004 acceptance, L005 unknowns
    auto_balance = bool(idx.get("auto_balance")) or any(bool(fm.get("auto_balance")) for _, fm, _ in docs)
    for key, fm, where in docs:
        p_file = fm.get("priority", "P1")
        for f in features(fm):
            prio = f.get("priority", p_file)
            fid = effective(f, fm, "fidelity", "faithful")
            ev = f.get("evidence") or fm.get("evidence") or []
            sev = "BLOCK" if prio == "P0" else "WARN"
            if fid in ("exact", "faithful") and not ev:
                add(sev, "L003", "%s %s" % (where, f.get("id")), "%s feature has no evidence" % fid)
            for tok in ev:
                m = CAP_RE.match(str(tok))
                if not m or m.group(1) not in g["captures"]:
                    add(sev, "L003", "%s %s" % (where, f.get("id")), "evidence token %s not found in captures/index.md" % tok)
            acc = [a for a in (f.get("acceptance") or []) if isinstance(a, str)]
            if not any(a.strip().startswith(VERIFIERS) for a in acc):
                add("BLOCK", "L004", "%s %s" % (where, f.get("id")), "no acceptance criterion with a verifier tag %s" % "|".join(VERIFIERS))
            elif prio == "P0" and not any(a.strip().startswith(("[play]", "[edit]")) for a in acc):
                add("BLOCK", "L004", "%s %s" % (where, f.get("id")), "P0 feature needs a [play] or [edit] criterion")
        for path in unknowns(fm):
            if auto_balance and is_tunable_path(path):
                continue
            add("BLOCK" if p_file == "P0" else "WARN", "L005", "%s %s" % (where, path), "unknown value '?'")
    # L006 numbers, L007 reachability
    econ = [fm for _, fm, _ in docs if fm.get("type") == "economy"]
    currencies = {}
    for fm in econ:
        for c in fm.get("currencies") or []:
            currencies[c.get("id")] = c
            if not c.get("sources"):
                add("BLOCK", "L006", c.get("id"), "currency has no source")
            if not c.get("sinks"):
                add("BLOCK", "L006", c.get("id"), "currency has no sink")
    prices = g["prices"]
    if econ and not prices and not auto_balance:
        add("BLOCK", "L006", "economy/prices.csv", "price table missing")
    for row in prices:
        if row.get("currency") not in currencies and currencies:
            add("BLOCK", "L007", row.get("id"), "price row uses unknown currency %r" % row.get("currency"))
    paid = [r for r in prices if r.get("price") not in ("", "0", None)]
    for fm in econ:
        target = (fm.get("balance_targets") or {}).get("first_purchase_s")
        income = fm.get("income_per_s")
        if paid and target and income:
            cheapest = min(float(r["price"]) for r in paid if str(r["price"]).replace(".", "", 1).isdigit())
            if cheapest / float(income) > 1.5 * float(target):
                add("WARN", "L007", "economy", "cheapest paid item needs %.0f s of income, target is %s s" % (cheapest / float(income), target))
    used_currency = {r.get("currency") for r in prices}
    for cid, c in currencies.items():
        if cid not in used_currency and not (c.get("sinks") or []):
            add("WARN", "L007", cid, "currency is never spent")
    # L008 UI contract
    for key, fm, where in docs:
        if not where.startswith("ui/") or not fm:
            continue
        els = fm.get("elements") or []
        names = set()
        for e in els:
            nm = e.get("name")
            if nm in names:
                add("BLOCK", "L008", where, "duplicate element name %s" % nm)
            names.add(nm)
            if e.get("anchor") not in ANCHORS:
                add("BLOCK", "L008", "%s %s" % (where, nm), "bad or missing anchor")
            elif not str(e["anchor"]).startswith("stretch") and not (_numeric(e.get("pos")) and _numeric(e.get("size"))):
                add("BLOCK", "L008", "%s %s" % (where, nm), "fixed anchor needs pos and size")
            if fm.get("kind") == "hud" and not e.get("zone"):
                add("BLOCK", "L008", "%s %s" % (where, nm), "HUD element without zone")
        if not fm.get("states"):
            add("WARN", "L008", where, "no states listed")
        rects = element_rects(fm)
        leaves = [e for e in els if not e.get("container") and not e.get("state") and e.get("name") in rects]
        for i, a in enumerate(leaves):
            ra = rects[a["name"]]
            for b in leaves[i + 1:]:
                rb = rects[b["name"]]
                if min(ra[2] - 4, rb[2] - 4) - max(ra[0] + 4, rb[0] + 4) > 0 and min(ra[3] - 4, rb[3] - 4) - max(ra[1] + 4, rb[1] + 4) > 0:
                    add("BLOCK", "L008", where, "%s overlaps %s" % (a["name"], b["name"]))
        if not fm.get("captures") and fm.get("fidelity", idx.get("ui_default")) == "exact":
            add("BLOCK", "L014", where, "exact UI without captures")
        elif fm.get("fidelity", idx.get("ui_default")) == "exact" and len(fm.get("captures") or []) < len(fm.get("states") or []):
            add("BLOCK", "L014", where, "exact UI needs one full-screen capture per state (%d captures for %d states)" % (len(fm.get("captures") or []), len(fm.get("states") or [])))
        for tok in fm.get("captures") or []:
            m = CAP_RE.match(str(tok))
            if not m or m.group(1) not in g["captures"]:
                add("WARN", "L003", where, "capture token %s not found in captures/index.md" % tok)
    # L009 assets
    asset_ids = {r.get("id") for r in g["assets"]}
    for r in g["assets"]:
        if r.get("source") == "buy":
            add("BLOCK", "L009", r.get("id"), "asset source 'buy' is unresolved: the human must supply it")
        if not (r.get("license") or "").strip():
            add("WARN", "L009", r.get("id"), "asset has no license/provenance")
        if r.get("source") == "ref-project" and not g.get("no_fs") and not os.path.exists(r.get("path_or_prompt", "")):
            add("WARN", "L009", r.get("id"), "ref-project path does not exist")
    for key, fm, where in docs:
        for aid in set(re.findall(r"\bA-\d{3}\b", json.dumps(fm))):
            if aid not in asset_ids:
                add("BLOCK", "L009", where, "asset %s is not in assets/assets.csv" % aid)
    # L010 orphans
    opened = {str(o).split("@")[-1] for _, fm, _ in docs for o in fm.get("opened_by") or []}
    referenced_ui = {fm.get("ui") for _, fm, _ in docs if fm.get("ui")}
    for key, fm, where in docs:
        if where.startswith("ui/") and fm.get("kind") != "hud" and not fm.get("opened_by"):
            add("WARN", "L010", where, "screen is not opened by anything")
    for ref in referenced_ui:
        if ref not in ids:
            add("BLOCK", "L010", ref, "referenced UI screen does not exist")
    # L012 coverage
    types = {fm.get("type") for _, fm, w in docs if not w.startswith("ui/")}
    for t in P0_TYPES:
        if t not in types:
            add("BLOCK", "L012", "gdd", "required P0 system type '%s' is missing" % t)
    if not any(fm.get("kind") == "hud" for _, fm, w in docs if w.startswith("ui/")):
        add("BLOCK", "L012", "gdd", "no HUD screen")
    if not re.search(r"^\s*\d+\.", g["golden"], re.M):
        add("BLOCK", "L012", "qa/golden-path.md", "golden path missing or has no numbered steps")
    # L013 monetization
    for key, fm, where in docs:
        if fm.get("type") != "monetization":
            continue
        for ad in (fm.get("ads") or {}).get("rewarded") or []:
            if not ad.get("reward") or not ad.get("placement"):
                add("BLOCK", "L013", where, "rewarded ad %s without reward or placement" % ad.get("id"))
            if ad.get("ui") and ad["ui"] not in ids:
                add("BLOCK", "L013", where, "ad %s refers to a missing UI %s" % (ad.get("id"), ad["ui"]))
        for p in fm.get("iap") or []:
            if not p.get("grants") and p.get("type") != "non_consumable":
                add("BLOCK", "L013", where, "IAP %s grants nothing" % p.get("id"))
        if fm.get("ads") and not fm.get("consent"):
            add("WARN", "L013", where, "ads without a consent flow")
    # L011 budget
    if estimate_h is not None:
        if estimate_h > day_h:
            add("BLOCK", "L011", "gdd", "estimate %.1f h exceeds the %s h day: cut scope" % (estimate_h, day_h))
        elif estimate_h > 0.6 * day_h:
            add("WARN", "L011", "gdd", "estimate %.1f h is above 60%% of the %s h day" % (estimate_h, day_h))
    # L015 stale
    if last_hash and last_hash != gdd_hash(g["root"]):
        add("INFO", "L015", "gdd", "GDD changed since the last orchestrator run: re-plan impacted tasks")
    return F


def summary(g):
    counts = {}
    for _, v in g["systems"].items():
        fm = v["fm"]
        for f in features(fm):
            key = (fm.get("type"), f.get("priority", fm.get("priority")))
            counts[key] = counts.get(key, 0) + 1
    return counts


def write_reports(g, findings, out, estimate_h=None):
    os.makedirs(out, exist_ok=True)
    blocks = [f for f in findings if f.sev == "BLOCK"]
    lines = ["# GDD lint report", "", "%d BLOCK, %d WARN, %d INFO" % (len(blocks), sum(f.sev == "WARN" for f in findings), sum(f.sev == "INFO" for f in findings)), ""]
    if estimate_h is not None:
        lines.append("Estimated effort: %.1f agent-hours." % estimate_h)
    for sev in ("BLOCK", "WARN", "INFO"):
        for f in findings:
            if f.sev == sev:
                lines.append("- %s %s [%s] %s" % (sev, f.rule, f.where, f.message))
    with open(os.path.join(out, "lint-report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    qs = ["# Open questions (max 4 per batch, recommend a default for each)", ""]
    for f in findings:
        if f.rule == "L005":
            qs.append("- %s: %s" % (f.where, f.message))
    with open(os.path.join(out, "questions.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(qs) + "\n")
    if not blocks:
        merged = {"index": g["index"], "systems": {k: v["fm"] for k, v in g["systems"].items()}, "ui": {k: v["fm"] for k, v in g["ui"].items()},
                  "prices": g["prices"], "assets": g["assets"], "gdd_hash": gdd_hash(g["root"])}
        with open(os.path.join(out, "gdd.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(merged, fh, indent=1)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or not os.path.isdir(argv[0]):
        print(__doc__, file=sys.stderr)
        return 2
    opts = {"--out": None, "--state": None, "--day-h": "16"}
    for k in opts:
        if k in argv:
            opts[k] = argv[argv.index(k) + 1]
    g = load_gdd(argv[0])
    g["no_fs"] = "--no-fs" in argv
    day_h = float(opts["--day-h"])
    est = None
    try:
        import gen_task_graph  # noqa: WPS433
        graph = gen_task_graph.generate(g)
        est = graph["totals"]["wall_h"]
    except ImportError:
        pass
    last = None
    if opts["--state"] and os.path.isfile(opts["--state"]):
        with open(opts["--state"], encoding="utf-8") as f:
            last = json.load(f).get("gdd_hash")
    findings = lint(g, est, day_h, last)
    out = opts["--out"] or os.path.join(argv[0], "_generated")
    write_reports(g, findings, out, est)
    for f in findings:
        print("%s %s [%s] %s" % (f.sev, f.rule, f.where, f.message))
    blocks = sum(f.sev == "BLOCK" for f in findings)
    print("%d BLOCK, %d WARN" % (blocks, sum(f.sev == "WARN" for f in findings)))
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
