"""Grep first-party C# for patterns that break the house rules or hide leftovers. Cheap proxy, never a perf claim.

  py -I qa_banned_api.py --project P [--files Assets/_Game/Scripts/A.cs] [--rules qa/banned-rules.json]

Each rule: id, regex, hot (severity inside Update/FixedUpdate/LateUpdate/OnTrigger*/OnCollision* bodies), other
(severity elsewhere, null = ignore). Editor/ and Tests/ folders are skipped unless a rule sets "editor": true.
Suppress one line with:  // qa-allow: RULE-ID reason   (the reason is mandatory).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qa_common import allowed, base_parser, finding, first_party, read_text, rel, report, select_files  # noqa: E402

DEFAULT_RULES = [
    {"id": "FIND-OBJECT", "regex": r"\bFindObjects?OfType\b|\bFindFirstObjectByType\b|\bFindAnyObjectByType\b|\bGameObject\.Find\(|\.FindWithTag\(", "hot": "error", "other": "warn",
     "msg": "scene search; cache the reference or use the registry"},
    {"id": "GET-COMPONENT-HOT", "regex": r"\bGetComponent(s|InChildren|InParent)?\s*[<(]", "hot": "error", "other": None,
     "msg": "GetComponent in a hot callback; cache it or use the collision registry"},
    {"id": "CAMERA-MAIN", "regex": r"\bCamera\.main\b", "hot": "error", "other": None, "msg": "cache Camera.main"},
    {"id": "NEW-WAIT", "regex": r"\bnew\s+WaitForSeconds\b", "hot": "error", "other": "warn", "msg": "allocates; use UniTask delay or a cached instance"},
    {"id": "PHYSICS-ALLOC", "regex": r"\bPhysics2?D?\.(RaycastAll|SphereCastAll|CapsuleCastAll|OverlapSphere|OverlapBox|OverlapCapsule)\(", "hot": "error", "other": "warn",
     "msg": "allocating physics query; use the NonAlloc variant with a reusable buffer"},
    {"id": "SPAWN-HOT", "regex": r"\b(Instantiate|Destroy)\s*\(", "hot": "error", "other": None, "msg": "spawn/destroy in a hot callback; pool it"},
    {"id": "LOG-HOT", "regex": r"\bDebug\.Log(Warning)?\s*\(", "hot": "warn", "other": None, "msg": "logging in a per-frame callback"},
    {"id": "PLAYERPREFS", "regex": r"\bPlayerPrefs\.", "hot": "error", "other": "error", "msg": "use the DataBlock persistence, not PlayerPrefs"},
    {"id": "TASK-RUN", "regex": r"\bTask\.Run\(", "hot": "error", "other": "error", "msg": "no Task.Run for Unity gameplay work"},
    {"id": "ASYNC-VOID", "regex": r"\basync\s+void\b", "hot": "warn", "other": "warn", "msg": "prefer UniTask; async void only for event entry points"},
    {"id": "SEND-MESSAGE", "regex": r"\bSendMessage(Upwards)?\(|\bBroadcastMessage\(", "hot": "warn", "other": "warn", "msg": "reflection-based messaging"},
    {"id": "RESOURCES-LOAD", "regex": r"\bResources\.Load(All)?\s*[<(]", "hot": "warn", "other": "warn", "msg": "load through the factory, not ad hoc"},
    {"id": "TIMESCALE-SET", "regex": r"\bTime\.timeScale\s*=[^=]", "hot": "warn", "other": "warn", "msg": "timeScale change: only pause/debug code may do this; QA verdicts need timeScale 1",
     "skip_paths": ["/Dev/", "/Debug/", "Pause", "Cheat"]},
    {"id": "LEFTOVER", "regex": r"//\s*(REVERT|TODO\s*QA)\b|\bTEMP_[A-Z_]+\b", "hot": "error", "other": "error", "msg": "temporary test code left in the diff"},
]
HOT_RE = re.compile(r"\b(Update|FixedUpdate|LateUpdate|OnTrigger(Enter|Exit|Stay)2?D?|OnCollision(Enter|Exit|Stay)2?D?|OnTriggerEnterFunc|OnCollisionEnterFunc)\s*\(")


def strip_code(line, in_block):
    """Remove strings and comments so braces and API names inside them are ignored. Returns (code, comment, in_block)."""
    code, i, comment = [], 0, ""
    while i < len(line):
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                return "".join(code), comment, True
            i, in_block = j + 2, False
            continue
        two = line[i:i + 2]
        if two == "/*":
            in_block = True
            i += 2
        elif two == "//":
            comment = line[i:]
            break
        elif line[i] == '"':
            j = i + 1
            while j < len(line) and line[j] != '"':
                j += 2 if line[j] == "\\" else 1
            code.append('""')
            i = j + 1
        else:
            code.append(line[i])
            i += 1
    return "".join(code), comment, in_block


def scan_text(text, relpath, rules):
    out = []
    depth, hot_depth, in_block = 0, None, False
    pending_hot = False
    lines = text.splitlines()
    has_update = bool(re.search(r"\bvoid\s+(Update|FixedUpdate|LateUpdate)\s*\(", text))
    if has_update and re.search(r"^\s*using\s+System\.Linq\s*;", text, re.M):
        n = next(i for i, l in enumerate(lines, 1) if "System.Linq" in l)
        out.append(finding("LINQ-IN-UPDATE-FILE", "warn", relpath, n, "System.Linq in a file with per-frame callbacks; keep it out of hot paths"))
    for n, raw in enumerate(lines, 1):
        code, comment, in_block = strip_code(raw, in_block)
        sig = HOT_RE.search(code)
        if sig:
            tail = code[sig.end():]
            if "=>" not in tail and ("{" in tail or ";" not in tail):
                pending_hot = True
        if pending_hot and not sig and ";" in code and "{" not in code:
            pending_hot = False  # expression body or declaration on the following line
        is_hot = hot_depth is not None or (pending_hot and "{" in code)
        for rule in rules:
            sev = rule["hot"] if is_hot else rule["other"]
            if not sev:
                continue
            target = raw if rule["id"] == "LEFTOVER" else code
            if not re.search(rule["regex"], target):
                continue
            if any(s in relpath for s in rule.get("skip_paths", [])):
                continue
            ok = allowed(raw, rule["id"])
            if ok:
                continue
            msg = rule["msg"] + (" (qa-allow needs a reason)" if ok is False else "")
            out.append(finding(rule["id"], sev, relpath, n, msg))
        for ch in code:
            if ch == "{":
                depth += 1
                if pending_hot and hot_depth is None:
                    hot_depth, pending_hot = depth, False
            elif ch == "}":
                if hot_depth is not None and depth == hot_depth:
                    hot_depth = None
                depth -= 1
    return out


def scan(root, files=None, rules=None, scope="Assets/_Game"):
    rules = rules or DEFAULT_RULES
    scope = first_party(root, scope)
    out = []
    for p in select_files(root, (".cs",), files):
        r = rel(root, p)
        if not r.startswith(scope + "/") or "/Editor/" in "/" + r or "/Tests/" in "/" + r or "/Plugins/" in r:
            continue
        text = read_text(p)
        if text:
            out += scan_text(text, r, rules)
    return out


def main(argv=None):
    ap = base_parser(__doc__)
    ap.add_argument("--rules", help="JSON file with a list of rules replacing the defaults")
    a = ap.parse_args(argv)
    rules = None
    if a.rules:
        with open(a.rules, encoding="utf-8") as f:
            rules = json.load(f)
    return report(scan(a.project, a.files, rules, a.first_party), a.json)


if __name__ == "__main__":
    sys.exit(main())
