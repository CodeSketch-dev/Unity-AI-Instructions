"""Create a new skill in the right place: skills/<group>/<name>/SKILL.md from the house template.
Usage: python tools/skillkit/new_skill.py <kebab-name> --group <group> --desc "Use when ..." [--triggers "a, b, c"]
Groups are the folders allowed by tools/publish/repo_layout_lint.py (SKILL_GROUPS). Next: edit the body, run skill_lint, publish.bat."""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "publish"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repo_layout_lint  # noqa: E402
import skill_paths  # noqa: E402

TEMPLATE = """---
name: {name}
description: "{desc}"
triggers: {triggers}
---

# {title}

Why: <one or two lines: the failure or cost this skill prevents>.

## Steps
1. <first concrete step, with the file or command>
2. <next step>
3. Verify: <the check that proves it worked>

## Exceptions
<when NOT to apply it>
"""


def create_skill(skills_root, name, group, desc, triggers):
    skills_root = Path(skills_root)
    if group not in repo_layout_lint.SKILL_GROUPS:
        raise ValueError("unknown group '%s'; use one of: %s" % (group, ", ".join(repo_layout_lint.SKILL_GROUPS)))
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", name):
        raise ValueError("name must be kebab-case (lowercase letters, digits, hyphens)")
    if not desc.startswith("Use when"):
        raise ValueError("description must start with 'Use when' and say when the skill applies")
    if skill_paths.skill_dir(str(skills_root), name):
        raise ValueError("skill '%s' already exists" % name)
    d = skills_root / group / name
    d.mkdir(parents=True)
    triggers = triggers.strip() or name.replace("-", " ")
    (d / "SKILL.md").write_text(TEMPLATE.format(name=name, desc=desc.replace('"', "'"), triggers=triggers, title=name.replace("-", " ").capitalize()), encoding="utf-8", newline="\n")
    return str(d / "SKILL.md")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--group", required=True)
    ap.add_argument("--desc", required=True)
    ap.add_argument("--triggers", default="")
    a = ap.parse_args(argv)
    repo = Path(__file__).resolve().parent.parent.parent
    try:
        print(create_skill(repo / "skills", a.name, a.group, a.desc, a.triggers))
    except ValueError as e:
        print("error: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
