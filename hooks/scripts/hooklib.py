"""Shared helpers for the pipeline hooks (stdlib only).

Claude Code passes a JSON event on stdin: {"tool_name": ..., "tool_input": {...}, "cwd": ...}.
A hook blocks by exiting 2 with the reason on stderr (PreToolUse, Stop, ...). Exit 0 = allow.
"""
import json
import os
import sys


def read_event():
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def project_dir(event=None):
    return os.environ.get("CLAUDE_PROJECT_DIR") or (event or {}).get("cwd") or os.getcwd()


def block(message):
    sys.stderr.write(message.rstrip() + "\n")
    return 2


def norm(path):
    return (path or "").replace("\\", "/")


def run_state_dir(project):
    d = os.path.join(project, "docs", "pipeline", "run-state")
    os.makedirs(d, exist_ok=True)
    return d
