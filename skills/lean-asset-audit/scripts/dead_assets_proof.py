#!/usr/bin/env python
"""Dead-asset proof pack builder. READ-ONLY on the project; writes only CSV/MD into --out.

Usage (stdlib only; run with -I, from a folder that is not untrusted):
  python -I dead_assets_proof.py --root <unity project> --out <report dir> \
      [--cand NAME=Assets/rel/folder ...] [--scenes] [--duplicates] [--packages] \
      [--derived Assets/rel/folder ...] [--vendor /fragment/ ...] [--min-dup-bytes 10000]

Categories (each becomes one CSV):
  --cand NAME=folder   every non-.meta file under the folder is a candidate
  --scenes             every .unity file
  --duplicates         same file name + same size + same sha1 (>= --min-dup-bytes)
  --derived folder     derived/generated index inside Assets: never DEAD-PROVEN, only LIKELY-DEAD (untrack + ignore)
  --packages           manifest packages with no using/asmdef/asset use (static check only, never DEAD-PROVEN)

Proof model
  * guid index: every .meta under Assets -> guid -> asset path.
  * reference index: every text-serialized file (scenes, prefabs, assets, materials, controllers, metas,
    asmdef, json, ProjectSettings, Packages/manifest) is scanned for `guid: <32hex>` / `GUID:<32hex>`.
    The asset's own .meta is ignored. Referrers that are themselves DEAD-PROVEN are ignored in later
    passes (fixpoint, max 4 passes), so chains of dead assets are found.
  * binary-serialized scenes/prefabs/assets (no %YAML header) cannot be parsed: for every candidate that would
    otherwise be DEAD-PROVEN the raw bytes are searched for the guid in 3 byte layouts. A hit -> UNKNOWN.
    (The little-endian nibble-reversed layout was the one that matched when validated on a real project:
    validate on yours with a GUID you know is used by a binary scene before trusting a miss.)
  * string references: every string literal in every .cs; exact name / name.ext / path matches -> UNKNOWN.
    A prefix literal ("Ladder_") in Editor code only is noted but allowed, in runtime code -> UNKNOWN.
  * Resources / StreamingAssets / Plugins / Editor Default Resources / Gizmos and build-settings scenes -> KEEP.
  * An ancestor folder whose guid is referenced from outside (Addressables folder entry, SpriteAtlas) -> UNKNOWN.
Verdicts: DEAD-PROVEN (safe to delete after the Editor re-check), LIKELY-DEAD (needs a human), KEEP, UNKNOWN.
"""
import argparse, csv, hashlib, json, os, re, sys, time
from collections import defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--cand", action="append", default=[], help="NAME=Assets/relative/folder")
ap.add_argument("--derived", action="append", default=[])
ap.add_argument("--vendor", action="append", default=[], help="lower-case path fragment, e.g. /packages fx/")
ap.add_argument("--scenes", action="store_true")
ap.add_argument("--duplicates", action="store_true")
ap.add_argument("--packages", action="store_true")
ap.add_argument("--min-dup-bytes", type=int, default=10000)
args = ap.parse_args()

ROOT = Path(args.root).resolve()
OUT = Path(args.out).resolve()
ASSETS = ROOT / "Assets"
OUT.mkdir(parents=True, exist_ok=True)

TEXT_EXT = {".unity", ".prefab", ".asset", ".mat", ".controller", ".anim", ".overridecontroller", ".mixer",
            ".shadergraph", ".shadersubgraph", ".meta", ".preset", ".lighting", ".flare", ".spriteatlas",
            ".spriteatlasv2", ".playable", ".rendertexture", ".physicmaterial", ".physicsmaterial2d",
            ".guiskin", ".cubemap", ".terrainlayer", ".brush", ".mask", ".inputactions", ".asmdef",
            ".asmref", ".json", ".uxml", ".uss", ".tss", ".vfx", ".shadervariants", ".signal",
            ".fontsettings", ".giparams", ".colors", ".curves", ".gradients"}
GUID_RE = re.compile(rb"(?:guid:\s*|GUID:)([0-9a-fA-F]{32})", re.I)
PATH_RE = re.compile(rb"Assets/[A-Za-z0-9_ ./\-]+\.[A-Za-z0-9]+")
LIT_RE = re.compile(r'"([^"\\\n]{3,200})"')
PROTECT = ("/resources/", "/streamingassets/", "/editor default resources/", "/plugins/", "/gizmos/")
VENDOR_HINT = tuple(["/plugins/", "/packages fx/", "/packages required/", "/thirdparty/", "/textmesh pro/"]
                    + [v.lower() for v in args.vendor])


