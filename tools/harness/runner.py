"""Task runner: brief -> agent -> scope check -> verifiers -> progress record, with rework on failure and hard loop limits.
Limits are code: max tasks, max attempts, max consecutive failures, STOP file, per-command timeouts, per-task lock.
Scope is always judged against the state BEFORE ATTEMPT 1, so a rework attempt can never launder an earlier violation."""
import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from . import progress, scope, verify

LOCK_STALE_SECONDS = 2 * 3600
TAIL = 600


def build_brief(task, failure=None, attempt=1):
    lines = ["You are working under the studio harness.", "Task %s: %s" % (task.id, task.title), "", task.brief, "",
             "Rules: change only files matching: %s. Do not commit, push, publish or edit settings files." % ", ".join(task.owns),
             "Verifiers that will judge the result (exit 0 = pass):"]
    lines += ["- %s: %s" % (v["name"], " ".join(v["cmd"])) for v in task.verify]
    lines += ["Read the matching skills first. When finished, stop: do not claim success, the verifiers decide."]
    if failure:
        lines += ["", "Attempt %d. The previous attempt failed." % attempt, failure, "Fix the cause; do not patch the symptom."]
    return "\n".join(lines)


def _lock_path(progress_path, task_id):
    return Path(progress_path).parent / "locks" / (task_id + ".lock")


def _take_lock(path, token):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and time.time() - path.stat().st_mtime > LOCK_STALE_SECONDS:
        path.unlink()
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, token.encode())
    os.close(fd)
    return True


def _touch(path):
    try:
        os.utime(str(path), None)
    except OSError:
        pass


def _release(path, token):
    """Delete the lock only if it is still ours (another runner may have taken over a stale one)."""
    try:
        if path.read_text() == token:
            path.unlink()
    except OSError:
        pass


def _read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def _forbidden(profile):
    return profile.get("forbidden", scope.DEFAULT_FORBIDDEN)


def _runner_owned(rel, repo, progress_path):
    """Files the harness itself writes during a run (progress, summary, locks, baselines) are not the agent's changes."""
    try:
        base = Path(progress_path).resolve().parent.relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        return False
    return rel.startswith(base + "/")


def run_task(task, agent, repo, progress_path, profiles, extra_watch=None):
    if task.permission not in profiles:
        raise ValueError("task '%s': unknown permission profile '%s' (known: %s)" % (task.id, task.permission, ", ".join(sorted(profiles))))
    profile = profiles[task.permission]
    lock = _lock_path(progress_path, task.id)
    token = "%d-%s" % (os.getpid(), uuid.uuid4().hex)
    if not _take_lock(lock, token):
        return "locked"
    try:
        baseline = scope.snapshot(repo, extra_watch)
        base_file = Path(progress_path).parent / "baselines" / (task.id + ".json")
        base_file.parent.mkdir(parents=True, exist_ok=True)
        base_file.write_text(json.dumps(baseline), encoding="utf-8")
        env = {"HARNESS_BASELINE": str(base_file)}
        good_progress = _read_bytes(progress_path)
        status, failure = "fail-agent", None
        for attempt in range(1, task.max_attempts + 1):
            _touch(lock)
            brief = build_brief(task, failure, attempt)
            res = agent.run(brief, task, repo, profile)
            rec = {"task": task.id, "kind": task.kind, "attempt": attempt, "agent": agent.name, "agent_seconds": res.seconds}
            changed = [p for p in scope.changed_since(baseline, scope.snapshot(repo, extra_watch)) if not _runner_owned(p, repo, progress_path)]
            violations = scope.check_scope(changed, task.owns, _forbidden(profile))
            if _read_bytes(progress_path) != good_progress:  # only the harness may write the progress file
                violations.append("progress file was modified by the agent (only the harness may write it)")
                if good_progress is None:
                    try:
                        os.remove(progress_path)
                    except OSError:
                        pass
                else:
                    Path(progress_path).write_bytes(good_progress)
            if res.exit != 0:
                rec["agent_tail"] = res.tail[-TAIL:]
            if violations:
                status = "fail-scope"
                rec.update(status=status, violations=violations, signature=verify.signature({"name": "scope", "tail": violations[0]}))
                failure = "Scope violation: %s. Revert the out-of-scope changes and keep only changes inside the allowed paths." % "; ".join(violations)
            elif res.exit != 0:
                status = "fail-agent"
                rec.update(status=status, signature=verify.signature({"name": "agent", "tail": res.tail}))
                failure = "The agent run failed (exit %s): %s" % (res.exit, res.tail[-TAIL:])
            else:
                ok, results = verify.run_verifiers(task.verify, repo, env=env)
                slim = [{"name": r["name"], "exit": r["exit"], "timeout": r["timeout"], "tail": r["tail"][-TAIL:]} for r in results]
                if ok:
                    status = "pass"
                    rec.update(status=status, verify=slim)
                else:
                    bad = results[-1]
                    status = "fail-verify"
                    rec.update(status=status, verify=slim, signature=verify.signature(bad))
                    failure = "Verifier failed: %s (exit %s)\n--- output tail ---\n%s" % (bad["name"], bad["exit"], bad["tail"][-TAIL:])
            progress.append(progress_path, rec)
            good_progress = _read_bytes(progress_path)
            if status == "pass":
                break
        return status
    finally:
        _release(lock, token)


def run_loop(tasks, agent, repo, progress_path, profiles, max_tasks=5, stop_file=None, max_consecutive_failures=3, extra_watch=None, ignore_done=False):
    ran, consecutive, halted, attempted = [], 0, None, set()
    while True:
        if stop_file and os.path.exists(stop_file):
            halted = "stop-file"
            break
        if len(ran) >= max_tasks:
            halted = "max-tasks"
            break
        done = set() if ignore_done else progress.done_ids(progress.read(progress_path))
        remaining = [t for t in tasks if t.id not in done and t.id not in attempted]
        if not remaining:
            halted = "no-tasks"
            break
        t = remaining[0]
        attempted.add(t.id)
        status = run_task(t, agent, repo, progress_path, profiles, extra_watch)
        if status == "locked":
            continue
        ran.append((t.id, status))
        consecutive = 0 if status == "pass" else consecutive + 1
        if consecutive >= max_consecutive_failures:
            halted = "consecutive-failures"
            break
    progress.write_summary(progress.read(progress_path), str(Path(progress_path).with_name("progress.md")))
    return {"ran": ran, "halted": halted}
