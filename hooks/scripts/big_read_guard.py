"""PreToolUse(Read) guard: refuse a whole-file Read of a huge text doc and return its headings instead (saves tokens).

Applies to doc/data text files (md, txt, json, yaml, csv, log) over THRESHOLD_KB with no offset and no limit.
Source code, images and PDFs are never guarded. Escape hatches: set STUDIO_READ_GUARD=off, or repeat the same Read
within 120 s (the second attempt passes, so an agent that truly needs the whole file is never deadlocked).
Exit 2 + headings on stderr = refused; exit 0 = allowed.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

THRESHOLD_KB = 80
EXTS = (".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".log")
MAX_HEADINGS = 40


def headings(path):
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if re.match(r"^#{1,4} ", line):
                    out.append("%6d  %s" % (i, line.strip()[:100]))
    except OSError:
        pass
    return out


def decide(event, now=None):
    """Return a refusal message or None."""
    if os.environ.get("STUDIO_READ_GUARD", "").lower() == "off" or event.get("tool_name") != "Read":
        return None
    ti = event.get("tool_input") or {}
    path = ti.get("file_path") or ""
    if ti.get("offset") or ti.get("limit") or ti.get("pages") or ti.get("allow_large"):
        return None
    if not path.lower().endswith(EXTS) or not os.path.isfile(path):
        return None
    size = os.path.getsize(path)
    if size <= THRESHOLD_KB * 1024:
        return None
    now = time.time() if now is None else now
    stamp = os.path.join(hooklib.run_state_dir(hooklib.project_dir(event)), "read-guard.json")
    try:
        with open(stamp, encoding="utf-8") as f:
            seen = json.load(f)
    except (OSError, ValueError):
        seen = {}
    key = hooklib.norm(path)
    if now - seen.get(key, 0) < 120:
        return None
    seen[key] = now
    try:
        with open(stamp, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in seen.items() if now - v < 600}, f)
    except OSError:
        pass
    heads = headings(path)
    lines = heads[:MAX_HEADINGS] or ["  (no markdown headings: read it in ranges of a few hundred lines)"]
    if len(heads) > MAX_HEADINGS:
        lines.append("  ... %d more headings: Grep '^#' on the file" % (len(heads) - MAX_HEADINGS))
    return ("Read refused: %s is %d KB (limit %d KB for a whole-file read). Read by section: pick a heading below, then Read with "
            "offset (its line) and limit (a few hundred lines). If you truly need everything, repeat the same Read within 2 minutes.\n%s"
            % (path, size // 1024, THRESHOLD_KB, "\n".join(lines)))


def main():
    msg = decide(hooklib.read_event())
    if msg:
        return hooklib.block(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