def rel(p):
    return p.relative_to(ROOT).as_posix()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# 1. walk
all_files = []
for dp, dn, fn in os.walk(ASSETS):
    for f in fn:
        p = Path(dp) / f
        try:
            all_files.append((p, p.stat().st_size))
        except OSError:
            pass
log("files under Assets:", len(all_files))

guid2path, path2guid = {}, {}
for p, _ in all_files:
    if p.suffix == ".meta":
        try:
            head = p.read_bytes()[:400]
        except OSError:
            continue
        m = re.search(rb"guid:\s*([0-9a-f]{32})", head)
        if m:
            g = m.group(1).decode()
            a = rel(p)[:-5]
            guid2path[g] = a
            path2guid[a] = g

# 2. reference index
refs = defaultdict(set)
path_refs = defaultdict(set)
binary_files = []
scan = [(p, s) for p, s in all_files if p.suffix.lower() in TEXT_EXT]
for extra in (ROOT / "ProjectSettings", ROOT / "Packages"):
    if extra.exists():
        for dp, dn, fn in os.walk(extra):
            for f in fn:
                p = Path(dp) / f
                if p.suffix.lower() in (".asset", ".json", ".asmdef", ".meta") or f == "manifest.json":
                    scan.append((p, p.stat().st_size))
for p, s in scan:
    try:
        data = p.read_bytes()
    except OSError:
        continue
    if p.suffix.lower() in (".unity", ".prefab", ".asset") and not data.startswith(b"%YAML"):
        binary_files.append(rel(p))
        continue
    r = rel(p)
    referrer = r[:-5] if r.endswith(".meta") else r
    for m in GUID_RE.finditer(data):
        refs[m.group(1).decode().lower()].add(referrer)
    if s < 20_000_000:
        for m in PATH_RE.finditer(data):
            path_refs[m.group(0).decode("utf8", "ignore")].add(referrer)
log("guids referenced:", len(refs), "binary-serialized files:", len(binary_files))

# 3. string literals in code
lit_index = defaultdict(list)
prefix_lits = []
cs_count = 0
for p, _ in all_files:
    if p.suffix != ".cs":
        continue
    cs_count += 1
    try:
        txt = p.read_text(encoding="utf8", errors="ignore")
    except OSError:
        continue
    r = rel(p)
    ed = "/editor/" in r.lower()
    for m in LIT_RE.finditer(txt):
        lit = m.group(1)
        last = lit.replace("\\", "/").rstrip("/").split("/")[-1]
        key = os.path.splitext(last)[0].lower()
        lit_index[key].append((lit, r, ed))
        if len(lit) >= 5 and (lit.endswith("_") or lit.endswith("/")):
            prefix_lits.append((lit, r, ed))
log("cs files:", cs_count)

build_scenes = set()
ebs = ROOT / "ProjectSettings" / "EditorBuildSettings.asset"
if ebs.exists():
    t = ebs.read_text(encoding="utf8", errors="ignore")
    build_scenes = set(re.findall(r"path:\s*(Assets/[^\n]+?\.unity)", t))
    for g in re.findall(r"guid:\s*([0-9a-f]{32})", t):
        if g in guid2path:
            build_scenes.add(guid2path[g])
log("build settings scenes:", len(build_scenes))


class Rec:
    def __init__(self, path, size, cat):
        self.path, self.size, self.cat = path, size, cat
        self.guid = path2guid.get(path, "")
        self.notes, self.verdict, self.group = [], "UNKNOWN", None
        self.vendor = any(h in path.lower() for h in VENDOR_HINT)


recs = []
size_of = {rel(p): s for p, s in all_files}

for spec in args.cand:
    name, _, folder = spec.partition("=")
    folder = folder.strip("/") + "/"
    for p, s in all_files:
        r = rel(p)
        if r.startswith(folder) and p.suffix != ".meta":
            recs.append(Rec(r, s, name))
for folder in args.derived:
    folder = folder.strip("/") + "/"
    for p, s in all_files:
        r = rel(p)
        if r.startswith(folder) and p.suffix != ".meta":
            recs.append(Rec(r, s, "derived"))
if args.scenes:
    for p, s in all_files:
        if p.suffix == ".unity":
            recs.append(Rec(rel(p), s, "scenes"))
