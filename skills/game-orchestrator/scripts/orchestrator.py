"""Orchestrator state tool: the resumable memory of the pipeline (stdlib only).

Usage:
  py -I orchestrator.py init   <gdd-dir> --project <project-root> [--day-h 16]
  py -I orchestrator.py status --project <project-root>
  py -I orchestrator.py next   --project <project-root>
  py -I orchestrator.py mark   <task-id> <in_progress|done|blocked|failed|pending> --project <root> [--evidence "text"]... [--note "text"] [--agent name]
  py -I orchestrator.py resume --project <root> [--live agent1,agent2]

State lives in `<project>/docs/orchestrator/state.json` (atomic write: temp file + rename) with an append-only
`log.md`. `next` returns ready tasks: up to 4 file-lane tasks (agents P/D/T) and at most 1 Editor-lane task (B/U),
never two tasks with overlapping claims. A task cannot be marked done without evidence (definition of done).
`resume` reconciles after a crash or compaction: in_progress tasks without a live agent go back to pending with
attempts + 1; after 3 attempts they become blocked (fallback: lower fidelity or cut P2).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gdd_lint  # noqa: E402
import gen_task_graph  # noqa: E402

MAX_ATTEMPTS = 3
FILE_LANE = ("P", "D", "T")
EDITOR_LANE = ("B", "U")
STATUSES = ("pending", "in_progress", "done", "blocked", "failed")


def paths(project):
    base = os.path.join(project, "docs", "orchestrator")
    return os.path.join(base, "state.json"), os.path.join(base, "log.md")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def log(project, line):
    _, lp = paths(project)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    with open(lp, "a", encoding="utf-8", newline="\n") as f:
        f.write("%s | %s\n" % (now(), line))


def load(project):
    with open(paths(project)[0], encoding="utf-8") as f:
        return json.load(f)


def save(project, state):
    sp, _ = paths(project)
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    tmp = sp + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, sp)


def init(gdd_dir, project, day_h=16.0):
    g = gdd_lint.load_gdd(gdd_dir)
    graph = gen_task_graph.generate(g, day_h)
    state = {"schema": 1, "game": g["index"].get("game"), "gdd_hash": gdd_lint.gdd_hash(gdd_dir), "started": now(), "phase": 0,
             "gate": {}, "budget": {"day_h": day_h, "est_wall_h": graph["totals"]["wall_h"], "est_sum_h": graph["totals"]["sum_h"],
                                    "tokens_cap": (g["index"].get("budget") or {}).get("tokens_cap")},
             "editor": {"project": project, "mcp": "unknown", "lock_owner": None, "last_compile_ok": None},
             "tasks": {t["id"]: dict(t) for t in graph["tasks"]}, "dropped": graph["dropped"], "assumptions": [], "human_pending": [],
             "blockers": [], "next_actions": []}
    recompute(state)
    save(project, state)
    log(project, "init | %d tasks, est wall %.1f h, dropped %d" % (len(state["tasks"]), graph["totals"]["wall_h"], len(graph["dropped"])))
    return state


def recompute(state):
    phases = sorted({t["phase"] for t in state["tasks"].values()})
    gate, current = {}, None
    for p in phases:
        ts = [t for t in state["tasks"].values() if t["phase"] == p]
        gate["G%d" % p] = "pass" if all(t["status"] == "done" for t in ts) else "open"
        if current is None and gate["G%d" % p] == "open":
            current = p
    state["gate"] = gate
    state["phase"] = current if current is not None else (phases[-1] if phases else 0)
    return state


def _claims_conflict(a, b):
    return bool(set(a["claims"]) & set(b["claims"]))


def ready(state, max_file=4):
    tasks = state["tasks"]
    busy = [t for t in tasks.values() if t["status"] == "in_progress"]
    out, file_n, editor_n = [], sum(t["agent"] in FILE_LANE for t in busy), sum(t["agent"] in EDITOR_LANE for t in busy)
    for tid in sorted(tasks):
        t = tasks[tid]
        if t["status"] != "pending" or any(tasks[d]["status"] != "done" for d in t["depends_on"] if d in tasks):
            continue
        if any(_claims_conflict(t, o) for o in busy + out):
            continue
        if t["agent"] in EDITOR_LANE:
            if editor_n >= 1:
                continue
            editor_n += 1
        else:
            if file_n >= max_file:
                continue
            file_n += 1
        out.append(t)
    return out


def mark(project, tid, status, evidence=None, note=None, agent=None):
    state = load(project)
    if tid not in state["tasks"]:
        raise KeyError("unknown task %s" % tid)
    if status not in STATUSES:
        raise ValueError("bad status %s" % status)
    t = state["tasks"][tid]
    if status == "done" and not evidence:
        raise ValueError("a task cannot be done without evidence (definition of done)")
    if status == "in_progress":
        if any(state["tasks"][d]["status"] != "done" for d in t["depends_on"] if d in state["tasks"]):
            raise ValueError("%s has unfinished dependencies" % tid)
        t["started"], t["agent_name"] = now(), agent
    if status in ("failed",):
        t["attempts"] += 1
        status = "blocked" if t["attempts"] >= MAX_ATTEMPTS else "pending"
    t["status"] = status
    if evidence:
        t["evidence"] = evidence
    if note:
        t["last_note"] = note
    recompute(state)
    save(project, state)
    log(project, "%s | %s | %s" % (tid, status, note or "; ".join(evidence or [])))
    return state


def resume(project, live=()):
    state = load(project)
    changes = []
    for tid, t in state["tasks"].items():
        if t["status"] == "in_progress" and t.get("agent_name") not in live:
            t["attempts"] += 1
            t["status"] = "blocked" if t["attempts"] >= MAX_ATTEMPTS else "pending"
            changes.append("%s in_progress without a live agent -> %s (attempts %d)" % (tid, t["status"], t["attempts"]))
        elif t["status"] == "done" and not t.get("evidence"):
            t["status"] = "pending"
            changes.append("%s was done without evidence -> reopened" % tid)
    recompute(state)
    state["next_actions"] = [t["id"] for t in ready(state)]
    save(project, state)
    for c in changes:
        log(project, "resume | " + c)
    return state, changes


def status(state):
    counts = {s: 0 for s in STATUSES}
    for t in state["tasks"].values():
        counts[t["status"]] += 1
    return {"game": state["game"], "phase": state["phase"], "gates": state["gate"], "counts": counts,
            "done_h": round(sum(t["est_h"] for t in state["tasks"].values() if t["status"] == "done"), 2),
            "total_h": round(sum(t["est_h"] for t in state["tasks"].values()), 2),
            "blocked": [t["id"] for t in state["tasks"].values() if t["status"] == "blocked"]}


def _opt(argv, key, default=None):
    return argv[argv.index(key) + 1] if key in argv else default


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("init", "status", "next", "mark", "resume"):
        print(__doc__, file=sys.stderr)
        return 2
    cmd, project = argv[0], _opt(argv, "--project")
    if not project:
        print("--project is required", file=sys.stderr)
        return 2
    try:
        if cmd == "init":
            s = init(argv[1], project, float(_opt(argv, "--day-h", 16)))
            print("initialised %d tasks, phase %d" % (len(s["tasks"]), s["phase"]))
        elif cmd == "status":
            print(json.dumps(status(load(project)), indent=1))
        elif cmd == "next":
            for t in ready(load(project)):
                print("%s [%s] %s (%s) skills: %s" % (t["id"], t["agent"], t["title"], t["group"], ", ".join(t["skills"])))
        elif cmd == "mark":
            ev = [argv[i + 1] for i, a in enumerate(argv) if a == "--evidence"]
            mark(project, argv[1], argv[2], ev, _opt(argv, "--note"), _opt(argv, "--agent"))
            print("%s -> %s" % (argv[1], argv[2]))
        else:
            _, changes = resume(project, set((_opt(argv, "--live", "") or "").split(",")) - {""})
            print("\n".join(changes) or "state consistent")
    except (KeyError, ValueError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
