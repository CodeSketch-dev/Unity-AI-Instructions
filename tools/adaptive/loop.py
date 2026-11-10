"""Execution loop: EXECUTE -> VERIFY -> MEASURE (+ failure path DETECT -> DIAGNOSE -> FALLBACK -> RETRY SAFELY).

Safety rules enforced here, not by convention:
- every attempt has a timeout; total attempts are capped; an emergency STOP file/env halts before each attempt;
- no verification => no success (status 'no_verification' unless allow_unverified, then verified=0 and not learned as success);
- a non-idempotent step that failed or timed out is NEVER retried and never falls back unless its state_check
  proves 'not_applied'; otherwise the loop stops with 'needs_manual_check'.
Timing split: tool_ms (measured), wait_ms/model_ms/tokens only if the step reports them via ctx; else UNKNOWN (NULL).
"""
import concurrent.futures
import os
import subprocess
import time

from . import store


class Step:
    def __init__(self, name, fn, verify=None, idempotent=True, timeout_s=30.0, state_check=None):
        self.name, self.fn, self.verify = name, fn, verify
        self.idempotent, self.timeout_s, self.state_check = idempotent, timeout_s, state_check


def stop_file():
    return os.path.join(store.home(), "STOP")


def request_stop():
    os.makedirs(store.home(), exist_ok=True)
    open(stop_file(), "w").write(str(time.time()))


def clear_stop():
    if os.path.exists(stop_file()):
        os.remove(stop_file())


def stop_requested():
    return os.environ.get("ADAPTIVE_STOP") == "1" or os.path.exists(stop_file())


def run_command(cmd, timeout_s=60, cwd=None):
    """Deterministic CLI helper: returns (returncode, tail of stdout+stderr). Kills on timeout."""
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=cwd)
    return p.returncode, ((p.stdout or "") + (p.stderr or ""))[-2000:]


def _call(step, ctx):
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(step.fn, ctx)
    try:
        return fut.result(timeout=step.timeout_s), None
    except concurrent.futures.TimeoutError:
        return None, "timeout after %.1fs" % step.timeout_s
    except Exception as e:  # noqa: BLE001
        return None, "%s: %s" % (type(e).__name__, e)
    finally:
        ex.shutdown(wait=False, cancel_futures=True)


def run(steps, category, env, conn=None, max_attempts=4, max_retries_same=1, predicted_p=None, allow_unverified=False,
        task_fp=None, backoff_s=0.0):
    attempts, first_fail_ts, retries = [], None, 0
    first = True
    for step in steps:
        same_retries = 0
        while True:
            if stop_requested():
                return {"status": "stopped", "attempts": attempts, "reason": "emergency stop"}
            if len(attempts) >= max_attempts:
                return {"status": "exhausted", "attempts": attempts, "reason": "max_attempts"}
            ctx = {"wait_ms": None, "model_ms": None, "tool_calls": 1, "in_tok": None, "out_tok": None, "cache_tok": None}
            t0 = time.time()
            result, err = _call(step, ctx)
            t1 = time.time()
            lat = (t1 - t0) * 1000.0
            verified = None
            if err is None:
                try:
                    verified = step.verify(result, ctx) if step.verify else None
                except Exception as e:  # noqa: BLE001
                    err = "verify failed: %s" % e
            ok = err is None and verified is True
            unverified = err is None and verified is None
            if unverified and not allow_unverified:
                err = "no verification available"
            rec = dict(category=category, env=env, method=step.name, success=ok or (unverified and allow_unverified),
                       verified=ok, latency_ms=lat, tool_ms=lat, wait_ms=ctx["wait_ms"], model_ms=ctx["model_ms"],
                       tool_calls=ctx["tool_calls"], in_tok=ctx["in_tok"], out_tok=ctx["out_tok"], cache_tok=ctx["cache_tok"],
                       retries=retries, fail_reason=None if (ok or unverified and allow_unverified) else (err or "verification false"),
                       predicted_p=predicted_p if first else None, ts_start=t0, ts_end=t1, task_fp=task_fp)
            first = False
            if ok:
                if first_fail_ts:
                    rec["recovery_ms"] = (t1 - first_fail_ts) * 1000.0
                attempts.append(rec)
                if conn:
                    store.record_run(conn, **rec)
                return {"status": "ok", "method": step.name, "result": result, "attempts": attempts}
            attempts.append(rec)
            if conn:
                store.record_run(conn, **rec)
            if unverified and not allow_unverified:
                return {"status": "no_verification", "attempts": attempts, "reason": "cannot verify result; stopping"}
            if unverified and allow_unverified:
                return {"status": "unverified", "method": step.name, "result": result, "attempts": attempts}
            first_fail_ts = first_fail_ts or t1
            retries += 1
            if not step.idempotent:
                state = step.state_check() if step.state_check else None
                if state != "not_applied":
                    return {"status": "needs_manual_check", "attempts": attempts,
                            "reason": "non-idempotent step '%s' failed; state unknown, not retrying" % step.name}
                break  # proven untouched: safe to fall back (no same-step retry)
            transient = err is not None
            if transient and same_retries < max_retries_same:
                same_retries += 1
                if backoff_s:
                    time.sleep(backoff_s)
                continue
            break
    return {"status": "failed", "attempts": attempts, "reason": "all methods failed"}