if args.duplicates:
    skip = {".meta", ".cs", ".dll", ".asmdef", ".shader", ".cginc", ".hlsl", ".so", ".a", ".aar", ".jar", ".json", ".txt", ".md", ".pdf"}
    derived_prefix = tuple(d.strip("/") + "/" for d in args.derived)
    by_ns = defaultdict(list)
    for p, s in all_files:
        if s >= args.min_dup_bytes and p.suffix.lower() not in skip and not rel(p).startswith(derived_prefix):
            by_ns[(p.name, s)].append(p)
    groups = 0
    for (name, s), ps in by_ns.items():
        if len(ps) < 2:
            continue
        hs = defaultdict(list)
        for p in ps:
            hs[hashlib.sha1(p.read_bytes()).hexdigest()].append(p)
        for h, same in hs.items():
            if len(same) > 1:
                groups += 1
                for p in same:
                    r = Rec(rel(p), s, "duplicates")
                    r.group = h[:10]
                    recs.append(r)
    log("duplicate groups:", groups)

dead_set = set()


def ancestors(path):
    parts = path.split("/")
    for i in range(len(parts) - 1, 1, -1):
        yield "/".join(parts[:i])


def live_refs(rec):
    out = set()
    for x in refs.get(rec.guid, ()):
        if x != rec.path and x not in dead_set:
            out.add(x)
    for x in path_refs.get(rec.path, ()):
        if x != rec.path and x not in dead_set:
            out.add(x)
    return out


def str_hits(rec):
    name = os.path.basename(rec.path)
    stem = os.path.splitext(name)[0]
    hits = []
    for lit, f, ed in lit_index.get(stem.lower(), ()):
        l = lit.replace("\\", "/")
        last = l.rstrip("/").split("/")[-1]
        if last == name or last == stem or l == rec.path or rec.path in l or l.endswith("/" + rec.path.split("Assets/", 1)[-1]):
            hits.append((lit, f, ed))
    pre = [(lit, f, ed) for lit, f, ed in prefix_lits if stem.startswith(lit) or name.startswith(lit)]
    return hits, pre


def layouts(g):
    g = g.lower()
    groups = [g[i:i + 8] for i in range(0, 32, 8)]
    a = bytes.fromhex(g)
    rev = [x[::-1] for x in groups]
    b = bytes.fromhex("".join(rev))
    c = b"".join(bytes.fromhex(x)[::-1] for x in rev)
    return (a, b, c)


blobs = {}
for bf in binary_files:
    try:
        blobs[bf] = (ROOT / bf).read_bytes()
    except OSError:
        pass


def binary_hit(g):
    if not g or not blobs:
        return None
    ls = layouts(g)
    for bf, blob in blobs.items():
        if any(l in blob for l in ls):
            return bf
    return None


def evaluate(rec):
    rec.notes = []
    low = "/" + rec.path.lower()
    lr = live_refs(rec)
    ignored = len([x for x in refs.get(rec.guid, ()) if x in dead_set])
    if ignored:
        rec.notes.append(f"{ignored} referrer(s) ignored because they are DEAD-PROVEN themselves")
    if lr:
        rec.notes.append("referenced by: " + "; ".join(sorted(lr)[:3]) + (" ..." if len(lr) > 3 else ""))
        rec.verdict = "KEEP"
        return
    if rec.path in build_scenes:
        rec.notes.append("in EditorBuildSettings scenes")
        rec.verdict = "KEEP"
        return
    for pt in PROTECT:
        if pt in low + "/":
            rec.notes.append(f"protected folder {pt} (loadable by name/path at runtime)")
            rec.verdict = "KEEP"
            return
    if not rec.guid:
        rec.notes.append("no .meta guid found")
        rec.verdict = "UNKNOWN"
        return
    for anc in ancestors(rec.path):
        ag = path2guid.get(anc)
        if ag:
            outside = [x for x in refs.get(ag, ()) if not x.startswith(anc + "/") and x != anc]
            if outside:
                rec.notes.append(f"ancestor folder {anc} referenced by {sorted(outside)[0]}")
                rec.verdict = "UNKNOWN"
                return
    hits, pre = str_hits(rec)
    if hits:
        l, f, ed = hits[0]
        rec.notes.append(f'string literal "{l}" in {f}{" (Editor)" if ed else " (runtime)"}')
        rec.verdict = "UNKNOWN"
        return
    rt = [x for x in pre if not x[2]]
    if rt:
        rec.notes.append(f'runtime prefix literal "{rt[0][0]}" in {rt[0][1]}')
        rec.verdict = "UNKNOWN"
        return
    if pre:
        rec.notes.append(f'editor-only prefix literal "{pre[0][0]}" in {pre[0][1]} (a builder regenerates it)')
    rec.notes.append("0 guid refs in scenes/prefabs/assets/materials/metas/ProjectSettings; no string/path ref in .cs; not in Resources/build settings")
    rec.verdict = "DEAD-PROVEN"


