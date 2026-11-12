"""QA run bookkeeping: run the static stage, record stage results, compute the verdict, write the report.

  py -I qa_run.py static  --project P [--scope diff|full] [--required-refs F] [--rules F]
  py -I qa_run.py record  --project P --stage S1 --result pass|fail|skip --evidence "..." [--signature SIG] [--soft-note TEXT]
  py -I qa_run.py verdict --project P --task NAME --rung mcp|batch|static [--time-scale 1] [--save fresh|fixture|unknown]

Stages: S0 preflight, S1 compile, S2 static, S3 data, S4 wiring, S5 ui, S6 play, S7 perf, S8 log. Unity-dependent stages are
recorded by the agent with real evidence (test output, Console excerpt). Verdicts (see rule-qa-verdicts):
PASS, PASS-WITH-NOTES, STATIC-PASS, INCONCLUSIVE, FAIL. State: docs/qa/run-state.json; reports: docs/qa/reports/.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qa_asmdef  # noqa: E402
import qa_banned_api  # noqa: E402
import qa_lint_layout  # noqa: E402
import qa_scan_refs  # noqa: E402

STAGES = ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
REQUIRED_FOR_PASS = ["S1", "S2", "S3", "S4", "S6", "S8"]
MAX_ITER = 5


def state_path(project):
    return os.path.join(project, "docs", "qa", "run-state.json")


def load_state(project):
    try:
        with open(state_path(project), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"stages": {}, "history": []}


def save_state(project, state):
    p = state_path(project)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, p)


def changed_files(project):
    try:
        out = subprocess.run(["git", "-C", project, "status", "--porcelain", "--", "Assets", "Packages", "ProjectSettings"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    files = []
    for line in out.splitlines():
        p = line[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ")[1]
        files.append(p)
    return files


def fingerprint(project):
    h = hashlib.sha1()
    for f in sorted(changed_files(project)):
        h.update(f.encode())
        try:
            with open(os.path.join(project, f), "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
    return h.hexdigest()[:12]


def run_static(project, scope, required_refs, rules):
    files = None
    if scope == "diff":
        files = changed_files(project)
        if not files:
            files = ["__none__"]
    patterns = []
    if required_refs and os.path.isfile(required_refs):
        with open(required_refs, encoding="utf-8") as f:
            patterns = json.load(f).get("patterns", [])
    rule_list = None
    if rules and os.path.isfile(rules):
        with open(rules, encoding="utf-8") as f:
            rule_list = json.load(f)
    findings, _ = qa_scan_refs.scan(project, files, patterns)
    findings += qa_banned_api.scan(project, files, rule_list)
    findings += qa_lint_layout.scan(project, files)
    findings += qa_asmdef.scan(project, files)
    return findings


def cmd_static(a):
    findings = run_static(a.project, a.scope, a.required_refs, a.rules)
    art = os.path.join(a.project, "docs", "qa", "artifacts")
    os.makedirs(art, exist_ok=True)
    with open(os.path.join(art, "static.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for x in findings:
            f.write(json.dumps(x) + "\n")
    errors = [x for x in findings if x["severity"] == "error"]
    warns = len(findings) - len(errors)
    sig = ";".join(sorted({"%s:%s" % (x["rule"], x["file"]) for x in errors}))[:200]
    ev = "static scan %s: %d error(s), %d warning(s); details docs/qa/artifacts/static.jsonl" % (a.scope, len(errors), warns)
    record(a.project, "S2", "fail" if errors else "pass", ev, sig if errors else "", "%d warning(s)" % warns if warns else "")
    for x in errors[:15]:
        print("ERROR %s %s:%s %s" % (x["rule"], x["file"], x["line"], x["msg"]))
    print(ev)
    return 1 if errors else 0


def record(project, stage, result, evidence, signature="", soft_note=""):
    st = load_state(project)
    if result == "pass" and not evidence.strip():
        print("refused: a pass needs evidence")
        return 1
    st["stages"][stage] = {"result": result, "evidence": evidence, "signature": signature, "soft_note": soft_note,
                           "at": datetime.datetime.now().isoformat(timespec="seconds")}
    hist = st.setdefault("history", [])
    hist.append({"stage": stage, "result": result, "signature": signature})
    save_state(project, st)
    if result == "fail" and signature:
        same = 0
        for h in reversed(hist[:-1]):
            if h["stage"] == stage and h["result"] == "fail":
                if h["signature"] == signature:
                    same += 1
                else:
                    break
        if same >= 2:
            print("ESCALATE: same failure signature 3 times in a row at %s; stop looping and write the one-screen summary" % stage)
        elif same == 1:
            print("CHANGE STRATEGY: same failure signature twice at %s; re-read the failing code path before another attempt" % stage)
        fails = sum(1 for h in hist if h["result"] == "fail")
        if fails >= MAX_ITER:
            print("ESCALATE: %d failed iterations recorded (cap %d)" % (fails, MAX_ITER))
    return 0


def compute_verdict(stages, rung, time_scale, save):
    invalid = []
    if str(time_scale) != "1":
        invalid.append("timeScale %s (verdicts need 1)" % time_scale)
    if save not in ("fresh", "fixture"):
        invalid.append("save state %s (needs fresh or a named fixture)" % save)
    if invalid:
        return "INCONCLUSIVE", invalid
    res = {s: stages.get(s, {}).get("result", "none") for s in STAGES}
    if any(v == "fail" for v in res.values()):
        return "FAIL", [s for s, v in res.items() if v == "fail"]
    if rung == "static" or res["S1"] != "pass":
        return ("STATIC-PASS", ["compile, wiring and play are NOT verified"]) if res["S2"] == "pass" else ("INCONCLUSIVE", ["static stage did not run"])
    missing = [s for s in REQUIRED_FOR_PASS if res[s] != "pass"]
    if missing:
        return "INCONCLUSIVE", ["stages not passed: " + ", ".join(missing)]
    notes = [s for s in STAGES if stages.get(s, {}).get("soft_note")]
    return ("PASS-WITH-NOTES", notes) if notes else ("PASS", [])


def cmd_verdict(a):
    st = load_state(a.project)
    verdict, why = compute_verdict(st["stages"], a.rung, a.time_scale, a.save)
    day = datetime.date.today().isoformat()
    rd = os.path.join(a.project, "docs", "qa", "reports")
    os.makedirs(rd, exist_ok=True)
    base = os.path.join(rd, "%s-%s" % (day, a.task))
    data = {"task": a.task, "date": day, "rung": a.rung, "timeScale": a.time_scale, "save": a.save, "verdict": verdict,
            "reasons": why, "fingerprint": fingerprint(a.project), "stages": st["stages"]}
    with open(base + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
    lines = ["# QA report: %s (%s)" % (a.task, day), "", "Verdict: **%s**  rung: %s  timeScale: %s  save: %s" % (verdict, a.rung, a.time_scale, a.save), "",
             "| Stage | Result | Evidence |", "|---|---|---|"]
    for s in STAGES:
        e = st["stages"].get(s)
        lines.append("| %s | %s | %s |" % (s, e["result"] if e else "not run", (e["evidence"] if e else "").replace("|", "/")[:120]))
    if why:
        lines += ["", "Reasons / not verified: " + "; ".join(why)]
    if verdict in ("STATIC-PASS", "INCONCLUSIVE"):
        lines += ["", "Do not report this work as done."]
    with open(base + ".md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("%s -> %s.md" % (verdict, os.path.relpath(base, a.project)))
    return 0 if verdict in ("PASS", "PASS-WITH-NOTES") else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("static")
    s.add_argument("--project", default=".")
    s.add_argument("--scope", choices=["diff", "full"], default="full")
    s.add_argument("--required-refs")
    s.add_argument("--rules")
    r = sub.add_parser("record")
    r.add_argument("--project", default=".")
    r.add_argument("--stage", required=True, choices=STAGES)
    r.add_argument("--result", required=True, choices=["pass", "fail", "skip"])
    r.add_argument("--evidence", default="")
    r.add_argument("--signature", default="")
    r.add_argument("--soft-note", default="")
    v = sub.add_parser("verdict")
    v.add_argument("--project", default=".")
    v.add_argument("--task", required=True)
    v.add_argument("--rung", choices=["mcp", "batch", "static"], required=True)
    v.add_argument("--time-scale", default="1")
    v.add_argument("--save", default="unknown")
    a = ap.parse_args(argv)
    if a.cmd == "static":
        return cmd_static(a)
    if a.cmd == "record":
        return record(a.project, a.stage, a.result, a.evidence, a.signature, a.soft_note)
    return cmd_verdict(a)


if __name__ == "__main__":
    sys.exit(main())
