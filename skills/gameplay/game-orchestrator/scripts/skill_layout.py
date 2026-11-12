"""Find sibling skills from a script that lives in a skill, in both layouts:
repo (grouped): skills/<group>/<skill>/scripts/x.py   installed (flat): skills/<skill>/scripts/x.py"""
import os


def skills_root(script_file):
    here = os.path.dirname(os.path.abspath(script_file))
    grouped = os.path.normpath(os.path.join(here, "..", "..", ".."))
    flat = os.path.normpath(os.path.join(here, "..", ".."))
    return grouped if os.path.basename(grouped) == "skills" else flat


def _is_skill(path):
    return os.path.isfile(os.path.join(path, "SKILL.md"))


def skill_dirs(root):
    """{name: dir} for every skill under root (depth 1 or 2)."""
    out = {}
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa):
            continue
        if _is_skill(pa):
            out[a] = pa
            continue
        for b in sorted(os.listdir(pa)):
            pb = os.path.join(pa, b)
            if os.path.isdir(pb) and _is_skill(pb):
                out[b] = pb
    return out


def skill_names(script_file):
    return sorted(skill_dirs(skills_root(script_file)))


def sibling_scripts(script_file, name):
    return os.path.join(skill_dirs(skills_root(script_file))[name], "scripts")
