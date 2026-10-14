"""Estimate the model-visible skill listing cost and generate a skillOverrides snippet for the non-hub skills.

  py -I tools/skill_budget.py [--skills skills] [--hubs tools/hubs.txt] [--context-tokens 200000] [--write docs/skill-overrides.snippet.json]

Claude Code lists every skill name and spends about 1% of the context window on descriptions; over budget it drops descriptions
of the least-invoked skills. Hubs (tools/hubs.txt) keep their descriptions; every other skill can be set to "name-only" so the
set stays routable without eating the budget. Estimate: 4 characters per token. Exit 1 when the hub listing alone exceeds the budget.
"""
import argparse
import json
import os
import re
import sys

CHARS_PER_TOKEN = 4
ENTRY_OVERHEAD = 4   # "- name: " plus newline


def read_skills(skills_dir):
    out = {}
    for d in sorted(os.listdir(skills_dir)):
        p = os.path.join(skills_dir, d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            m = re.search(r"^description:\s*(.+)$", f.read(), re.M)
        out[d] = len(m.group(1).strip()) if m else 0
    return out


def read_hubs(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def cost(skills, hubs):
    hub_chars = sum(len(n) + ENTRY_OVERHEAD + skills[n] for n in hubs if n in skills)
    rest_names = sum(len(n) + ENTRY_OVERHEAD for n in skills if n not in hubs)
    full = sum(len(n) + ENTRY_OVERHEAD + c for n, c in skills.items())
    return hub_chars, rest_names, full


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills", default="skills")
    ap.add_argument("--hubs", default="tools/hubs.txt")
    ap.add_argument("--context-tokens", type=int, default=200000)
    ap.add_argument("--write")
    a = ap.parse_args(argv)
    skills = read_skills(a.skills)
    hubs = read_hubs(a.hubs)
    unknown = [h for h in hubs if h not in skills]
    for u in unknown:
        print("ERROR hub %s is not a skill" % u)
    budget = int(a.context_tokens * CHARS_PER_TOKEN * 0.01)
    hub_chars, rest_names, full = cost(skills, hubs)
    print("skills: %d, hubs: %d, budget: %d chars (1%% of %d tokens)" % (len(skills), len(hubs), budget, a.context_tokens))
    print("all described: %d chars (%d%% of budget)" % (full, full * 100 // budget))
    print("hubs described + others name-only: %d chars (%d%% of budget)" % (hub_chars + rest_names, (hub_chars + rest_names) * 100 // budget))
    if a.write:
        snippet = {"skillOverrides": {n: "name-only" for n in skills if n not in hubs}}
        with open(a.write, "w", encoding="utf-8", newline="\n") as f:
            json.dump(snippet, f, indent=1)
        print("wrote %s (%d name-only overrides); merge into settings.json" % (a.write, len(snippet["skillOverrides"])))
    return 1 if unknown or hub_chars + rest_names > budget else 0


if __name__ == "__main__":
    sys.exit(main())
