"""Run a task's verifier commands (argument lists, shell=False). These, not the agent's words, decide pass or fail."""
import hashlib
import os
import re
import signal
import subprocess
import sys
import time

TAIL_CHARS = 1200


def _kill_tree(proc):
    try:
        if sys.platform == "win32":
            r = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            if r.returncode != 0:
                proc.kill()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        proc.kill()


def finish_killed(proc, wait=5):
    """Collect output after a kill without risking a hang: an orphaned grandchild can keep the pipe open forever."""
    try:
        out, _ = proc.communicate(timeout=wait)
        return out or ""
    except subprocess.TimeoutExpired:
        try:
            proc.stdout.close()
        except Exception:
            pass
        return ""


def run_one(item, cwd, default_timeout=300, env=None):
    timeout = item.get("timeout", default_timeout)
    started = time.time()
    res = {"name": item["name"], "cmd": item["cmd"], "exit": None, "timeout": False, "tail": "", "seconds": 0.0}
    try:
        kwargs = {} if sys.platform == "win32" else {"start_new_session": True}
        proc = subprocess.Popen(item["cmd"], cwd=cwd, env=dict(os.environ, **env) if env else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", **kwargs)
    except (FileNotFoundError, OSError) as e:
        res.update(exit=127, tail="command not found or not runnable: %s" % e)
        return res
    try:
        out, _ = proc.communicate(timeout=timeout)
        res["exit"] = proc.returncode
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        out = finish_killed(proc)
        res.update(exit=-1, timeout=True)
    res["tail"] = (out or "")[-TAIL_CHARS:]
    res["seconds"] = round(time.time() - started, 2)
    return res


def run_verifiers(verify, cwd, default_timeout=300, env=None):
    results = []
    for item in verify:
        r = run_one(item, cwd, default_timeout, env)
        results.append(r)
        if r["exit"] != 0:
            return False, results
    return True, results


_PATH = re.compile(r"[A-Za-z]:[\\/][^\s:'\"]+|(?<![\w.])/[^\s:'\"]+")
_ERRORISH = re.compile(r"error|fail|assert|exception|traceback|not found|timeout", re.I)


def signature(result):
    """Stable id for 'the same failure again': numbers and paths stripped from the first error-looking line."""
    lines = [ln.strip() for ln in (result.get("tail") or "").splitlines() if ln.strip()]
    line = next((ln for ln in lines if _ERRORISH.search(ln)), lines[-1] if lines else "no output")
    line = _PATH.sub("<path>", line)
    line = re.sub(r"\d+", "#", line)
    line = re.sub(r"\s+", " ", line)
    return hashlib.sha1((result.get("name", "") + "|" + line).encode("utf-8")).hexdigest()[:12]
