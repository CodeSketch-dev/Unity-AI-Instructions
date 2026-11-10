"""Real token metrics from a Claude Code transcript JSONL. Returns UNKNOWN (None) when the runtime gave none.

Assistant entries carry message.usage; one API message can repeat across content blocks, so entries are
de-duplicated by message.id (last wins). Never estimates. Reads usage numbers only, never message text.
"""
import json


def transcript_usage(path, since_line=0):
    seen = {}
    n_lines = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, ln in enumerate(f):
            n_lines = i + 1
            if i < since_line or '"usage"' not in ln:
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            m = d.get("message") or {}
            u = m.get("usage")
            if not isinstance(u, dict):
                continue
            seen[m.get("id") or "line%d" % i] = u
    if not seen:
        return {"in_tok": None, "out_tok": None, "cache_tok": None, "messages": 0, "lines": n_lines, "status": "UNKNOWN"}
    tot = lambda k: sum(int(u.get(k) or 0) for u in seen.values())  # noqa: E731
    return {"in_tok": tot("input_tokens"), "out_tok": tot("output_tokens"),
            "cache_tok": tot("cache_creation_input_tokens") + tot("cache_read_input_tokens"),
            "messages": len(seen), "lines": n_lines, "status": "measured"}
