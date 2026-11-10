"""Inventory + spec-conformance audit of skills (agentskills.io rules). Read-only.

Usage: py -I scripts/inventory.py [--repo <skills-dir>] [--json] [--only <name>]
Scans: the repo skills dir (own, editable), ~/.claude/skills (own), and plugin caches under
~/.claude/plugins (vendor, READ-ONLY: reported, never edited).
Exit 1 when an editable (non-vendor) skill has an error.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
from skill_lint import parse_frontmatter  # noqa: E402

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
HOUSE_KEYS = {"triggers", "not"}
PATH_RE = re.compile(r"(?<![\w/.-])((?:scripts|references|assets)/[\w./-]+\.\w+)")


def check(path, origin):
    sdir = os.path.dirname(path)
    folder = os.path.basename(sdir)
    text = open(path, encoding="utf-8", errors="replace").read()
    fm, body = parse_frontmatter(text)
    res = {"name": folder, "origin": origin, "path": path, "errors": [], "warns": []}
    if fm is None:
        res["errors"].append("frontmatter missing/unterminated")
        return res
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        res["errors"].append("name violates spec (a-z0-9-, <=64, no leading/trailing/double hyphen)")
    if name != folder:
        res["errors"].append("name '%s' != folder" % name)
    if not desc or len(desc) > 1024:
        res["errors"].append("description empty or >1024 chars")
    if desc and not re.search(r"\b(when|use (for|before|after|at|on|to|it|this)|triggers? on)\b", desc.lower()):
        res["warns"].append("description lacks a 'when to use' clause (weak activation)")
    if len(desc) > 300 and origin == "own":
        res["warns"].append("description >300 chars (house limit)")
    unknown = set(fm) - SPEC_KEYS - HOUSE_KEYS
    if unknown:
        res["warns"].append("non-spec frontmatter keys: %s" % ", ".join(sorted(unknown)))
    if len(fm.get("compatibility", "")) > 500:
        res["errors"].append("compatibility >500 chars")
    lines = len(body.splitlines())
    res["body_lines"], res["body_tokens_est"] = lines, len(body) // 4
    if lines >= 500:
        res["errors"].append("body >=500 lines")
    elif res["body_tokens_est"] > 5000:
        res["warns"].append("body ~%d tokens (>5000 recommended max)" % res["body_tokens_est"])
    for rel in sorted(set(PATH_RE.findall(body))):
        if not os.path.exists(os.path.join(sdir, rel)):
            res["warns"].append("mentioned path not in skill folder: %s" % rel)
    return res


def collect(repo):
    out = []
    for p in sorted(glob.glob(os.path.join(repo, "*", "SKILL.md"))):
        out.append(check(p, "own"))
    home = os.path.expanduser("~/.claude")
    for p in sorted(glob.glob(os.path.join(home, "skills", "*", "SKILL.md"))):
        out.append(check(p, "own-user"))
    for p in sorted(glob.glob(os.path.join(home, "plugins", "**", "skills", "*", "SKILL.md"), recursive=True)):
        out.append(check(p, "vendor-readonly"))
    return out


def main():
    a = sys.argv[1:]
    repo = a[a.index("--repo") + 1] if "--repo" in a else os.path.join(REPO, "skills")
    only = a[a.index("--only") + 1] if "--only" in a else None
    rows = [r for r in collect(repo) if not only or r["name"] == only]
    if "--json" in a:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            for m in r["errors"]:
                print("ERROR [%s/%s] %s" % (r["origin"], r["name"], m))
            for m in r["warns"]:
                print("warn  [%s/%s] %s" % (r["origin"], r["name"], m))
    by = {}
    for r in rows:
        c = by.setdefault(r["origin"], [0, 0, 0])
        c[0] += 1
        c[1] += bool(r["errors"])
        c[2] += bool(r["warns"])
    for o, (n, e, w) in by.items():
        print("%s: %d skills, %d with errors, %d with warnings" % (o, n, e, w))
    return 1 if any(r["errors"] for r in rows if r["origin"] != "vendor-readonly") else 0


if __name__ == "__main__":
    sys.exit(main())
