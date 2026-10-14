"""Resolve the GUID dependency closure of Unity assets and optionally copy it.

Read-only by default. Source project is never modified.

Examples
  python -I resolve_closure.py --source D:/ref --asset Assets/Prefabs/Boss.prefab
  python -I resolve_closure.py --source D:/ref --target D:/mine --asset Assets/Prefabs/Boss.prefab \
      --asset Assets/Vfx/Hit.prefab --dest-prefix Assets/_Art/Imported
  python -I resolve_closure.py ... --apply      # copy missing files + .meta (GUIDs preserved)

How it works: every .meta in the source gives guid -> file. Text-serialized assets (and the .meta of
models/textures, whose material remaps reference GUIDs) are scanned for `guid: <32 hex>`; newly found
assets are scanned in turn until nothing new appears.

Limits (reported, never guessed): scripts (.cs/.dll) are listed but copied only with --allow-scripts;
GUIDs not found in the source Assets/Packages (built-in resources, registry packages) are listed as
unresolved; shader `#include "path"` and Resources.Load/Addressables string paths are not GUID
references, so they are listed as warnings for manual review.
"""
import argparse
import json
import os
import re
import shutil
import sys

GUID_RE = re.compile(r"guid: ([0-9a-f]{32})")
INCLUDE_RE = re.compile(r'#include\s+"([^"]+)"')
TEXT_EXTS = {
    ".prefab", ".mat", ".asset", ".anim", ".controller", ".overridecontroller", ".unity",
    ".playable", ".mask", ".physicmaterial", ".physicsmaterial2d", ".flare", ".rendertexture",
    ".spriteatlas", ".lighting", ".signal", ".shadergraph", ".shadersubgraph", ".vfx", ".guiskin",
    ".fontsettings", ".cubemap", ".terrainlayer", ".brush", ".preset", ".inputactions", ".asmdef",
    ".asmref", ".shadervariants", ".mixer", ".renderer", ".timeline",
}
SCRIPT_EXTS = {".cs", ".dll"}
SKIP_DIRS = {"Library", "Temp", "Obj", "Logs", ".git", ".vs", "Builds", "UserSettings"}
BUILTIN_PREFIXES = ("0000000000000000", "00000000000000000")


def build_index(project_root):
    """guid -> absolute asset path for every .meta under Assets/ and Packages/."""
    index = {}
    for top in ("Assets", "Packages"):
        base = os.path.join(project_root, top)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if not name.endswith(".meta"):
                    continue
                meta = os.path.join(dirpath, name)
                try:
                    with open(meta, "r", encoding="utf-8", errors="ignore") as handle:
                        head = handle.read(600)
                except OSError:
                    continue
                match = re.search(r"^guid: ([0-9a-f]{32})", head, re.M)
                if match:
                    index[match.group(1)] = meta[:-5]
    return index


