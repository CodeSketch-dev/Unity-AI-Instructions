"""SubagentStart/SubagentStop hook: append one JSON line per event to docs/pipeline/agent-log.jsonl (audit trail).

Fields: ts, event, agent_type, agent_id, summary (first 160 chars of the last message on stop). Never blocks, never raises.
Rotates at 1 MB (keeps one .old file) so the log cannot grow without bound.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

MAX_BYTES = 1_000_000


def record(event):
    name = event.get("hook_event_name") or ("SubagentStop" if "last_assistant_message" in event else "SubagentStart")
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": name,
        "agent_type": event.get("agent_type") or "",
        "agent_id": event.get("agent_id") or "",
        "summary": " ".join(str(event.get("last_assistant_message") or "").split())[:160],
    }


def main():
    try:
        event = hooklib.read_event()
        if not event.get("agent_type"):
            return 0  # internal agents carry no type
        d = os.path.join(hooklib.project_dir(event), "docs", "pipeline")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "agent-log.jsonl")
        if os.path.isfile(path) and os.path.getsize(path) > MAX_BYTES:
            os.replace(path, path + ".old")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record(event), ensure_ascii=False) + "\n")
    except Exception:  # audit must never break a session
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
