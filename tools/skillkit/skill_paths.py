"""Single place that knows how skills are laid out: skills/<group>/<skill>/SKILL.md (grouped) or skills/<skill>/SKILL.md (legacy flat).
Every tool uses this instead of listing the skills folder itself. Installed copies (~/.claude/skills, <project>/.claude/skills) are always flat."""
import os


def _is_skill(path):
    return os.path.isfile(os.path.join(path, "SKILL.md"))


def iter_skills(root):
    """Yield (name, absolute_dir) for every skill under root, sorted by name."""
    root = str(root)
    found = []
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa) or a.startswith("."):
            continue
        if _is_skill(pa):
            found.append((a, pa))
            continue
        for b in sorted(os.listdir(pa)):
            pb = os.path.join(pa, b)
            if os.path.isdir(pb) and _is_skill(pb):
                found.append((b, pb))
    return sorted(found, key=lambda t: t[0])


def skill_dir(root, name):
    for n, d in iter_skills(root):
        if n == name:
            return d
    return None


def group_of(root, name):
    d = skill_dir(root, name)
    if d is None:
        return None
    parent = os.path.dirname(d)
    return None if os.path.abspath(parent) == os.path.abspath(str(root)) else os.path.basename(parent)


def duplicates(root):
    seen, dup = set(), []
    for n, _ in iter_skills(root):
        if n in seen and n not in dup:
            dup.append(n)
        seen.add(n)
    return dup


def orphans(root):
    """Folders that are neither a skill nor a group holding skills: a skill folder missing its SKILL.md, or an empty group."""
    root = str(root)
    out = []
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa) or a.startswith(".") or _is_skill(pa):
            continue
        kids = [b for b in sorted(os.listdir(pa)) if os.path.isdir(os.path.join(pa, b)) and not b.startswith(".")]
        if not kids:
            out.append(a)
        out.extend("%s/%s" % (a, b) for b in kids if not _is_skill(os.path.join(pa, b)))
    return out
