"""Skill test-fix-retest helper: score one skill, snapshot a baseline, decide keep-or-revert after an edit.

Usage (run with py -I):
  skill_loop.py score    <skills-dir> <name>            print the score JSON for one skill
  skill_loop.py snapshot <skills-dir> <name>            save SKILL.md + score as the baseline (.skill-loop/<name>/)
  skill_loop.py decide   <skills-dir> <name> [--apply]  compare with the baseline: KEEP when score >= baseline, else REVERT
                                                        (--apply restores the baseline file on REVERT)

Score (0-100) = 100 minus 25 per lint error, 5 per own lint warning (trigger collisions with other skills excluded), 10 per
failed spec check. Spec file (optional): <skills-dir>/../evals/skill-specs/<name>.json
  {"must_contain": ["regex", ...], "must_not_contain": ["regex", ...], "triggers_any": ["word", ...]}
A spec pass proves the written instructions cover the cases; it does not prove an agent follows them. Behaviour runs live in
the tools/evals/ trigger graders and the skill-evals harness (with-skill versus without-skill runs).
"""
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_lint  # noqa: E402


def spec_path(skills_dir, name):
    return os.path.join(os.path.dirname(os.path.abspath(skills_dir)), "tools", "evals", "skill-specs", name + ".json")


def load_spec(skills_dir, name):
    p = spec_path(skills_dir, name)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def spec_failures(text, fm, spec):
    out = []
    if not spec:
        return out
    for rx in spec.get("must_contain", []):
        if not re.search(rx, text, re.I | re.M):
            out.append("missing: " + rx)
    for rx in spec.get("must_not_contain", []):
        if re.search(rx, text, re.I | re.M):
            out.append("forbidden: " + rx)
    words = spec.get("triggers_any")
    if words:
        hay = (fm.get("triggers", "") + " " + fm.get("description", "")).lower()
        if not any(w.lower() in hay for w in words):
            out.append("no trigger/description word from " + ",".join(words))
    return out


def score(skills_dir, name):
    path = os.path.join(skills_dir, name, "SKILL.md")
    if not os.path.isfile(path):
        return {"skill": name, "score": 0, "errors": ["SKILL.md missing"], "warnings": [], "spec": []}
    findings = [f for f in skill_lint.lint_dir(skills_dir) if name in f.skill.split(",")]
    errors = ["%s: %s" % (f.code, f.message) for f in findings if f.severity == "error"]
    warns = ["%s: %s" % (f.code, f.message) for f in findings if f.severity == "warn" and f.code != "trigger-collision"]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, _ = skill_lint.parse_frontmatter(text)
    spec = spec_failures(text, fm or {}, load_spec(skills_dir, name))
    s = max(0, 100 - 25 * len(errors) - 5 * len(warns) - 10 * len(spec))
    return {"skill": name, "score": s, "errors": errors, "warnings": warns, "spec": spec}


def base_dir(skills_dir, name):
    return os.path.join(os.path.dirname(os.path.abspath(skills_dir)), ".skill-loop", name)


def snapshot(skills_dir, name):
    d = base_dir(skills_dir, name)
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(os.path.join(skills_dir, name, "SKILL.md"), os.path.join(d, "SKILL.md"))
    res = score(skills_dir, name)
    with open(os.path.join(d, "score.json"), "w", encoding="utf-8") as f:
        json.dump(res, f)
    return res


def decide(skills_dir, name, apply=False):
    d = base_dir(skills_dir, name)
    try:
        with open(os.path.join(d, "score.json"), encoding="utf-8") as f:
            before = json.load(f)["score"]
    except (OSError, ValueError, KeyError):
        return {"verdict": "NO-BASELINE", "before": None, "after": score(skills_dir, name)["score"]}
    after = score(skills_dir, name)["score"]
    verdict = "KEEP" if after >= before else "REVERT"
    if verdict == "REVERT" and apply:
        shutil.copyfile(os.path.join(d, "SKILL.md"), os.path.join(skills_dir, name, "SKILL.md"))
        verdict = "REVERTED"
    return {"verdict": verdict, "before": before, "after": after}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    apply = "--apply" in a
    a = [x for x in a if x != "--apply"]
    if len(a) != 3 or a[0] not in ("score", "snapshot", "decide") or not os.path.isdir(a[1]):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, skills_dir, name = a
    res = {"score": score, "snapshot": snapshot}.get(cmd, lambda s, n: decide(s, n, apply))(skills_dir, name)
    print(json.dumps(res, indent=2))
    if cmd == "score":
        return 0 if not res["errors"] else 1
    return 1 if res.get("verdict") in ("REVERT", "REVERTED") else 0


if __name__ == "__main__":
    sys.exit(main())
