"""Record that the changed files were verified (compile + Console read), clearing the Stop-gate dirty list.

Usage: py -I gate_ok.py --evidence "Console clean 12:04, compile ok" [--project <root>]
Refuses an empty evidence string. Appends the evidence to docs/pipeline/run-state/gate-log.md.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ev = argv[argv.index("--evidence") + 1].strip() if "--evidence" in argv and argv.index("--evidence") + 1 < len(argv) else ""
    project = argv[argv.index("--project") + 1] if "--project" in argv else hooklib.project_dir()
    if not ev:
        print("evidence is required (what did you verify?)", file=sys.stderr)
        return 1
    state = hooklib.run_state_dir(project)
    dirty = os.path.join(state, "dirty.txt")
    n = 0
    if os.path.isfile(dirty):
        with open(dirty, encoding="utf-8") as f:
            n = sum(1 for l in f if l.strip())
        os.remove(dirty)
    counter = os.path.join(state, "stop-gate.count")
    if os.path.isfile(counter):
        os.remove(counter)
    with open(os.path.join(state, "gate-log.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("%s | verified %d file(s) | %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), n, ev))
    print("gate recorded for %d file(s)" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
