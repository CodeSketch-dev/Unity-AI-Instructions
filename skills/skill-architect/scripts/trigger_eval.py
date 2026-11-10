"""Offline activation test: simulates the studio router (skill_router.json, same scoring as ui_gate_reminder.ps1)
on labelled queries. No model call. Proves the description/triggers route the right skill; not that an agent obeys it.

Usage: py -I scripts/trigger_eval.py [queries.json] [--skill <name>]
queries.json: [{"q": "...", "should": ["skill"], "not": ["skill"]}]  (default evals/skill-architect/trigger-queries.json)
A "should" skill must be in the top 12 (the hook limit); a "not" skill must not be in the list.
Run tools/build_skill_router.py first when skills changed (publish.bat does it).
"""
import json
import os
import re
import sys
import unicodedata

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ROUTER = json.load(open(os.path.join(REPO, "skill_router.json"), encoding="utf-8"))


def route(q):
    s = unicodedata.normalize("NFD", q.lower())
    ascii_ = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    extra = ""
    for k, v in ROUTER["vi"].items():
        if re.search(r"(?<![a-z])%s(?![a-z])" % re.escape(k), ascii_):
            extra += " " + v
    tokens = set(re.findall(r"[a-z][a-z0-9]{2,}", ascii_ + " " + extra))
    out = []
    for sk in ROUTER["skills"]:
        sc = 3 * sum(w in tokens for w in sk["w"]) + 3 * sum(w in ascii_ for w in sk["t"]) + sum(w in tokens for w in sk["d"])
        sc -= 3 * sum(w in ascii_ for w in sk.get("x", []))
        if sc >= 3:
            out.append((sc, sk["n"]))
    out.sort(key=lambda t: -t[0])
    return [n for _, n in out[:12]]


def main():
    a = sys.argv[1:]
    only = a[a.index("--skill") + 1] if "--skill" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--skill")]
    path = pos[0] if pos else os.path.join(REPO, "evals", "skill-architect", "trigger-queries.json")
    cases = json.load(open(path, encoding="utf-8"))
    fail = total = 0
    for c in cases:
        if only and only not in c.get("should", []) + c.get("not", []):
            continue
        got = route(c["q"])
        miss = [s for s in c.get("should", []) if s not in got]
        bad = [s for s in c.get("not", []) if s in got]
        total += 1
        if miss or bad:
            fail += 1
            print("FAIL %r missing=%s unwanted=%s got=%s" % (c["q"][:70], miss, bad, got[:5]))
    print("%d/%d trigger cases pass" % (total - fail, total))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
