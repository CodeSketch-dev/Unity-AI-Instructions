"""PostToolUse hook for Edit|Write on SKILL.md: lint the edited skill and feed errors back (exit 2 = message to the agent).

Runs the repo's tools/skill_lint.py on the skills directory that contains the file (so duplicate names and collisions
are caught). Silent when the file is not a SKILL.md or the linter is missing.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


def main():
    event = hooklib.read_event()
    path = hooklib.norm((event.get("tool_input") or {}).get("file_path", ""))
    if not path.endswith("/SKILL.md"):
        return 0
    skills_dir = os.path.dirname(os.path.dirname(path))
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or hooklib.project_dir(event)
    lint = os.path.join(plugin_root, "tools", "skill_lint.py")
    if not os.path.isfile(lint):
        return 0
    r = subprocess.run([sys.executable, "-I", lint, skills_dir], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return hooklib.block("skill lint failed:\n" + r.stdout[-1500:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
