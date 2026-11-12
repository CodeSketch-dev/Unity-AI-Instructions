"""Learned preferences -> skill proposals. Proposals are files; editing a skill needs explicit permission.

A proposal is written only when a data-backed method beats the hierarchy's first choice with enough samples
(>=PROPOSE_MIN_N effective for both, lb >= 0.9 for the winner, >=30% faster). Applying (explicit flag only):
backup -> append a delimited LEARNED block (never touches mandatory text or safety rules) -> lint + score
before/after -> restore the backup when anything gets worse. Rollback restores the latest adaptive backup.
"""
import json
import os
import re
import shutil
import sys
import time

from . import selector, store

PROPOSE_MIN_N = 20.0
START = "<!-- adaptive:learned:start -->"
END = "<!-- adaptive:learned:end -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)


def proposals_dir():
    return os.path.join(store.home(), "proposals")


def propose(conn, taxonomy_data, now=None):
    out = []
    for cat in taxonomy_data["categories"]:
        cands = cat["candidates"]
        if len(cands) < 2:
            continue
        envs = [r[0] for r in conn.execute("SELECT DISTINCT env FROM runs WHERE category=?", (store.clean_key(cat["id"]),))]
        for env in envs:
            st = {m: selector.method_stats(store.scope_runs(conn, cat["id"], env, m), now) for m in cands}
            first, best = cands[0], None
            for m in cands[1:]:
                s, f = st[m], st[first]
                if (s["n_eff"] >= PROPOSE_MIN_N and f["n_eff"] >= PROPOSE_MIN_N and s["lb"] >= 0.9 and s["lat_ms"] and f["lat_ms"]
                        and s["lat_ms"] <= 0.7 * f["lat_ms"] and s["p"] >= f["p"] - 0.02):
                    best = m
            if best:
                out.append({"category": cat["id"], "env": env, "hierarchy_first": first, "winner": best,
                            "evidence": {k: {"n_eff": round(v["n_eff"], 1), "p": round(v["p"], 3), "lb": round(v["lb"], 3),
                                             "lat_ms": v["lat_ms"]} for k, v in st.items()}, "status": "pending"})
    os.makedirs(proposals_dir(), exist_ok=True)
    for p in out:
        fn = os.path.join(proposals_dir(), re.sub(r"[^a-z0-9._-]", "_", "%s__%s.json" % (p["category"], p["env"]), flags=re.I))
        json.dump(p, open(fn, "w"), indent=1)
    return out


def learned_text(p):
    return ("%s\n## Learned preference (measured, not mandatory)\nFor `%s` in env `%s`, `%s` measured better than the default `%s` "
            "(n_eff %.0f vs %.0f). Prefer it there; keep the default as fallback. Safety rules and verification above still apply. "
            "Reset with `cli.py reset`.\n%s\n" % (START, p["category"], p["env"], p["winner"], p["hierarchy_first"],
                                                  p["evidence"][p["winner"]]["n_eff"], p["evidence"][p["hierarchy_first"]]["n_eff"], END))


def _sdir(skills_dir, name):
    """Skill folder by name in the grouped (skills/<group>/<name>) or flat layout."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skillkit"))
    import skill_paths  # noqa: E402
    return skill_paths.skill_dir(skills_dir, name) or os.path.join(skills_dir, name)


def backup_skill(skills_dir, name):
    src = _sdir(skills_dir, name)
    dst = os.path.join(store.home(), "skill-backups", time.strftime("%Y%m%d-%H%M%S-") + "%06d" % int((time.time() % 1) * 1e6), name)
    shutil.copytree(src, dst)
    return dst


def _score(skills_dir, name):
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "skillkit"))
    import skill_loop  # noqa: E402
    return skill_loop.score(skills_dir, name)["score"]


def apply(proposal, skills_dir, skill, allow_skill_edit=False, score_fn=None):
    if not allow_skill_edit:
        return {"applied": False, "reason": "explicit permission flag missing (--allow-skill-edit)"}
    md = os.path.join(_sdir(skills_dir, skill), "SKILL.md")
    if not os.path.isfile(md):
        return {"applied": False, "reason": "skill not found: %s" % skill}
    bak = backup_skill(skills_dir, skill)
    score_fn = score_fn or _score
    before = score_fn(skills_dir, skill)
    text = open(md, encoding="utf-8").read()
    text = BLOCK_RE.sub("", text).rstrip("\n") + "\n\n" + learned_text(proposal)
    open(md, "w", encoding="utf-8").write(text)
    after = score_fn(skills_dir, skill)
    if after < before:
        shutil.rmtree(_sdir(skills_dir, skill))
        shutil.copytree(os.path.join(bak), _sdir(skills_dir, skill))
        return {"applied": False, "reason": "score dropped %s -> %s; restored from backup" % (before, after), "backup": bak}
    return {"applied": True, "backup": bak, "score": [before, after]}


def rollback(skills_dir, skill):
    root = os.path.join(store.home(), "skill-backups")
    if not os.path.isdir(root):
        return {"restored": False, "reason": "no backups"}
    for ts in sorted(os.listdir(root), reverse=True):
        cand = os.path.join(root, ts, skill)
        if os.path.isdir(cand):
            dst = _sdir(skills_dir, skill)
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(cand, dst)
            return {"restored": True, "from": cand}
    return {"restored": False, "reason": "no backup for %s" % skill}