for it in range(4):
    before = set(dead_set)
    for r in recs:
        evaluate(r)
        if r.verdict == "DEAD-PROVEN":
            if r.cat == "derived":
                r.verdict = "LIKELY-DEAD"
                r.notes.append("derived index: untrack + gitignore, do NOT delete from disk")
            elif r.vendor and r.cat in ("scenes", "duplicates"):
                r.verdict = "LIKELY-DEAD"
                r.notes.append("inside a vendor folder: unreferenced but vendor-owned, owner decision")
    for r in recs:
        if r.verdict == "DEAD-PROVEN":
            bh = binary_hit(r.guid)
            if bh:
                r.verdict = "UNKNOWN"
                r.notes.append(f"guid bytes found inside binary-serialized {bh}")
    groups = defaultdict(list)
    for r in recs:
        if r.cat == "duplicates":
            groups[r.group].append(r)
    for gid, members in groups.items():
        alive = [m for m in members if m.verdict in ("KEEP", "UNKNOWN")]
        for m in members:
            if m.verdict != "DEAD-PROVEN":
                continue
            if alive:
                m.notes.append("identical copy kept: " + alive[0].path)
            else:
                m.verdict = "LIKELY-DEAD"
                m.notes.append("whole duplicate group unreferenced: keep one canonical copy")
    dead_set = {r.path for r in recs if r.verdict == "DEAD-PROVEN"}
    log(f"pass {it}: dead-proven {len(dead_set)}")
    if dead_set == before:
        break

rank = {"KEEP": 0, "UNKNOWN": 1, "LIKELY-DEAD": 2, "DEAD-PROVEN": 3}
best = {}
for r in recs:
    if r.path not in best or rank[r.verdict] < rank[best[r.path]]:
        best[r.path] = r.verdict
for r in recs:
    if r.verdict != best[r.path]:
        r.notes.append(f"also listed in another category with stricter verdict {best[r.path]}")
        r.verdict = best[r.path]
dead_set = {r.path for r in recs if r.verdict == "DEAD-PROVEN"}

# packages
pkg_rows = []
if args.packages:
    manifest = ROOT / "Packages" / "manifest.json"
    deps = json.loads(manifest.read_text(encoding="utf8"))["dependencies"]
    cache = ROOT / "Library" / "PackageCache"
    pkg_dirs = {d.name.split("@")[0]: d for d in cache.iterdir()} if cache.exists() else {}
    required_by = defaultdict(list)
    for name, d in pkg_dirs.items():
        pj = d / "package.json"
        if pj.exists():
            try:
                for dep in json.loads(pj.read_text(encoding="utf8")).get("dependencies", {}):
                    required_by[dep].append(name)
            except Exception:
                pass
    using_set, asm_refs = set(), set()
    using_re = re.compile(r"^\s*using\s+(?:static\s+)?(?:\w+\s*=\s*)?([\w.]+)\s*;", re.M)
    ns_re = re.compile(r"^\s*namespace\s+([\w.]+)", re.M)
    for p, _ in all_files:
        if p.suffix == ".cs":
            try:
                using_set.update(m.group(1) for m in using_re.finditer(p.read_text(encoding="utf8", errors="ignore")))
            except OSError:
                pass
        elif p.suffix == ".asmdef":
            try:
                asm_refs.update(x for x in json.loads(p.read_text(encoding="utf8-sig")).get("references", []) if not x.startswith("GUID:"))
            except Exception:
                pass
    for name, ver in sorted(deps.items()):
        row = {"path": f"Packages/manifest.json:{name} = {ver}", "size": 0, "refs": 0, "notes": [], "verdict": "UNKNOWN"}
        d = pkg_dirs.get(name)
        if name.startswith("com.unity.modules."):
            row.update(verdict="KEEP", notes=["built-in module (disable only after checking the scenes use no such component)"])
        elif d is None:
            row["notes"].append("not in Library/PackageCache (cannot prove)")
        else:
            nss, asms, pguids, size = set(), set(), set(), 0
            for dp, dn, fn in os.walk(d):
                for f in fn:
                    fp = Path(dp) / f
                    try:
                        size += fp.stat().st_size
                    except OSError:
                        pass
                    try:
                        if f.endswith(".cs"):
                            nss.update(m.group(1) for m in ns_re.finditer(fp.read_text(encoding="utf8", errors="ignore")))
                        elif f.endswith(".asmdef"):
                            asms.add(json.loads(fp.read_text(encoding="utf8-sig")).get("name", ""))
                        elif f.endswith(".meta"):
                            m = re.search(rb"guid:\s*([0-9a-f]{32})", fp.read_bytes()[:300])
                            if m:
                                pguids.add(m.group(1).decode())
                    except Exception:
                        pass
            use_ns = sorted(n for n in nss if n in using_set or any(u.startswith(n + ".") for u in using_set))
            use_asm = sorted(a for a in asms if a and a in asm_refs)
            use_guid = sorted({x for g in pguids for x in refs.get(g, ()) if x.startswith(("Assets/", "ProjectSettings"))})
            rb = [x for x in required_by.get(name, []) if x != name]
            row["size"] = size
            row["refs"] = len(use_ns) + len(use_asm) + len(use_guid)
            row["notes"].append(f"using-hits {len(use_ns)} {use_ns[:3]}; asmdef-ref hits {use_asm[:3]}; asset/guid referrers {len(use_guid)} {use_guid[:2]}")
            if rb:
                row["notes"].append("dependency of: " + ", ".join(rb[:4]))
            if row["refs"] or rb:
                row["verdict"] = "KEEP"
            elif not nss:
                row["notes"].append("precompiled / no .cs namespaces: a static scan cannot prove it unused")
            else:
                row["verdict"] = "LIKELY-DEAD"
                row["notes"].append("no using/asmdef/asset use found (static; transitive or native use is not provable)")
        pkg_rows.append(row)

