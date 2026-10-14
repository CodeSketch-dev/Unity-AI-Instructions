"""SessionStart hook: give the agent the resume context without a prompt (stdout is added as context).

Prints: git status (short), the last 25 lines of docs/agent-handoff.md, the orchestrator status summary if a state file
exists, and the unverified-files warning. Output stays small (token cost). Never blocks.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


def tail(path, n):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()[-n:]
    except OSError:
        return []


def main():
    event = hooklib.read_event()
    root = hooklib.project_dir(event)
    out = ["# Session context (auto)"]
    try:
        st = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
        out += ["## git status", st[:1200] or "(clean)"]
    except (OSError, subprocess.SubprocessError):
        pass
    handoff = tail(os.path.join(root, "docs", "agent-handoff.md"), 25)
    if handoff:
        out += ["## docs/agent-handoff.md (tail)"] + handoff
    sp = os.path.join(root, "docs", "orchestrator", "state.json")
    if os.path.isfile(sp):
        try:
            with open(sp, encoding="utf-8") as f:
                s = json.load(f)
            counts = {}
            for t in s["tasks"].values():
                counts[t["status"]] = counts.get(t["status"], 0) + 1
            out += ["## orchestrator", "game %s, phase %s, tasks %s. Run: orchestrator.py resume, then next." % (s.get("game"), s.get("phase"), counts)]
        except (OSError, ValueError, KeyError):
            pass
    dirty = os.path.join(root, "docs", "pipeline", "run-state", "dirty.txt")
    if os.path.isfile(dirty) and os.path.getsize(dirty) > 0:
        out.append("## WARNING: changed files were never verified (dirty.txt): compile and read the Console first.")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
