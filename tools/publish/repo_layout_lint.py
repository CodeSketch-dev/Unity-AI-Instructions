"""Repo layout lint: keeps the repo root and skills/ tidy. Every message is a micro-prompt naming the fix.
Usage: python tools/publish/repo_layout_lint.py [repo]   (exit 1 on violations)"""
import sys
from pathlib import Path

DOC = "docs/REPO-LAYOUT.md"
ROOT_FILES = {"AGENTS.md", "README.txt", "README.md", "STUDIO-BRAIN-DIGEST.md", "publish.bat", "sync.bat", ".gitignore"}
ROOT_DIRS = {"skills", "agents", "commands", "hooks", "data", "docs", "tools", "outputs"}
MAX_ENTRIES = 15
SKILL_GROUPS = ("ui", "gameplay", "studio-process", "unity-editor", "world-art", "perf-build", "clone-reference", "economy-monetization", "qa-testing", "general")
SKILL_GROUP_MAX = 60
# folders that may be wider than MAX_ENTRIES, each with the reason it cannot be split
WIDTH_EXEMPT = {
    "agents": "Claude loads agent definitions one level deep",
    "tools/tests": "pytest discovery over flat test files",
    "tools/evals/triggers": "one generated eval case per skill",
    "docs/superpowers": "dated plan/spec files",
}


def _hint(name, path):
    if path.is_file() and name.endswith(".ps1"):
        return "hook scripts belong in hooks/ps1/"
    if path.is_file() and name.endswith(".json"):
        return "data files belong in data/"
    if name == "projects.txt":
        return "config files belong in data/"
    if path.is_dir() and name in ("lint", "evals", "templates", "packages"):
        return "this lives under tools/ (lint, evals, packages) or data/ (templates)"
    if path.is_file() and name.endswith(".py"):
        return "scripts belong in tools/"
    return "move it into the matching folder, or add it to the allowlist in tools/publish/repo_layout_lint.py with a reason"


def _entries(d):
    return [e for e in d.iterdir() if not e.name.startswith(".") and e.name != "__pycache__"]


def _width_violations(repo):
    out = []
    for top in sorted(p for p in repo.iterdir() if p.is_dir() and p.name in ROOT_DIRS):
        for d in [top] + sorted(c for c in top.iterdir() if c.is_dir() and not c.name.startswith(".")):
            rel = d.relative_to(repo).as_posix()
            if rel.startswith("skills/"):
                continue  # skill groups use SKILL_GROUP_MAX in _skill_violations
            if rel in WIDTH_EXEMPT or d == top and top.name == "outputs":
                continue
            n = len(_entries(d))
            if n > MAX_ENTRIES:
                out.append("[LAYOUT] %s/ has %d entries (max %d): group them into subfolders by purpose. MANDATORY: read %s." % (rel, n, MAX_ENTRIES, DOC))
    return out


def _skill_violations(repo):
    out = []
    sk = repo / "skills"
    if not sk.is_dir():
        return out
    names = {}
    groups = ", ".join(SKILL_GROUPS)
    for d in sorted(p for p in sk.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if (d / "SKILL.md").is_file():
            out.append("[LAYOUT] skills/%s is a flat skill: skills live in skills/<group>/%s/ (groups: %s). Use python tools/skillkit/new_skill.py. MANDATORY: read %s." % (d.name, d.name, groups, DOC))
            continue
        if d.name not in SKILL_GROUPS:
            out.append("[LAYOUT] skills/%s is not a known skill group (groups: %s). Put the skill in one of them, or add a group in tools/publish/repo_layout_lint.py with a reason. MANDATORY: read %s." % (d.name, groups, DOC))
            continue
        kids = sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__")
        if len(kids) > SKILL_GROUP_MAX:
            out.append("[LAYOUT] skills/%s has %d entries (max %d): split the group. MANDATORY: read %s." % (d.name, len(kids), SKILL_GROUP_MAX, DOC))
        for k in kids:
            if not (k / "SKILL.md").is_file():
                out.append("[LAYOUT] skills/%s/%s has no SKILL.md: every skill folder needs one. MANDATORY: read %s." % (d.name, k.name, DOC))
            elif k.name in names:
                out.append("[LAYOUT] skill '%s' exists twice (skills/%s and skills/%s): names must be unique. MANDATORY: read %s." % (k.name, names[k.name], d.name, DOC))
            else:
                names[k.name] = d.name
    return out


def check_layout(repo):
    repo = Path(repo)
    out = []
    for p in sorted(repo.iterdir()):
        n = p.name
        if n.startswith("."):
            continue
        if p.is_file() and n not in ROOT_FILES:
            out.append("[LAYOUT] '%s' is not allowed at the repo root: %s. MANDATORY: read %s before moving it." % (n, _hint(n, p), DOC))
        elif p.is_dir() and n not in ROOT_DIRS:
            out.append("[LAYOUT] folder '%s/' is not allowed at the repo root: %s. MANDATORY: read %s before moving it." % (n, _hint(n, p), DOC))
    out.extend(_width_violations(repo))
    out.extend(_skill_violations(repo))
    return out


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent.parent)
    msgs = check_layout(repo)
    for m in msgs:
        print(m)
    print("layout lint: %d violation(s)" % len(msgs))
    sys.exit(1 if msgs else 0)
