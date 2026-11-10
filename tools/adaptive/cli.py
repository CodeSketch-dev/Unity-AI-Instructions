"""Adaptive Task Intelligence CLI (stdlib). Output is short JSON/text so it costs few tokens.

  py -I tools/adaptive/cli.py classify "<task text>"
  py -I tools/adaptive/cli.py select --category C --env E [--candidates a,b,c] [--profile balanced|speed|tokens|accuracy] [--critical]
  py -I tools/adaptive/cli.py record --category C --env E --method M --success 1 --verified 1 --latency-ms N [--in-tok N --out-tok N ...]
  py -I tools/adaptive/cli.py report [--category C]          # aggregates only
  py -I tools/adaptive/cli.py reset --category C [--env E --method M]   # soft reset (undo: reset-undo <id>)
  py -I tools/adaptive/cli.py backup | restore <file> | resets | health
  py -I tools/adaptive/cli.py propose | apply <proposal.json> --skill S --allow-skill-edit | rollback-skill S
  py -I tools/adaptive/cli.py metrics --transcript <file.jsonl>     # real token totals or UNKNOWN
  py -I tools/adaptive/cli.py stop | resume                          # emergency stop switch
Env signature format: os=windows|app=<name>|ver=<x>  (must contain app=; a changed ver is detected and old data is not reused).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from adaptive import classify, loop, metrics, selector, skill_proposals, store  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def out(o):
    print(json.dumps(o, indent=1, default=str))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="adaptive")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("classify"); p.add_argument("text")
    p = sub.add_parser("select")
    p.add_argument("--category", required=True); p.add_argument("--env", required=True)
    p.add_argument("--candidates"); p.add_argument("--profile", default="balanced", choices=sorted(selector.PROFILES))
    p.add_argument("--critical", action="store_true"); p.add_argument("--no-explore", action="store_true")
    p = sub.add_parser("record")
    for a in ("category", "env", "method"):
        p.add_argument("--" + a, required=True)
    p.add_argument("--success", type=int, required=True); p.add_argument("--verified", type=int, default=0)
    for a in ("latency-ms", "tool-ms", "wait-ms", "model-ms", "recovery-ms", "predicted-p"):
        p.add_argument("--" + a, type=float)
    for a in ("tool-calls", "in-tok", "out-tok", "cache-tok", "retries"):
        p.add_argument("--" + a, type=int)
    p.add_argument("--fail-reason")
    p = sub.add_parser("report"); p.add_argument("--category")
    p = sub.add_parser("reset")
    for a in ("category", "env", "method"):
        p.add_argument("--" + a)
    p = sub.add_parser("reset-undo"); p.add_argument("id", type=int)
    sub.add_parser("backup"); p = sub.add_parser("restore"); p.add_argument("file")
    sub.add_parser("resets"); sub.add_parser("health"); sub.add_parser("propose")
    p = sub.add_parser("apply"); p.add_argument("proposal"); p.add_argument("--skill", required=True)
    p.add_argument("--allow-skill-edit", action="store_true")
    p = sub.add_parser("rollback-skill"); p.add_argument("skill")
    p = sub.add_parser("metrics"); p.add_argument("--transcript", required=True); p.add_argument("--since-line", type=int, default=0)
    sub.add_parser("stop"); sub.add_parser("resume")
    a = ap.parse_args(argv)
    skills_dir = os.path.join(REPO, "skills")

    if a.cmd == "classify":
        out(classify.classify(a.text)); return 0
    if a.cmd == "stop":
        loop.request_stop(); print("STOP set at", loop.stop_file()); return 0
    if a.cmd == "resume":
        loop.clear_stop(); print("STOP cleared"); return 0
    if a.cmd == "metrics":
        out(metrics.transcript_usage(a.transcript, a.since_line)); return 0
    if a.cmd == "rollback-skill":
        out(skill_proposals.rollback(skills_dir, a.skill)); return 0
    if a.cmd == "restore":
        store.restore(None, a.file); print("restored from", a.file); return 0
    if a.cmd == "backup":
        print(store.backup(None, "manual") or "no database yet"); return 0
    conn = store.connect()
    if a.cmd == "select":
        cands = a.candidates.split(",") if a.candidates else None
        if not cands:
            for c in classify.taxonomy()["categories"]:
                if c["id"] == a.category:
                    cands = c["candidates"]
        if not cands:
            print("unknown category; pass --candidates a,b,c", file=sys.stderr); return 2
        r = selector.select(conn, a.category, cands, a.env, a.profile, a.critical, explore=not a.no_explore)
        r["stats"] = {m: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()} for m, s in r["stats"].items()}
        out(r)
    elif a.cmd == "record":
        kw = {k: v for k, v in vars(a).items() if k not in ("cmd",) and v is not None}
        kw = {k.replace("-", "_"): v for k, v in kw.items()}
        print("recorded run", store.record_run(conn, **kw))
    elif a.cmd == "report":
        out(store.summary(conn, a.category))
    elif a.cmd == "reset":
        print("reset id", store.reset(conn, a.category, a.env, a.method), "(undo with: reset-undo <id>)")
    elif a.cmd == "reset-undo":
        store.undo_reset(conn, a.id); print("undone", a.id)
    elif a.cmd == "resets":
        out([dict(r) for r in conn.execute("SELECT * FROM resets ORDER BY id DESC LIMIT 20")])
    elif a.cmd == "health":
        n = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        out({"db": store.db_path(), "schema": store.SCHEMA_VERSION, "runs": n, "size_kb": round(os.path.getsize(store.db_path()) / 1024, 1),
             "stop_active": loop.stop_requested()})
    elif a.cmd == "propose":
        out(skill_proposals.propose(conn, classify.taxonomy()))
    elif a.cmd == "apply":
        out(skill_proposals.apply(json.load(open(a.proposal)), skills_dir, a.skill, a.allow_skill_edit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
