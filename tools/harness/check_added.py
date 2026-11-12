"""Verifier for train tasks: the trainer may only ADD new skills / lint rules, never edit existing ones.
It compares against the baseline snapshot the runner took before the task (env HARNESS_BASELINE), so files that were
already new or dirty before the run do not count, and edits the trainer made are never hidden.
Usage: python tools/harness/check_added.py [repo]   (exit 1 with the reasons)"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import scope  # noqa: E402

WATCH = ["skills/**", "tools/lint/rules/**", "tools/lint/tests/**"]
NEW_COUNTS = ["skills/*/*/SKILL.md", "tools/lint/rules/*.py"]
SKIP_NAMES = {"conftest.py", "pytest.ini", "setup.cfg", "pyproject.toml", "tox.ini"}


def _tracked(repo, rel):
    return subprocess.run(["git", "-C", str(repo), "cat-file", "-e", "HEAD:" + rel], capture_output=True).returncode == 0


def check(repo, baseline=None):
    repo = Path(repo)
    after = scope.snapshot(repo, extra_watch=[])
    changed = [p for p in scope.changed_since(baseline or {}, after) if not p.startswith("__")]
    new, problems = [], []
    for rel in changed:
        if os.path.basename(rel) in SKIP_NAMES and rel.startswith("tools/lint/") and after.get(rel) not in (None, "deleted"):
            problems.append("a pytest config file could hide failing tests: %s" % rel)
        if not any(scope.matches(rel, g) for g in WATCH):
            continue
        if _tracked(repo, rel):
            problems.append("edited an existing file (only new skills/rules are allowed): %s" % rel)
        elif after.get(rel) not in (None, "deleted"):
            new.append(rel)
    if not any(scope.matches(p, g) for p in new for g in NEW_COUNTS):
        problems.append("no new skill (skills/<group>/<name>/SKILL.md) or lint rule (tools/lint/rules/<name>.py) was added")
    return problems


if __name__ == "__main__":
    base = None
    if os.environ.get("HARNESS_BASELINE") and os.path.isfile(os.environ["HARNESS_BASELINE"]):
        with open(os.environ["HARNESS_BASELINE"], encoding="utf-8") as f:
            base = json.load(f)
    problems = check(sys.argv[1] if len(sys.argv) > 1 else ".", base)
    for p in problems:
        print(p)
    sys.exit(1 if problems else 0)
