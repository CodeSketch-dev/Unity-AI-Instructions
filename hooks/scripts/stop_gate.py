"""Stop hook: do not let the agent finish while changed Unity files are unverified.

If docs/pipeline/run-state/dirty.txt lists files, the agent must compile through Unity MCP, read the Console, then run
`py -I hooks/scripts/gate_ok.py --evidence "<what was verified>"` (clears the list). This hook cannot compile Unity
itself: it enforces the process and records that verification was claimed with evidence. It blocks at most 3 times per
phase (counter file) and then lets the stop proceed, writing the failure to docs/agent-handoff.md so a human sees it.
Exit 2 = block (reason on stderr). Set UNITY_GATE_DISABLE=1 to disable (e.g. non-Unity sessions).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

MAX_BLOCKS = 3


def check(project):
    state = hooklib.run_state_dir(project)
    dirty, counter = os.path.join(state, "dirty.txt"), os.path.join(state, "stop-gate.count")
    files = []
    if os.path.isfile(dirty):
        with open(dirty, encoding="utf-8") as f:
            files = [l.strip() for l in f if l.strip()]
    if not files:
        if os.path.isfile(counter):
            os.remove(counter)
        return None
    n = 0
    if os.path.isfile(counter):
        with open(counter, encoding="utf-8") as f:
            try:
                n = int(f.read().strip() or 0)
            except ValueError:
                n = 0
    if n >= MAX_BLOCKS:
        handoff = os.path.join(project, "docs", "agent-handoff.md")
        os.makedirs(os.path.dirname(handoff), exist_ok=True)
        with open(handoff, "a", encoding="utf-8", newline="\n") as f:
            f.write("- %s | stop-gate | gave up after %d blocks: %d changed file(s) were never verified (%s) | next agent: compile and read the Console first\n"
                    % (time.strftime("%Y-%m-%d"), MAX_BLOCKS, len(files), ", ".join(files[:5])))
        os.remove(counter)
        return None
    with open(counter, "w", encoding="utf-8") as f:
        f.write(str(n + 1))
    return ("%d file(s) changed since the last verified gate (%s%s). Compile through Unity MCP, read the Console, fix errors, then run: "
            "py -I hooks/scripts/gate_ok.py --evidence \"<what you verified>\"" % (len(files), ", ".join(files[:5]), "..." if len(files) > 5 else ""))


def main():
    if os.environ.get("UNITY_GATE_DISABLE") == "1":
        return 0
    event = hooklib.read_event()
    reason = check(hooklib.project_dir(event))
    return hooklib.block(reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
