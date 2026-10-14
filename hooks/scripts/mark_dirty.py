"""PostToolUse hook for Edit|Write: remember which Unity-relevant files changed since the last verified gate.

Appends the path to docs/pipeline/run-state/dirty.txt for .cs, .asmdef, .asset, .prefab, .unity, .shader, .shadergraph,
.uxml, .json under Assets/. The Stop gate (stop_gate.py) refuses to let the agent finish while this list is non-empty
until `gate_ok.py` records verification evidence. Never blocks (exit 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

TRACKED = (".cs", ".asmdef", ".asset", ".prefab", ".unity", ".shader", ".shadergraph", ".hlsl", ".cginc")


def main():
    event = hooklib.read_event()
    ti = event.get("tool_input") or {}
    path = hooklib.norm(ti.get("file_path") or ti.get("path") or "")
    if not path.lower().endswith(TRACKED):
        return 0
    state = hooklib.run_state_dir(hooklib.project_dir(event))
    dirty = os.path.join(state, "dirty.txt")
    existing = set()
    if os.path.isfile(dirty):
        with open(dirty, encoding="utf-8") as f:
            existing = {l.strip() for l in f if l.strip()}
    if path not in existing:
        with open(dirty, "a", encoding="utf-8", newline="\n") as f:
            f.write(path + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
