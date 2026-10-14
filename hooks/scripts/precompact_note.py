"""PreCompact hook: leave a breadcrumb before the context is compacted (never blocks).

Appends one line to docs/orchestrator/log.md (when an orchestrator state exists) naming the phase and the in-progress
tasks, so the producer can reconcile after compaction (`orchestrator.py resume`). Durable facts already live in files.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


def main():
    event = hooklib.read_event()
    root = hooklib.project_dir(event)
    sp = os.path.join(root, "docs", "orchestrator", "state.json")
    if not os.path.isfile(sp):
        return 0
    try:
        with open(sp, encoding="utf-8") as f:
            s = json.load(f)
        busy = [tid for tid, t in s["tasks"].items() if t["status"] == "in_progress"]
        with open(os.path.join(root, "docs", "orchestrator", "log.md"), "a", encoding="utf-8", newline="\n") as f:
            f.write("%s | compaction | phase %s, in progress: %s | after compaction run: orchestrator.py resume\n"
                    % (time.strftime("%Y-%m-%dT%H:%M:%S"), s.get("phase"), ", ".join(busy) or "none"))
    except (OSError, ValueError, KeyError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
