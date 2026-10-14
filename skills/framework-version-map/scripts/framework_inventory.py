"""Survey a Unity project's framework usage (read-only).

Usage: py -I framework_inventory.py <unity-project>
Lists DataBlock subclasses, ScriptableObjectSingleton factories (and whether the
Resources asset exists), RuntimeInitializeOnLoadMethod hooks, and StaticBus events
subscribed without a matching unsubscribe. Exit 1 if a factory asset is missing
or a bus event is unbalanced. Scans Assets/ only (not Library/ or Packages/).
"""
import json
import os
import re
import sys
from collections import defaultdict

NS_RE = re.compile(r"^\s*namespace\s+([\w.]+)", re.M)
DATA_RE = re.compile(r"\bclass\s+(\w+)\s*:\s*DataBlock<")
FACTORY_RE = re.compile(r"\bclass\s+(\w+)\s*:\s*(?:Serialized)?ScriptableObjectSingleton<")
HOOK_RE = re.compile(r"RuntimeInitializeOnLoadMethod\s*\(\s*(?:RuntimeInitializeLoadType\.)?(\w+)?")
BUS_RE = re.compile(r"StaticBus<(\w+)>\.(Subscribe|Unsubscribe)\s*\(")


def cs_files(project):
    assets = os.path.join(project, "Assets")
    for base, _, files in os.walk(assets):
        for name in files:
            if name.endswith(".cs"):
                yield os.path.join(base, name)


def singleton_assets(project):
    found = set()
    for base, _, files in os.walk(os.path.join(project, "Assets")):
        if os.path.basename(base) == "ScriptableObjectSingletons":
            found.update(n for n in files if n.endswith(".asset"))
    return found


def scan(project):
    assets = singleton_assets(project)
    res = {"data_blocks": [], "factories": [], "init_hooks": [], "unbalanced_bus": []}
    bus = defaultdict(lambda: [0, 0])
    for path in cs_files(project):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        m = NS_RE.search(text)
        ns = m.group(1) if m else ""
        rel = os.path.relpath(path, project)
        for cls in DATA_RE.findall(text):
            res["data_blocks"].append({"name": (ns + "." if ns else "") + cls, "file": rel})
        for cls in FACTORY_RE.findall(text):
            full = (ns + "." if ns else "") + cls
            res["factories"].append({"name": full, "file": rel, "asset_exists": (full + ".asset") in assets})
        for stage in HOOK_RE.findall(text):
            res["init_hooks"].append({"stage": stage or "AfterSceneLoad", "file": rel})
        for ev, kind in BUS_RE.findall(text):
            bus[ev][0 if kind == "Subscribe" else 1] += 1
    for ev, (subs, unsubs) in sorted(bus.items()):
        if subs > unsubs:
            res["unbalanced_bus"].append({"event": ev, "subscribe": subs, "unsubscribe": unsubs})
    return res


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or not os.path.isdir(os.path.join(argv[0], "Assets")):
        print("usage: framework_inventory.py <unity-project>", file=sys.stderr)
        return 2
    res = scan(argv[0])
    if "--json" in argv:
        print(json.dumps(res, indent=2))
    else:
        print("DataBlocks: %d" % len(res["data_blocks"]))
        for d in res["data_blocks"]:
            print("  %s  (%s)" % (d["name"], d["file"]))
        print("Factories: %d" % len(res["factories"]))
        for f in res["factories"]:
            print("  %s  asset=%s" % (f["name"], "ok" if f["asset_exists"] else "MISSING"))
        print("Init hooks: %d" % len(res["init_hooks"]))
        for h in res["init_hooks"]:
            print("  %s  (%s)" % (h["stage"], h["file"]))
        for u in res["unbalanced_bus"]:
            print("UNBALANCED bus: %(event)s subscribe=%(subscribe)d unsubscribe=%(unsubscribe)d" % u)
    bad = any(not f["asset_exists"] for f in res["factories"]) or bool(res["unbalanced_bus"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
