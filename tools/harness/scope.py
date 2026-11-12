"""Permission enforcement the agent cannot bypass: compare state before and after the run.
snapshot() hashes every dirty file (files already dirty are not blamed, but further edits are caught), the git metadata that
decides what later runs (HEAD, refs, hooks, config) and a few protected files outside the repo (user-level agent settings).
It protects against mistakes and honest-but-wrong agents; run untrusted agents in a sandbox or worktree as well."""
import hashlib
import os
import re
from pathlib import Path
import subprocess

HEAD_KEY = "__HEAD__"
GIT_PREFIX = "__GIT__/"
EXT_PREFIX = "__EXT__/"
DEFAULT_FORBIDDEN = [".git/**", "**/settings.json", "**/settings.local.json", "**/.env", "**/.env.*", "**/*.pem", "**/*secret*", "**/*.keystore"]


def default_extra_watch():
    home = Path(os.path.expanduser("~"))
    return [str(home / ".claude" / "settings.json"), str(home / ".claude" / "CLAUDE.md"), str(home / ".codex" / "AGENTS.md")]


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def _sha(path):
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "unreadable"


def _git_meta(repo):
    out = {}
    git_dir = Path(repo) / ".git"
    if not git_dir.is_dir():
        return out
    for name in ("config", "packed-refs"):
        if (git_dir / name).is_file():
            out[GIT_PREFIX + name] = _sha(git_dir / name)
    hooks = git_dir / "hooks"
    if hooks.is_dir():
        for p in sorted(hooks.iterdir()):
            if p.is_file() and not p.name.endswith(".sample"):
                out[GIT_PREFIX + "hooks/" + p.name] = _sha(p)
    refs = git_dir / "refs"
    if refs.is_dir():
        for p in sorted(refs.rglob("*")):
            if p.is_file():
                out[GIT_PREFIX + p.relative_to(git_dir).as_posix()] = _sha(p)
    return out


def snapshot(repo, extra_watch=None):
    repo = Path(repo)
    snap = {HEAD_KEY: _git(repo, "rev-parse", "HEAD").strip()}
    entries = _git(repo, "status", "--porcelain", "-z", "-uall").split("\0")
    i = 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        if e[0] in "RC" and i < len(entries):  # rename/copy: the next entry is the source path
            src = entries[i]
            i += 1
            if e[0] == "R" and not (repo / src).exists():
                snap[src] = "deleted"
        rel = e[3:]
        p = repo / rel
        snap[rel] = _sha(p) if p.is_file() else "deleted"
    snap.update(_git_meta(repo))
    for w in (default_extra_watch() if extra_watch is None else extra_watch):
        snap[EXT_PREFIX + str(w)] = _sha(w) if os.path.isfile(w) else "absent"
    return snap


def changed_since(before, after):
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k))


def _regex(glob):
    out, i = "", 0
    while i < len(glob):
        c = glob[i]
        if glob.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif glob.startswith("**", i):
            out += ".*"
            i += 2
        elif c == "*":
            out += "[^/]*"
            i += 1
        elif c == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(c)
            i += 1
    return re.compile("^" + out + "$")


def matches(path, glob):
    return bool(_regex(glob).match(path.replace(chr(92), "/")))


def check_scope(changed, owns, forbidden):
    out = []
    for p in changed:
        if p == HEAD_KEY:
            out.append("agent made a git commit (HEAD moved); the harness forbids committing")
        elif p.startswith(GIT_PREFIX):
            out.append("git metadata changed: %s (hooks, refs, branches, tags and config are off limits)" % p[len(GIT_PREFIX):])
        elif p.startswith(EXT_PREFIX):
            out.append("protected file outside the repo changed: %s" % p[len(EXT_PREFIX):])
        else:
            hit = next((g for g in forbidden if matches(p, g)), None)
            if hit:
                out.append("forbidden path changed: %s (matches %s)" % (p, hit))
            elif not any(matches(p, g) for g in owns):
                out.append("outside the task scope: %s (owns: %s)" % (p, ", ".join(owns)))
    return out
