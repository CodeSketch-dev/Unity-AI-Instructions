#!/usr/bin/env python
"""Layout audit for the studio folder/naming standard. READ-ONLY. Stdlib only.

python -I layout_audit.py --root <unity project> [--game Assets/_Game] [--namespace Game] [--max-lines 400]
Checks (each prints PASS/FAIL with the offenders, first 15):
  F02 _Game top-level folders are the allowed buckets      F05 Scripts buckets
  F08 Resources holds no prefabs                           F10 no scratch folders / stray files in Assets
  N01 asmdef policy (first-party asmdefs only with references; test asmdefs exist)
  N03 namespace share      N04 file name == first type    N05 one top-level type per file
  N06 prefix drift (Evt_, _Factory suffix, project-initial variants)   N09 `using UnityEditor` in runtime code without #if
  H02 files over --max-lines                                H08 forbidden words in asset names (copy, backup, final, _old, New )
Exit code 1 when any FAIL. Pair with the unity-script-migration style_audit.py for per-feature counts.
"""
import argparse, os, re, sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--game", default="Assets/_Game")
ap.add_argument("--namespace", default="Game")
ap.add_argument("--max-lines", type=int, default=400)
a = ap.parse_args()
ROOT = Path(a.root).resolve()
GAME = ROOT / a.game
SCRIPTS = GAME / "Scripts"
ALLOWED_TOP = {"Audios", "Configs", "Fonts", "Localization", "Materials", "Prefabs", "Resources", "Scenes", "Scripts",
               "Textures", "Settings", "Tests", "Animations", "Shaders", "Meshes"}
ALLOWED_BUCKETS = {"Core", "Data", "Editor", "Event", "Factory", "Logic", "Utilities"}
fails = 0


def report(code, title, bad, limit=15):
    global fails
    status = "PASS" if not bad else "FAIL"
    if bad:
        fails += 1
    print(f"[{status}] {code} {title}" + (f" ({len(bad)})" if bad else ""))
    for b in bad[:limit]:
        print("    " + str(b))


def cs_files(base):
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if not d.startswith(".")]
        for f in fn:
            if f.endswith(".cs"):
                yield Path(dp) / f


def rel(p):
    return p.relative_to(ROOT).as_posix()


def is_editor(p):
    return "/Editor/" in rel(p) or "/Tests/" in rel(p)


if GAME.exists():
    report("F02", "Assets/_Game top-level folders", [d.name for d in GAME.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name not in ALLOWED_TOP])
if SCRIPTS.exists():
    report("F05", "Scripts buckets", [d.name for d in SCRIPTS.iterdir() if d.is_dir() and not d.name.startswith(".") and d.name not in ALLOWED_BUCKETS])
res = []
for dp, dn, fn in os.walk(GAME / "Resources") if (GAME / "Resources").exists() else []:
    res += [rel(Path(dp) / f) for f in fn if f.endswith(".prefab")]
report("F08", "no prefabs in Resources", res)
scratch = [n for n in os.listdir(ROOT / "Assets") if re.match(r"(?i)(_?tmp|backup|scratch|readme\.asset|projectsettings$|.*\.(png|jpg)$)", n) and not n.endswith(".meta")]
report("F10", "scratch folders / stray files in Assets root", scratch)

asm = [p for p in (ROOT / "Assets").rglob("*.asmdef") if a.game.split("/")[-1] in p.parts]
bad_asm, test_asm = [], 0
for p in asm:
    txt = p.read_text(encoding="utf-8-sig", errors="ignore")
    if "Tests" in p.parts or '"testAssemblies"' in txt or "UNITY_INCLUDE_TESTS" in txt:
        test_asm += 1
        continue
    if re.search(r'"references"\s*:\s*\[\s*\]', txt):
        bad_asm.append(rel(p) + " (empty references: a runtime asmdef needs a real reference list, otherwise use the default assemblies)")
report("N01", "first-party runtime asmdefs have real references", bad_asm)
report("N01b", "test asmdefs exist (EditMode + PlayMode)", [] if test_asm >= 2 else [f"found {test_asm} test asmdefs"])

ns_total = ns_ok = 0
mismatch, multi, drift, editor_leak, long_files, badnames = [], [], [], [], [], []
type_re = re.compile(r"^\s*(?:public\s+|internal\s+)?(?:static\s+|abstract\s+|sealed\s+|partial\s+)*(class|struct|enum|interface)\s+(\w+)", re.M)
for p in cs_files(SCRIPTS if SCRIPTS.exists() else GAME):
    txt = p.read_text(encoding="utf-8-sig", errors="ignore")
    r = rel(p)
    ns_total += 1
    if re.search(r"^\s*namespace\s+" + re.escape(a.namespace) + r"\b", txt, re.M):
        ns_ok += 1
    # top-level types: depth 0 or inside a single namespace block
    types, depth = [], 0
    for line in txt.splitlines():
        s = line.strip()
        m = type_re.match(line)
        if m and depth <= (1 if "namespace" in txt else 0) and not s.startswith("//"):
            types.append(m.group(2))
        depth += line.count("{") - line.count("}")
    stem = p.stem.split(".")[0]
    if types and stem not in types and not any(t.split("`")[0] == stem for t in types):
        mismatch.append(f"{r} -> {types[0]}")
    if len(types) > 1:
        multi.append(f"{r} ({len(types)} types)")
    for t in types:
        if re.match(r"(Evt_|.*_Factory$|.*(Kt|KT)_)", t):
            drift.append(f"{r}: {t}")
    if "using UnityEditor" in txt and not is_editor(p):
        # allowed when every UnityEditor use is inside #if UNITY_EDITOR
        first = txt.index("using UnityEditor")
        pre = txt[:first]
        if pre.count("#if UNITY_EDITOR") <= pre.count("#endif"):
            editor_leak.append(r)
    n = txt.count("\n") + 1
    if n > a.max_lines:
        long_files.append(f"{r} ({n} lines)")
share = (100.0 * ns_ok / ns_total) if ns_total else 0
report("N03", f"namespace {a.namespace} share {share:.0f}% (target >= 95%)", [] if share >= 95 else [f"{ns_total - ns_ok} files outside"])
report("N04", "file name == first type", mismatch)
report("N05", "one top-level type per file", multi)
report("N06", "prefix drift (Evt_, _Factory suffix, initials variants)", drift)
report("N09", "UnityEditor used in runtime code without #if UNITY_EDITOR", editor_leak)
report("H02", f"files over {a.max_lines} lines (document exceptions)", long_files)
for dp, dn, fn in os.walk(GAME):
    for f in fn + dn:
        if re.search(r"(?i)(\bcopy\b|backup|_final|_old\b|^new[ _]|\(\d+\))", f) and not f.endswith(".meta"):
            badnames.append(rel(Path(dp) / f))
report("H08", "forbidden words in names", badnames)
print("\nfailures:", fails)
sys.exit(1 if fails else 0)
