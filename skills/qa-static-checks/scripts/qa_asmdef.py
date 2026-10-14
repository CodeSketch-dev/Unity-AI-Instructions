"""Assembly definition rules and the UnityEditor-leak check that breaks player builds (stdlib only).

  py -I qa_asmdef.py --project P [--files ...]

ASMDEF-JSON       asmdef does not parse
ASMDEF-CYCLE      reference cycle
ASMDEF-EDITOR     assembly named *.Editor (or using UnityEditor) without includePlatforms [Editor]
ASMDEF-TESTS      test assembly without defineConstraints UNITY_INCLUDE_TESTS
EDITOR-LEAK       runtime .cs uses 'using UnityEditor' outside an Editor folder/asmdef and outside #if UNITY_EDITOR
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa_common import base_parser, finding, first_party, read_text, rel, report, select_files, walk  # noqa: E402

GUID_RE = re.compile(r"^guid:\s*([0-9a-f]{32})", re.M)


def load_asmdefs(root):
    defs, by_guid = {}, {}
    for p in walk(root, (".asmdef",)):
        t = read_text(p)
        try:
            d = json.loads(t)
        except (ValueError, TypeError):
            defs[p] = None
            continue
        defs[p] = d
        m = GUID_RE.search(read_text(p + ".meta") or "")
        if m:
            by_guid[m.group(1)] = d.get("name")
    return defs, by_guid


def resolve(refs, by_guid):
    out = []
    for r in refs:
        out.append(by_guid.get(r[5:], r) if r.startswith("GUID:") else r)
    return out


def find_cycle(graph):
    state, stack = {}, []

    def visit(n):
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, ()):
            if state.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if m not in state:
                c = visit(m)
                if c:
                    return c
        stack.pop()
        state[n] = 2
        return None

    for n in list(graph):
        if n not in state:
            c = visit(n)
            if c:
                return c
    return None


def asmdef_dirs(defs):
    return [(os.path.dirname(p), d) for p, d in defs.items() if d]


def editor_only(d):
    return d is not None and d.get("includePlatforms") == ["Editor"]


def scan(root, files=None, scope="Assets/_Game"):
    scope = first_party(root, scope)
    out = []
    defs, by_guid = load_asmdefs(root)
    graph = {}
    for p, d in defs.items():
        r = rel(root, p)
        if d is None:
            out.append(finding("ASMDEF-JSON", "error", r, 1, "asmdef is not valid JSON"))
            continue
        name = d.get("name", "")
        refs = resolve(d.get("references", []), by_guid)
        graph[name] = refs
        if name.endswith(".Editor") and not editor_only(d):
            out.append(finding("ASMDEF-EDITOR", "error", r, 1, "%s is an editor assembly without includePlatforms [Editor]" % name))
        is_test = name.endswith(".Tests") or "TestAssemblies" in d.get("optionalUnityReferences", [])
        if is_test and "UnityEngine.TestRunner" in refs and "UNITY_INCLUDE_TESTS" not in d.get("defineConstraints", []):
            out.append(finding("ASMDEF-TESTS", "error", r, 1, "test assembly without defineConstraints UNITY_INCLUDE_TESTS"))
        if "UnityEditor" in refs and not editor_only(d) and not name.endswith("Tests"):
            out.append(finding("ASMDEF-EDITOR", "error", r, 1, "runtime assembly references UnityEditor"))
    cyc = find_cycle(graph)
    if cyc:
        out.append(finding("ASMDEF-CYCLE", "error", "Assets", 1, "reference cycle: " + " -> ".join(cyc)))
    dirs = asmdef_dirs(defs)
    for p in select_files(root, (".cs",), files, subdirs=("Assets",)):
        r = rel(root, p)
        if not r.startswith(scope + "/") or "/Editor/" in "/" + r or "/Tests/" in "/" + r or "/Plugins/" in r:
            continue
        owner = max((dd for dd in dirs if p.startswith(dd[0] + os.sep)), key=lambda x: len(x[0]), default=None)
        if owner and editor_only(owner[1]):
            continue
        text = read_text(p) or ""
        m = re.search(r"^\s*using\s+UnityEditor\b", text, re.M)
        if not m:
            continue
        head = text[:m.start()]
        if head.count("#if UNITY_EDITOR") > head.count("#endif"):
            continue
        out.append(finding("EDITOR-LEAK", "error", r, head.count("\n") + 1, "using UnityEditor outside an Editor folder or #if UNITY_EDITOR breaks player builds"))
    return out


def main(argv=None):
    a = base_parser(__doc__).parse_args(argv)
    return report(scan(a.project, a.files, a.first_party), a.json)


if __name__ == "__main__":
    sys.exit(main())