# outputs
HDR = ["path", "size_bytes", "guid", "live_referrers", "proof_notes", "verdict"]
MB = 1024 * 1024
stats = {}


def row_of(r):
    return [r.path, r.size, r.guid, len(live_refs(r)), " | ".join(r.notes), r.verdict]


for cat in sorted({r.cat for r in recs}):
    rows = sorted((row_of(r) for r in recs if r.cat == cat), key=lambda x: (x[5], x[0]))
    with open(OUT / f"cat_{cat}.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(rows)
    st = defaultdict(lambda: [0, 0])
    for x in rows:
        st[x[5]][0] += 1
        st[x[5]][1] += x[1]
    stats[cat] = dict(st)
if pkg_rows:
    with open(OUT / "cat_packages.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        st = defaultdict(lambda: [0, 0])
        for r in sorted(pkg_rows, key=lambda r: (r["verdict"], r["path"])):
            w.writerow([r["path"], r["size"], "", r["refs"], " | ".join(r["notes"]), r["verdict"]])
            st[r["verdict"]][0] += 1
            st[r["verdict"]][1] += r["size"]
        stats["packages"] = dict(st)
seen = set()
with open(OUT / "dead_proven.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f)
    w.writerow(HDR + ["category"])
    for r in sorted(recs, key=lambda r: (r.cat, r.path)):
        if r.verdict == "DEAD-PROVEN" and r.path not in seen:
            seen.add(r.path)
            w.writerow(row_of(r) + [r.cat])

dp_size = sum(size_of.get(p, 0) for p in seen)
lines = ["# Dead-asset proof pack - summary", "",
         f"- files under Assets: {len(all_files)}; guids indexed: {len(guid2path)}; guids referenced: {len(refs)}; .cs scanned: {cs_count}",
         f"- build-settings scenes: {len(build_scenes)}; binary-serialized scene/prefab/asset files (byte-scanned): {len(binary_files)}", "",
         "| Category | Verdict | Count | MB |", "|---|---|---|---|"]
for cat, st in stats.items():
    for v in ("DEAD-PROVEN", "LIKELY-DEAD", "UNKNOWN", "KEEP"):
        if v in st:
            lines.append(f"| {cat} | {v} | {st[v][0]} | {st[v][1] / MB:.1f} |")
lines += ["", f"**DEAD-PROVEN unique files (dead_proven.csv): {len(seen)} files, {dp_size / MB:.1f} MB**", "",
          "Duplicates are identical sha1 + same name; a surviving copy is always kept. Derived folders are never DEAD-PROVEN. "
          "Packages are never DEAD-PROVEN (native or transitive use is not provable statically).",
          "Next: re-run right before deleting, delete through an Editor tool that logs a dry run first, then compile and open every build scene."]
(OUT / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf8")
log("done; dead-proven unique:", len(seen), f"{dp_size / MB:.1f} MB")
