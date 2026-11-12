"""Backup a skill and list what depends on it BEFORE editing/renaming/deleting.

Usage: py -I scripts/backup_deps.py backup <name>   -> copies skills/<name> to .skill-backups/<ts>/<name>
       py -I scripts/backup_deps.py deps <name>     -> files outside the skill that mention <name>
Only the repo skills dir is touched; vendor/plugin skills are refused (read-only).
"""
import os
import re
import shutil
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SCAN = ["skills", "agents", "hooks", "commands", "tools", "data/templates", "AGENTS.md", "data",
        "STUDIO-BRAIN-DIGEST.md"]
EXT = {".md", ".json", ".ps1", ".py", ".bat", ".txt", ".mjs", ".yaml", ".yml"}


def _own_dir(name):
    """repo skills/<group>/<name> (grouped) or skills/<name> (flat)"""
    import glob
    hits = glob.glob(os.path.join(REPO, "skills", "*", name, "SKILL.md")) or glob.glob(os.path.join(REPO, "skills", name, "SKILL.md"))
    return os.path.normpath(os.path.dirname(hits[0])) if hits else os.path.normpath(os.path.join(REPO, "skills", name))


def deps(name):
    pat = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(name))
    own = _own_dir(name) + os.sep
    hits = {}
    for entry in SCAN:
        root = os.path.join(REPO, entry)
        if os.path.isfile(root):
            files = [root]
        else:
            files = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs]
        for p in files:
            if os.path.splitext(p)[1] not in EXT or "__pycache__" in p or os.path.normpath(p).startswith(own):
                continue
            try:
                n = len(pat.findall(open(p, encoding="utf-8", errors="replace").read()))
            except OSError:
                continue
            if n:
                hits[os.path.relpath(p, REPO)] = n
    return hits


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("backup", "deps"):
        print(__doc__)
        return 2
    cmd, name = sys.argv[1:]
    src = os.path.join(REPO, "skills", name)
    if not os.path.isdir(src):
        print("not an editable repo skill (vendor/plugin skills are read-only): %s" % name)
        return 2
    if cmd == "backup":
        dst = os.path.join(REPO, ".skill-backups", time.strftime("%Y%m%d-%H%M%S"), name)
        shutil.copytree(src, dst)
        print("backup: %s" % os.path.relpath(dst, REPO))
    else:
        h = deps(name)
        for k, v in sorted(h.items()):
            print("%4d  %s" % (v, k))
        print("%d dependent file(s)" % len(h))
    return 0


if __name__ == "__main__":
    sys.exit(main())
