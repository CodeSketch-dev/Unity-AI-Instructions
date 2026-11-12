"""Repo layout lint: keeps the repo root and skills/ tidy. Every message is a micro-prompt naming the fix.
Usage: python tools/repo_layout_lint.py [repo]   (exit 1 on violations)"""
import sys
from pathlib import Path

DOC = "docs/REPO-LAYOUT.md"
ROOT_FILES = {"AGENTS.md", "README.txt", "README.md", "STUDIO-BRAIN-DIGEST.md", "publish.bat", "sync.bat", "projects.txt", ".gitignore"}
ROOT_DIRS = {"skills", "agents", "commands", "templates", "evals", "docs", "tools", "packages", "hooks", "data", "lint", "outputs"}


def _hint(name, path):
    if path.is_file() and name.endswith(".ps1"):
        return "hook scripts belong in hooks/ps1/"
    if path.is_file() and name.endswith(".json"):
        return "data files belong in data/"
    if path.is_file() and name.endswith(".py"):
        return "scripts belong in tools/"
    return "move it into the matching folder, or add it to the allowlist in tools/repo_layout_lint.py with a reason"


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
    sk = repo / "skills"
    if sk.is_dir():
        for d in sorted(sk.iterdir()):
            if d.is_dir() and not (d / "SKILL.md").is_file():
                out.append("[LAYOUT] skills/%s has no SKILL.md: every skill folder needs one. MANDATORY: read %s." % (d.name, DOC))
    return out


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent)
    msgs = check_layout(repo)
    for m in msgs:
        print(m)
    print("layout lint: %d violation(s)" % len(msgs))
    sys.exit(1 if msgs else 0)
