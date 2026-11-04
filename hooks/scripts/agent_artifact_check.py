"""SubagentStop hook (advisory): warn when a subagent stops without writing the report file its brief named.

The brief contract is a line such as: Report file: `docs/reports/x.md`  or  Write your report to `docs/reports/x.md`.
The path is read from the subagent's own transcript (first user message only). A missing file prints a systemMessage
JSON line (shown to the owner/coordinator) and exits 0: advisory, never blocks. A brief that names no path is not checked.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

CONTRACT = re.compile(r"(?:Report file:|Write your (?:full )?(?:output|report) to)\s*`([^`\n]+)`", re.I)
PLACEHOLDER = re.compile(r"\[[^\]]*\]|<[^>]*>|\{[^}]*\}")


def first_user_text(transcript):
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                if '"user"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    return line
                if obj.get("type") == "user" or obj.get("role") == "user" or obj.get("message", {}).get("role") == "user":
                    return json.dumps(obj.get("message", obj))
    except OSError:
        return ""
    return ""


def named_path(text):
    text = text.replace("\\\\", "/").replace(chr(92) + "`", "`")
    for m in CONTRACT.finditer(text):
        p = m.group(1).strip()
        if not PLACEHOLDER.search(p):
            return p
    return None


def decide(event):
    """Return a warning string, or None when fine / not checkable."""
    transcript = event.get("agent_transcript_path") or event.get("transcript_path")
    if not transcript or not event.get("agent_type"):
        return None
    if not os.path.isfile(transcript):
        return None
    path = named_path(first_user_text(transcript))
    if not path:
        return None
    full = path if os.path.isabs(path) else os.path.join(hooklib.project_dir(event), path)
    if os.path.isfile(full) and os.path.getsize(full) > 0:
        return None
    return ("Subagent %s stopped but the report file its brief named is missing or empty: %s. "
            "Treat the task as NOT done: resume the agent (SendMessage) and tell it to write the file." % (event.get("agent_type"), path))


def main():
    msg = decide(hooklib.read_event())
    if msg:
        print(json.dumps({"systemMessage": msg}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
