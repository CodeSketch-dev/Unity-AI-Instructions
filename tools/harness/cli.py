"""Studio harness CLI.
  python tools/harness/cli.py status                       progress summary, open ledger rows, STOP switch
  python tools/harness/cli.py next                         the next task that has not passed yet
  python tools/harness/cli.py run --agent claude|codex     run backlog tasks unattended inside the hard limits
  python tools/harness/cli.py mine                         turn repeated failures into candidates + train tasks
Create the file ~/.claude/harness.STOP (or pass --stop-file) to halt a running loop before its next task."""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness import agents, miner, progress, runner, tasks  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
OPEN_ROW = re.compile(r"\|\s*(OPEN|IN PROGRESS)\s*\|")


def _paths(a):
    return {
        "tasks": a.tasks_dir or str(REPO / "data" / "harness" / "tasks"),
        "profiles": a.profiles or str(REPO / "data" / "harness" / "permissions.json"),
        "progress": a.progress or str(REPO / "docs" / "log" / "harness" / "progress.jsonl"),
        "stop": a.stop_file or os.environ.get("HARNESS_STOP_FILE") or os.path.join(os.path.expanduser("~"), ".claude", "harness.STOP"),
        "ledger": a.ledger or str(REPO / "docs" / "owner-requests.md"),
    }


def _mine(p):
    recs = progress.read(p["progress"])
    cands = miner.mine(recs)
    md = str(Path(p["progress"]).with_name("candidates.md"))
    miner.write_candidates(cands, md)
    made = [str(miner.make_train_task(c, p["tasks"])) for c in cands]
    return cands, made


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["status", "next", "run", "mine"])
    ap.add_argument("--agent", default="claude", help="claude | codex | fake (no-op, for plumbing checks)")
    ap.add_argument("--model", default="")
    ap.add_argument("--max-tasks", type=int, default=5)
    ap.add_argument("--max-consecutive-failures", type=int, default=3)
    ap.add_argument("--only", default="", help="run just this task id")
    ap.add_argument("--force", action="store_true", help="run the task even if it already passed (use with --only)")
    ap.add_argument("--no-train", action="store_true", help="do not generate train tasks after a run")
    ap.add_argument("--tasks-dir")
    ap.add_argument("--profiles")
    ap.add_argument("--progress")
    ap.add_argument("--stop-file")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    p = _paths(a)

    if a.cmd == "status":
        recs = progress.read(p["progress"])
        if recs:
            last = {}
            for r in recs:
                last[r.get("task")] = r.get("status")
            print("tasks seen: %d | passed: %d | attempts logged: %d" % (len(last), sum(1 for s in last.values() if s == "pass"), len(recs)))
            for t, s in sorted(last.items(), key=lambda kv: str(kv[0])):
                print("  %s: %s" % (t, s))
        else:
            print("no progress yet")
        rows = sum(1 for line in open(p["ledger"], encoding="utf-8", errors="replace") if OPEN_ROW.search(line)) if os.path.isfile(p["ledger"]) else 0
        print("open ledger rows: %d" % rows)
        print("stop file: %s" % ("PRESENT (loop will halt)" if os.path.exists(p["stop"]) else "absent"))
        return 0

    ts = tasks.load_tasks(p["tasks"])
    if a.cmd == "next":
        t = progress.next_task(ts, progress.read(p["progress"]))
        print("%s: %s" % (t.id, t.title) if t else "no open tasks")
        return 0

    if a.cmd == "mine":
        cands, made = _mine(p)
        print("candidates: %d, train tasks: %d" % (len(cands), len(made)))
        for c in cands:
            print("  %s x%d  %s" % (c.signature, c.count, ", ".join(c.task_ids)))
        return 0

    if a.only:
        ts = [t for t in ts if t.id == a.only]
        if not ts:
            print("no task named %s" % a.only)
            return 2
    profiles = agents.load_profiles(p["profiles"])
    agent = agents.FakeAgent(lambda brief, task, cwd: None) if a.agent == "fake" else agents.make_agent(a.agent, a.model)
    res = runner.run_loop(ts, agent, REPO, p["progress"], profiles, max_tasks=a.max_tasks, stop_file=p["stop"], max_consecutive_failures=a.max_consecutive_failures, ignore_done=a.force)
    for tid, status in res["ran"]:
        print("%s -> %s" % (tid, status))
    print("halted: %s" % res["halted"])
    if not a.no_train:
        cands, made = _mine(p)
        print("training: %d candidate(s), %d train task(s) queued" % (len(cands), len(made)))
    return 0 if all(s == "pass" for _, s in res["ran"]) else 1


if __name__ == "__main__":
    sys.exit(main())
