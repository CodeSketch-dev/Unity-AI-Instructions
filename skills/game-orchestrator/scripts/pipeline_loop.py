"""Run one bounded, evidence-driven local pipeline iteration.

This controller owns only offline orchestration. It can lint the GDD and run a
cheap balance simulation when artifacts exist, but it never marks Unity,
Editor, PlayMode, or build work as passed without an adapter supplying real
evidence. State is written through the resumable orchestrator state file.

Usage:
  py -I pipeline_loop.py run <gdd-dir> --project <project-root> [--max-iterations 5]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gdd_lint  # noqa: E402
import evidence_index  # noqa: E402
import orchestrator  # noqa: E402
import skill_context  # noqa: E402

BALANCE = os.path.normpath(os.path.join(HERE, "..", "..", "auto-balance-game", "scripts"))
sys.path.insert(0, BALANCE)
import econ_sim  # noqa: E402

MAX_REPAIR_ATTEMPTS = 3


@contextmanager
def loop_lock(project):
    """Prevent two local loop runners from overwriting the same state."""
    path = os.path.join(project, "docs", "orchestrator", "pipeline-loop.lock")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("pid=%s\ntime=%s\n" % (os.getpid(), time.time()))
    except FileExistsError as exc:
        raise RuntimeError("pipeline loop is already running: %s" % path) from exc
    try:
        yield
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _task_id(state, key):
    for task in state["tasks"].values():
        if task.get("key") == key and task.get("system") == "pipeline":
            return task["id"]
    return None


def _ensure_state(gdd_dir, project):
    state_path = orchestrator.paths(project)[0]
    if os.path.isfile(state_path):
        state, _ = orchestrator.resume(project)
        return state
    return orchestrator.init(gdd_dir, project)


def _signature(findings):
    parts = ["%s:%s:%s" % (f.sev, f.rule, f.where) for f in findings if f.sev == "BLOCK"]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12] if parts else ""


def _repair(state, signature, stage, evidence):
    queue = state.setdefault("loop", {}).setdefault("repair_queue", [])
    item = next((x for x in queue if x["signature"] == signature), None)
    if item is None:
        item = {"signature": signature, "stage": stage, "attempts": 0, "blocked": False,
                "next_action": "inspect the first failing rule and patch its owning source"}
        queue.append(item)
    item["attempts"] += 1
    item["last_evidence"] = evidence
    item["blocked"] = item["attempts"] >= MAX_REPAIR_ATTEMPTS
    if item["blocked"]:
        item["next_action"] = "escalate to human or choose a documented scope/fidelity fallback"
    return item


def _record_gate(state, name, result, evidence, signature=""):
    state.setdefault("loop", {}).setdefault("gates", {})[name] = {
        "result": result, "evidence": evidence, "signature": signature,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def _mark_task(project, state, key, passed, evidence, signature=""):
    tid = _task_id(state, key)
    if not tid:
        return state
    task = state["tasks"][tid]
    if passed:
        if task["status"] == "pending":
            orchestrator.mark(project, tid, "in_progress", agent="pipeline-loop")
            state = orchestrator.load(project)
            orchestrator.mark(project, tid, "done", evidence=[evidence], agent="pipeline-loop")
        return orchestrator.load(project)
    if task["status"] == "pending":
        orchestrator.mark(project, tid, "in_progress", agent="pipeline-loop")
        state = orchestrator.load(project)
        orchestrator.mark(project, tid, "failed", evidence=[evidence], note=signature, agent="pipeline-loop")
        return orchestrator.load(project)
    return state


def _run_unity_placeholder(state):
    _record_gate(state, "unity", "inconclusive",
                 "Unity adapter not supplied; compile, serialized wiring, PlayMode and build were not run.")


def _run_mapspec_gate(gdd_dir, project, state):
    task_id = _task_id(state, "visual-mapspec")
    if task_id and any(state["tasks"][dep]["status"] != "done" for dep in state["tasks"][task_id]["depends_on"]):
        _record_gate(state, "visual-mapspec", "inconclusive", "visual-evidence dependency not complete")
        return state
    path = os.path.join(gdd_dir, "_generated", "map-spec.json")
    if not os.path.isfile(path):
        _record_gate(state, "visual-mapspec", "inconclusive", "map-spec.json not generated")
        return state
    with open(path, encoding="utf-8") as stream:
        reasons = evidence_index.validate_mapspec_artifact(json.load(stream))
    evidence = "MapSpec schema valid: %s" % path if not reasons else "MapSpec invalid: " + ", ".join(reasons)
    _record_gate(state, "visual-mapspec", "pass" if not reasons else "fail", evidence)
    return _mark_task(project, state, "visual-mapspec", not reasons, evidence)


def _write_active_context(project, state):
    """Expose only the current ready task's skill names to the next agent turn."""
    ready = orchestrator.ready(state, max_file=1)
    requested = ready[0].get("skills", []) if ready else []
    always_on = ["game-orchestrator", "multi-agent-coexistence", "token-efficient-workflow"]
    available = [name for name in os.listdir(os.path.normpath(os.path.join(HERE, "..", "..")))
                 if os.path.isdir(os.path.join(os.path.normpath(os.path.join(HERE, "..", "..")), name))]
    path = os.path.join(project, "docs", "orchestrator", "active-skills.json")
    previous = []
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as stream:
                previous = json.load(stream).get("active", [])
        except (OSError, ValueError):
            previous = []
    return skill_context.write_manifest(path, requested, always_on, "phase-%s" % state.get("phase", 0), available, previous)