def cached_index(project_root, cache_path, refresh):
    """Index of the (read-only) source project, cached because walking a big project is slow.

    The cache stores paths relative to the project root. Use --refresh-index after the source changed.
    """
    if cache_path and os.path.isfile(cache_path) and not refresh:
        with open(cache_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if data.get("root") == project_root:
            return {guid: os.path.join(project_root, rel) for guid, rel in data["index"].items()}
    index = build_index(project_root)
    if cache_path:
        relative = {guid: os.path.relpath(path, project_root) for guid, path in index.items()}
        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump({"root": project_root, "index": relative}, handle)
    return index


def referenced_guids(path):
    """GUIDs referenced by an asset file and by its .meta (own GUID excluded)."""
    found = set()
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXTS and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                found.update(GUID_RE.findall(handle.read()))
        except OSError:
            pass
    meta = path + ".meta"
    if os.path.isfile(meta):
        try:
            with open(meta, "r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    if line.startswith("guid:"):
                        continue
                    found.update(GUID_RE.findall(line))
        except OSError:
            pass
    return found


def shader_includes(path):
    if os.path.splitext(path)[1].lower() not in {".shader", ".hlsl", ".cginc", ".compute"}:
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            return INCLUDE_RE.findall(handle.read())
    except OSError:
        return []


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, help="source Unity project root (contains Assets/)")
    parser.add_argument("--target", help="target Unity project root, to mark what already exists there")
    parser.add_argument("--asset", action="append", required=True, help="root asset path relative to --source (repeatable)")
    parser.add_argument("--dest-prefix", default="Assets/_Art/Imported",
                        help="where missing files go inside --target (source relative path is kept below it)")
    parser.add_argument("--apply", action="store_true", help="copy missing files and .meta into --target")
    parser.add_argument("--allow-scripts", action="store_true", help="also copy .cs/.dll (review first)")
    parser.add_argument("--index-cache", help="JSON file caching the source GUID index (keep it outside any Unity project)")
    parser.add_argument("--refresh-index", action="store_true", help="rebuild the cached source index")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a markdown report")
    args = parser.parse_args()

    source = os.path.abspath(args.source)
    target = os.path.abspath(args.target) if args.target else None
    if args.apply and not target:
        parser.error("--apply needs --target")

    src_index = cached_index(source, args.index_cache, args.refresh_index)
    dst_index = build_index(target) if target else {}

    queue, visited = [], set()
    for rel in args.asset:
        full = os.path.join(source, rel)
        if not os.path.exists(full):
            sys.exit(f"root asset not found: {full}")
        meta = full + ".meta"
        guid = None
        if os.path.isfile(meta):
            with open(meta, "r", encoding="utf-8", errors="ignore") as handle:
                match = re.search(r"^guid: ([0-9a-f]{32})", handle.read(600), re.M)
                guid = match.group(1) if match else None
        if not guid:
            sys.exit(f"no .meta/guid for root asset: {rel}")
        queue.append(guid)

    members, unresolved, warnings = {}, set(), []
    while queue:
        guid = queue.pop()
        if guid in visited:
            continue
        visited.add(guid)
        if guid.startswith(BUILTIN_PREFIXES):
            continue
        path = src_index.get(guid)
        if path is None:
            unresolved.add(guid)
            continue
        members[guid] = path
        if os.path.isdir(path):
            continue
        for ref in referenced_guids(path):
            if ref not in visited:
                queue.append(ref)
        for include in shader_includes(path):
            warnings.append(f"{os.path.relpath(path, source)} includes \"{include}\" (path based; verify it is in the closure)")

    rows = []
    for guid, path in sorted(members.items(), key=lambda kv: kv[1]):
        rel = os.path.relpath(path, source).replace("\\", "/")
        ext = os.path.splitext(path)[1].lower()
        in_package = rel.startswith("Packages/")
        if guid in dst_index:
            same = os.path.relpath(dst_index[guid], target).replace("\\", "/")
            status = "present"
            note = same
        elif target:
            status = "missing"
            note = ""
        else:
            status = "n/a"
            note = ""
        kind = "script" if ext in SCRIPT_EXTS else ("package" if in_package else ("folder" if os.path.isdir(path) else "asset"))
        rows.append({"guid": guid, "path": rel, "kind": kind, "status": status, "target": note})

    copied = []
    if args.apply:
        for row in rows:
            if row["status"] != "missing" or row["kind"] == "folder":
                continue
            if row["kind"] == "script" and not args.allow_scripts:
                continue
            if row["kind"] == "package":
                continue
            src_file = os.path.join(source, row["path"])
            dst_file = os.path.join(target, args.dest_prefix, row["path"])
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            if os.path.exists(dst_file):
                row["target"] = "SKIPPED: destination file exists with a different GUID"
                continue
            shutil.copy2(src_file, dst_file)
            if os.path.isfile(src_file + ".meta"):
                shutil.copy2(src_file + ".meta", dst_file + ".meta")
            row["target"] = os.path.relpath(dst_file, target).replace("\\", "/")
            copied.append(row["path"])

    result = {
        "roots": args.asset,
        "members": rows,
        "unresolved_guids": sorted(unresolved),
        "warnings": sorted(set(warnings)),
        "copied": copied,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return

    counts = {}
    for row in rows:
        counts[(row["kind"], row["status"])] = counts.get((row["kind"], row["status"]), 0) + 1
    print(f"# Closure of {', '.join(args.asset)}\n")
    print(f"{len(rows)} members, {len(unresolved)} unresolved GUIDs, mode: {'APPLY' if args.apply else 'dry-run'}\n")
    print("| kind | status | count |\n|---|---|---|")
    for (kind, status), count in sorted(counts.items()):
        print(f"| {kind} | {status} | {count} |")
    print("\n| path | kind | status | target |\n|---|---|---|---|")
    for row in rows:
        print(f"| {row['path']} | {row['kind']} | {row['status']} | {row['target']} |")
    if unresolved:
        print("\n## Unresolved GUIDs (built-in, registry package, or missing in source)")
        for guid in sorted(unresolved):
            print(f"- {guid}")
    if result["warnings"]:
        print("\n## Warnings")
        for warning in result["warnings"]:
            print(f"- {warning}")
    scripts = [r["path"] for r in rows if r["kind"] == "script" and r["status"] != "present"]
    if scripts:
        print("\n## Scripts not in target (need a framework-aware decision, not blind copy)")
        for script in scripts:
            print(f"- {script}")


if __name__ == "__main__":
    main()
