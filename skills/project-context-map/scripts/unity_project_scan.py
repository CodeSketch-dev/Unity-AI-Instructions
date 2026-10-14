"""Scan a Unity project once into a compact index, then answer questions from the index instead of re-grepping.

Read-only. Never modifies the scanned project; write outputs OUTSIDE the project.

  scan   python -I unity_project_scan.py scan  --root <project> --out-json idx.json [--out-md map.md]
  query  python -I unity_project_scan.py query --index idx.json  pet cage [--limit 25]
  show   python -I unity_project_scan.py show  --index idx.json  Pet_Manager

What the index holds (all derived from files, nothing guessed):
  scripts   path, namespace, declared types (kind, name, base types), line count
  prefabs   path + the MonoBehaviour classes it uses (resolved through script GUIDs)
  scenes    path
  assets    ScriptableObject/asset classes with counts and sample paths
  menu      [MenuItem] entries with the file that defines them
  asmdefs, packages (manifest.json), folder file counts
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

VENDOR_HINTS = ("/plugins/", "/thirdparty/", "/third party/", "textmesh pro", "best http", "besthttp", "/demo", "/examples",
                "/samples", "externaldependencymanager", "googlemobileads", "firebase", "/editor default resources",
                "addressableassetsdata", "/gizmos/", "/streamingassets/")
SKIP_DIRS = {"Library", "Temp", "Obj", "Logs", ".git", ".vs", "Builds", "UserSettings", "node_modules"}
TYPE_RE = re.compile(r"^\s*(?:public|internal|private|protected|sealed|abstract|static|partial|\s)*\b(class|struct|enum|interface)\s+(\w+)(?:<[^>{]*>)?\s*(?::\s*([^\{\n]+))?", re.M)
NS_RE = re.compile(r"^\s*namespace\s+([\w.]+)", re.M)
MENU_RE = re.compile(r'\[MenuItem\("([^"]+)"')
GUID_RE = re.compile(r"guid: ([0-9a-f]{32})")
SCRIPT_REF_RE = re.compile(r"m_Script: \{fileID: 11500000, guid: ([0-9a-f]{32})")


def rel(path, root):
    return os.path.relpath(path, root).replace("\\", "/")


def walk(root, top):
    base = os.path.join(root, top)
    if not os.path.isdir(base):
        return
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def read(path, limit=None):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(limit) if limit else handle.read()
    except OSError:
        return ""


def meta_guid(path):
    meta = read(path + ".meta", 400)
    match = re.search(r"^guid: ([0-9a-f]{32})", meta, re.M)
    return match.group(1) if match else None


def is_vendor(path, first_party):
    if first_party:
        return not any(path.startswith(prefix) for prefix in first_party)
    return any(hint in path.lower() for hint in VENDOR_HINTS)


def scan(root, first_party=None):
    index = {"root": os.path.abspath(root), "scripts": [], "prefabs": [], "scenes": [], "assets": {}, "menu": [],
             "asmdefs": [], "packages": [], "folders": {}, "first_party": first_party or []}
    guid_to_class = {}
    folder_counts = Counter()

    # pass 1: scripts, menu items, asmdefs, scenes, folder stats
    for top in ("Assets", "Packages"):
        for path in walk(root, top):
            ext = os.path.splitext(path)[1].lower()
            r = rel(path, root)
            parts = r.split("/")
            if len(parts) > 2 and ext not in (".meta",):
                folder_counts["/".join(parts[:3])] += 1
            if ext == ".cs":
                text = read(path)
                ns = NS_RE.search(text)
                types = [{"kind": m.group(1), "name": m.group(2), "bases": (m.group(3) or "").strip().rstrip("{").strip()[:80]}
                         for m in TYPE_RE.finditer(text)][:12]
                index["scripts"].append({"path": r, "ns": ns.group(1) if ns else "", "types": types, "lines": text.count("\n") + 1})
                guid = meta_guid(path)
                if guid:
                    stem = os.path.splitext(os.path.basename(path))[0]
                    names = [t["name"] for t in types]
                    guid_to_class[guid] = stem if stem in names or not names else names[0]
                for m in MENU_RE.finditer(text):
                    index["menu"].append({"item": m.group(1), "path": r})
            elif ext == ".unity":
                index["scenes"].append(r)
            elif ext == ".asmdef":
                index["asmdefs"].append(r)

    manifest = read(os.path.join(root, "Packages", "manifest.json"))
    if manifest:
        try:
            index["packages"] = sorted(json.loads(manifest).get("dependencies", {}).keys())
        except ValueError:
            pass

    # pass 2: prefabs and ScriptableObject assets resolved through script GUIDs
    assets = defaultdict(list)
    for path in walk(root, "Assets"):
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".prefab", ".asset"):
            continue
        text = read(path)
        if not text.startswith("%YAML"):
            continue
        classes = sorted({guid_to_class[g] for g in SCRIPT_REF_RE.findall(text) if g in guid_to_class})
        r = rel(path, root)
        if ext == ".prefab":
            index["prefabs"].append({"path": r, "scripts": classes[:10]})
        elif classes:
            assets[classes[0]].append(r)
    index["assets"] = {cls: {"count": len(paths), "sample": paths[:3]} for cls, paths in sorted(assets.items())}
    index["folders"] = dict(folder_counts.most_common(60))
    return index


def draft_map(index):
    scripts = index["scripts"]
    fp = index.get("first_party")
    first_party = [s for s in scripts if not is_vendor(s["path"], fp)] or scripts
    lines = [f"# Project map (auto-draft from scan of {os.path.basename(index['root'])})", "",
             "Replace the draft sections with human knowledge; keep it under ~150 lines.", "",
             "## Scenes"] + [f"- {s}" for s in index["scenes"] if not is_vendor(s, fp)][:25]
    lines += ["", "## Packages"] + [f"- {p}" for p in index["packages"][:60]]
    lines += ["", "## Asmdefs"] + [f"- {a}" for a in index["asmdefs"][:20]]
    lines += ["", "## Top folders (file counts)"] + [f"- {f}: {c}" for f, c in list(index["folders"].items())[:25]]
    by_dir = defaultdict(list)
    for s in first_party:
        by_dir["/".join(s["path"].split("/")[:-1])].append(s)
    lines += ["", "## Scripts by folder (first-party; type: bases)"]
    for d, items in sorted(by_dir.items())[:60]:
        names = []
        for s in items[:12]:
            for t in s["types"][:1]:
                names.append(t["name"] + (f": {t['bases'].split(',')[0].strip()}" if t["bases"] else ""))
        lines.append(f"- {d} ({len(items)}): " + "; ".join(names))
    lines += ["", "## Editor menu tools"] + [f"- {m['item']}  ({m['path']})" for m in index["menu"] if not is_vendor(m["path"], fp)][:40]
    lines += ["", "## Asset classes (ScriptableObjects)"] + [f"- {c} x{v['count']}  e.g. {v['sample'][0]}" for c, v in list(index["assets"].items())[:40]]
    lines += ["", "## Singletons / events / states (by base type)"]
    for key in ("Singleton", "IEvent", "StateMachine", "IState", "DataBlock", "MonoCached"):
        hits = [t["name"] for s in scripts for t in s["types"] if key in t["bases"]]
        if hits:
            lines.append(f"- {key}: " + ", ".join(sorted(set(hits))[:30]))
    return "\n".join(lines) + "\n"


def match(text, terms):
    low = text.lower()
    return all(t in low for t in terms)


def query(index, terms, limit, no_vendor=False):
    terms = [t.lower() for t in terms]
    fp = index.get("first_party")
    out = []
    for s in index["scripts"]:
        blob = s["path"] + " " + s["ns"] + " " + " ".join(t["name"] + " " + t["bases"] for t in s["types"])
        if match(blob, terms):
            names = ", ".join(f"{t['kind'][0]}:{t['name']}" for t in s["types"][:4])
            out.append(("script", f"{s['path']}  [{names}]  {s['lines']}L"))
    for p in index["prefabs"]:
        if match(p["path"] + " " + " ".join(p["scripts"]), terms):
            out.append(("prefab", f"{p['path']}  scripts: {', '.join(p['scripts'][:5])}"))
    for s in index["scenes"]:
        if match(s, terms):
            out.append(("scene", s))
    for m in index["menu"]:
        if match(m["item"] + " " + m["path"], terms):
            out.append(("menu", f"{m['item']}  ({m['path']})"))
    for cls, v in index["assets"].items():
        if match(cls + " " + " ".join(v["sample"]), terms):
            out.append(("asset", f"{cls} x{v['count']}  e.g. {v['sample'][0]}"))
    def vendor(line):
        return is_vendor(line.split("  ")[0].split(" ")[0] if line.startswith("Assets") or line.startswith("Packages") else "", fp)
    tagged = [(kind, line, vendor(line)) for kind, line in out]
    if no_vendor:
        tagged = [x for x in tagged if not x[2]]
    tagged.sort(key=lambda x: x[2])
    print(f"{len(tagged)} matches for {terms} (showing {min(limit, len(tagged))}; (v) = vendor/third-party)")
    for kind, line, is_v in tagged[:limit]:
        print(f"[{kind}]{'(v)' if is_v else ''} {line}")


def show(index, name):
    low = name.lower()
    for s in index["scripts"]:
        if any(t["name"].lower() == low for t in s["types"]) or os.path.basename(s["path"]).lower() == low + ".cs":
            print(json.dumps(s, indent=1))
            users = [p["path"] for p in index["prefabs"] if any(c.lower() == low for c in p["scripts"])]
            print(f"used by {len(users)} prefabs:", *users[:15], sep="\n  ")
            return
    for p in index["prefabs"]:
        if os.path.splitext(os.path.basename(p["path"]))[0].lower() == low:
            print(p["path"])
            for cls in p["scripts"]:
                paths = [s["path"] for s in index["scripts"] if any(t["name"] == cls for t in s["types"])]
                print(f"  script {cls}: {paths[0] if paths else '?'}")
            return
    print("not found")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", required=True)
    p_scan.add_argument("--out-json", required=True)
    p_scan.add_argument("--out-md")
    p_scan.add_argument("--first-party", nargs="*", help="path prefixes of your own code, e.g. Assets/_ROOT (default: vendor heuristics)")
    p_query = sub.add_parser("query")
    p_query.add_argument("--index", required=True)
    p_query.add_argument("--limit", type=int, default=25)
    p_query.add_argument("--no-vendor", action="store_true")
    p_query.add_argument("terms", nargs="+")
    p_show = sub.add_parser("show")
    p_show.add_argument("--index", required=True)
    p_show.add_argument("name")
    args = parser.parse_args()

    if args.cmd == "scan":
        root = os.path.abspath(args.root)
        out_json = os.path.abspath(args.out_json)
        if out_json.startswith(root + os.sep):
            sys.exit("write the index outside the scanned project")
        index = scan(root, args.first_party)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as handle:
            json.dump(index, handle)
        if args.out_md:
            with open(args.out_md, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(draft_map(index))
        print(f"scripts {len(index['scripts'])}, prefabs {len(index['prefabs'])}, scenes {len(index['scenes'])}, "
              f"asset classes {len(index['assets'])}, menu items {len(index['menu'])} -> {out_json}")
    else:
        index = json.load(open(args.index, encoding="utf-8"))
        if args.cmd == "query":
            query(index, args.terms, args.limit, args.no_vendor)
        else:
            show(index, args.name)


if __name__ == "__main__":
    main()
