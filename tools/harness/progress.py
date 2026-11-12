"""Append-only progress file: one JSON object per attempt. Any later agent reads it to know what happened."""
import json
import os
import re
import time


_SECRET = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{10,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|Bearer\s+[A-Za-z0-9._-]{20,})")
_KV = re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd)\b(\s*[:=]\s*)(\S+)")


def scrub(obj):
    """Mask secrets in every string of a record before it is written (the progress file is committed and shared)."""
    if isinstance(obj, str):
        return _SECRET.sub("***", _KV.sub(lambda m: m.group(1) + m.group(2) + "***", obj))
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    return obj


def append(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec = scrub(dict(record))
    rec.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=True) + "\n")
    return rec


def read(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue  # a half-written or corrupt line must never stop status/mine
    return out


def done_ids(records):
    return {r.get("task") for r in records if r.get("status") == "pass"}


def next_task(tasks, records):
    done = done_ids(records)
    return next((t for t in tasks if t.id not in done), None)


def write_summary(records, md_path):
    last = {}
    for r in records:
        last[r.get("task")] = r
    lines = ["# Harness progress (generated, do not edit)", "", "| task | status | when | attempts |", "|---|---|---|---|"]
    attempts = {}
    for r in records:
        attempts[r.get("task")] = attempts.get(r.get("task"), 0) + 1
    for t, r in sorted(last.items(), key=lambda kv: str(kv[0])):
        lines.append("| %s | %s | %s | %d |" % (t, r.get("status"), r.get("ts", ""), attempts[t]))
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
