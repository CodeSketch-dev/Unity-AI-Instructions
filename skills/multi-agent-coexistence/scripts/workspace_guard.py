"""Detect that another agent/human changed a file after you read it, and coordinate who edits what.

Problem it solves: Claude and Codex (or an agent and the Unity Editor) work in the same folder. One edits from a stale
copy and silently overwrites the other's newer work. Run `check` right before you write or save.

State lives inside the git dir (`.git/agent-guard/`) when the folder is a git repo, otherwise in `.agent-guard/`; it is never
placed under Assets/, and is not committed.

  snapshot  record the current content hash of files you just READ and are about to edit
  check     list files that differ from your snapshot (someone else wrote them) -> re-read and merge; exit 1 if any
  claim     advisory lock on a file (scene, prefab, builder, singleton asset); fails if another live claim exists
  release   drop your claim(s)
  status    show claims and git-dirty files (who may be mid-change)

Examples
  python -I workspace_guard.py snapshot --agent claude Assets/_Game/Scripts/Editor/EggUi_Builder.cs Assets/_Game/Scenes/Gameplay.unity
  python -I workspace_guard.py check    --agent claude
  python -I workspace_guard.py snapshot --agent claude <same files>        # after YOUR OWN write, to accept it
  python -I workspace_guard.py claim    --agent codex Assets/_Game/Scenes/Gameplay.unity --note "wiring shop board"
  python -I workspace_guard.py status
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

DEFAULT_TTL = 2 * 60 * 60


def run_git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=60)
        return out.stdout if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def state_dir(root):
    git_dir = run_git(root, "rev-parse", "--absolute-git-dir")
    base = git_dir.strip() if git_dir else os.path.join(root, ".agent-guard-state")
    path = os.path.join(base, "agent-guard") if git_dir else base
    os.makedirs(path, exist_ok=True)
    return path


def sha(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def save(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)
    os.replace(tmp, path)


def norm(root, p):
    full = p if os.path.isabs(p) else os.path.join(root, p)
    return os.path.relpath(os.path.abspath(full), root).replace("\\", "/")


def cmd_snapshot(args, root, sd):
    path = os.path.join(sd, f"snapshot-{args.agent}.json")
    snap = load(path, {})
    targets = list(args.paths)
    if args.dirty:
        dirty = run_git(root, "status", "--porcelain") or ""
        targets += [line[3:].strip().strip('"') for line in dirty.splitlines() if line[3:].strip()]
    if not targets:
        sys.exit("give paths (files you just read) or --dirty")
    for p in targets:
        rel = norm(root, p)
        snap[rel] = {"sha": sha(os.path.join(root, rel)), "time": time.time()}
    save(path, snap)
    print(f"snapshot for {args.agent}: {len(targets)} file(s) recorded")


def cmd_check(args, root, sd):
    snap = load(os.path.join(sd, f"snapshot-{args.agent}.json"), {})
    if not snap:
        sys.exit(f"no snapshot for {args.agent}; run snapshot on the files you read first")
    only = {norm(root, p) for p in args.paths} if args.paths else None
    changed, deleted, ok = [], [], 0
    for rel, info in snap.items():
        if only is not None and rel not in only:
            continue
        current = sha(os.path.join(root, rel))
        if current is None and info["sha"] is not None:
            deleted.append(rel)
        elif current != info["sha"]:
            changed.append(rel)
        else:
            ok += 1
    claims = load(os.path.join(sd, "claims.json"), {})
    for rel in changed:
        holder = claims.get(rel)
        who = f" (claimed by {holder['agent']}: {holder['note']})" if holder and holder["agent"] != args.agent else ""
        print(f"CHANGED since your snapshot: {rel}{who}")
    for rel in deleted:
        print(f"DELETED since your snapshot: {rel}")
    print(f"{ok} unchanged, {len(changed)} changed, {len(deleted)} deleted")
    if changed or deleted:
        print("-> Do NOT write from your old copy. Re-read these files, merge your intent into the current content, snapshot again.")
        sys.exit(1)


def live_claims(claims, ttl):
    now = time.time()
    return {rel: c for rel, c in claims.items() if now - c["time"] < ttl}


def cmd_claim(args, root, sd):
    path = os.path.join(sd, "claims.json")
    claims = live_claims(load(path, {}), args.ttl)
    refused = []
    for p in args.paths:
        rel = norm(root, p)
        holder = claims.get(rel)
        if holder and holder["agent"] != args.agent:
            refused.append(f"{rel} is claimed by {holder['agent']} ({holder['note']}, {int((time.time() - holder['time']) / 60)} min ago)")
        else:
            claims[rel] = {"agent": args.agent, "note": args.note or "", "time": time.time()}
    save(path, claims)
    for line in refused:
        print("REFUSED:", line)
    print(f"{len(args.paths) - len(refused)} claimed")
    if refused:
        print("-> Ask the user, work on something else, or wait for the release; do not edit a claimed file.")
        sys.exit(1)


def cmd_release(args, root, sd):
    path = os.path.join(sd, "claims.json")
    claims = load(path, {})
    targets = {norm(root, p) for p in args.paths} if args.paths else None
    for rel in list(claims):
        if claims[rel]["agent"] == args.agent and (targets is None or rel in targets):
            del claims[rel]
    save(path, claims)
    print("released")


def cmd_status(args, root, sd):
    claims = live_claims(load(os.path.join(sd, "claims.json"), {}), args.ttl)
    print(f"claims ({len(claims)}):")
    for rel, c in sorted(claims.items()):
        print(f"  {rel}: {c['agent']} - {c['note']} ({int((time.time() - c['time']) / 60)} min)")
    dirty = run_git(root, "status", "--porcelain")
    if dirty is not None:
        lines = dirty.splitlines()
        print(f"git-dirty files ({len(lines)}); may be another agent's work in progress:")
        for line in lines[:30]:
            print("  " + line)
        if len(lines) > 30:
            print(f"  ... {len(lines) - 30} more")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("snapshot", "check", "claim", "release", "status"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--agent", default=os.environ.get("AGENT_NAME", "agent"), help="your name: claude, codex, human ...")
        p.add_argument("--ttl", type=int, default=DEFAULT_TTL, help="claim lifetime in seconds")
        if name != "status":
            p.add_argument("paths", nargs="*")
        if name == "snapshot":
            p.add_argument("--dirty", action="store_true", help="also snapshot every git-dirty file")
        if name == "claim":
            p.add_argument("--note", default="")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    sd = state_dir(root)
    {"snapshot": cmd_snapshot, "check": cmd_check, "claim": cmd_claim, "release": cmd_release, "status": cmd_status}[args.cmd](args, root, sd)


if __name__ == "__main__":
    main()