def run_once(gdd_dir, project, max_iterations=5):
    """Run at most one iteration and persist all evidence in orchestrator state."""
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    with loop_lock(project):
        state = _ensure_state(gdd_dir, project)
        _write_active_context(project, state)
        loop = state.setdefault("loop", {})
        loop.setdefault("iteration", 0)
        loop.setdefault("history", [])
        loop.setdefault("repair_queue", [])
        loop.setdefault("gates", {})
        if loop.get("iteration", 0) >= max_iterations:
            return {"status": "stopped", "reason": "iteration cap reached", "iteration": loop["iteration"]}
        loop["iteration"] = loop.get("iteration", 0) + 1

        g = gdd_lint.load_gdd(gdd_dir)
        evidence_path = os.path.join(gdd_dir, "_generated", "evidence-index.json")
        evidence_data = evidence_index.write(gdd_dir, evidence_path)
        evidence_check = evidence_index.validate_for_mapspec(evidence_data, require_images=False)
        findings = gdd_lint.lint(g, last_hash=state.get("gdd_hash"))
        generated = os.path.join(gdd_dir, "_generated")
        gdd_lint.write_reports(g, findings, generated)
        blocks = [f for f in findings if f.sev == "BLOCK"]
        gdd_evidence = "GDD lint: %d BLOCK, %d WARN; report %s" % (
            len(blocks), sum(f.sev == "WARN" for f in findings),
            os.path.join(generated, "lint-report.md"))
        if evidence_check:
            gdd_evidence += "; evidence index: " + ", ".join(evidence_check)
            blocks = list(blocks) + [type("EvidenceFinding", (), {"sev": "BLOCK", "rule": "evidence-index", "where": evidence_path})()]
        gdd_sig = _signature(findings)
        if blocks:
            repair = _repair(state, gdd_sig, "gdd", gdd_evidence)
            _record_gate(state, "gdd", "fail" if not repair["blocked"] else "blocked", gdd_evidence, gdd_sig)
            orchestrator.save(project, state)
            state = _mark_task(project, state, "lint", False, gdd_evidence, gdd_sig)
        else:
            _record_gate(state, "gdd", "pass", gdd_evidence)
            orchestrator.save(project, state)
            state = _mark_task(project, state, "lint", True, gdd_evidence)
        loop = state.setdefault("loop", {})
        loop.setdefault("iteration", 0)
        loop.setdefault("history", [])
        loop.setdefault("repair_queue", [])
        loop.setdefault("gates", {})

        balance_path = os.path.join(generated, "balance-plan.json")
        if os.path.isfile(balance_path) and not blocks:
            with open(balance_path, encoding="utf-8") as stream:
                balance = econ_sim.tune(json.load(stream))
            balance_evidence = "balance simulation %s: %d iteration(s)" % (balance["status"], balance["iterations"])
            _record_gate(state, "balance", "pass" if balance["status"] == "converged" else balance["status"], balance_evidence)
        else:
            _record_gate(state, "balance", "inconclusive", "balance-plan.json not available or GDD lint is blocked")

        state = _run_mapspec_gate(gdd_dir, project, state)

        _run_unity_placeholder(state)
        failed = any(v["result"] in ("fail", "blocked", "not-converged") for v in state["loop"]["gates"].values())
        blocked = any(v["result"] == "blocked" for v in state["loop"]["gates"].values())
        status = "blocked" if blocked else ("fail" if failed else "inconclusive")
        result = {"status": status, "iteration": loop["iteration"], "gates": state["loop"]["gates"],
                  "repair_queue": state["loop"]["repair_queue"],
                  "evidence_contract": {name: gate.get("evidence", "") for name, gate in state["loop"]["gates"].items()}}
        loop["history"].append(result)
        orchestrator.recompute(state)
        orchestrator.save(project, state)
        orchestrator.log(project, "loop | iteration %d | %s" % (loop["iteration"], status))
        return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("gdd_dir")
    run.add_argument("--project", required=True)
    run.add_argument("--max-iterations", type=int, default=5)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        print(json.dumps(run_once(args.gdd_dir, args.project, args.max_iterations), indent=1))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
