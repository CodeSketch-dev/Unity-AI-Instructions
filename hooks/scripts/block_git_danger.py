"""PreToolUse hook for Bash: block destructive or outward-facing git commands.

Blocks: git push, reset --hard, clean -f/-d/-x, checkout -- <path>, restore, stash drop/clear, branch -D, rebase -i,
any --force / -f push flag, `rm -rf` of Assets/ProjectSettings/Library paths. Allows read-only git and normal commits
unless the user disabled them (commits are the user's call: AGENTS.md says do not commit unless asked; the hook
cannot know, so it only blocks commits when docs/pipeline/no-commits exists).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

PATTERNS = [
    (r"\bgit\s+push\b", "git push is outward-facing: ask the user."),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard discards work: never without explicit authorization."),
    (r"\bgit\s+clean\b[^|;&]*-[a-z]*[fdx]", "git clean deletes untracked files: never without explicit authorization."),
    (r"\bgit\s+checkout\s+--\s", "git checkout -- discards changes: do not revert other agents' work."),
    (r"\bgit\s+restore\b", "git restore discards changes: do not revert other agents' work."),
    (r"\bgit\s+stash\s+(drop|clear)\b", "dropping stashes loses work."),
    (r"\bgit\s+branch\s+-D\b", "force-deleting a branch loses work."),
    (r"\bgit\s+rebase\s+-i\b", "interactive rebase is not supported here."),
    (r"\brm\s+-[a-z]*r[a-z]*f?\s+[^|;&]*\b(Assets|ProjectSettings|Library|Packages)\b", "recursive delete of a Unity project folder: ask the user."),
]


def decide(event):
    cmd = (event.get("tool_input") or {}).get("command", "")
    for pat, why in PATTERNS:
        if re.search(pat, cmd):
            return why
    if re.search(r"\bgit\s+commit\b", cmd) and os.path.exists(os.path.join(hooklib.project_dir(event), "docs", "pipeline", "no-commits")):
        return "commits are disabled for this run (docs/pipeline/no-commits exists): ask the user."
    return None


def main():
    event = hooklib.read_event()
    reason = decide(event)
    return hooklib.block(reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
