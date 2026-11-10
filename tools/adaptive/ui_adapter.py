"""Adapter around the `agent-desktop` CLI (vercel-labs/agent-desktop, Apache-2.0). NOT installed by this repo.

Only documented syntax is used (README summary read 2026-11-10): `snapshot --app X -i [--compact] [--skeleton]
[--root <ref>] [--window-id <id>]`, `click <ref>`, JSON envelope {version, ok, command, data|error}, refs
`@<snapshot_id>:e<n>`, error codes STALE_REF / AMBIGUOUS_TARGET, retry only if error.disposition.retry == 'safe'.
Everything else (find/get/wait flags, timeouts, exact tree child key) is undocumented there and is NOT assumed:
the tree walker is generic and the runner is injectable so the adapter is testable without the binary.
Adapter never decides to prefer accessibility: callers feed outcomes to the selector; too-large or failed
snapshots return a structured `fallback: vision` instead of raising.
"""
import json
import re
import shutil
import subprocess
import time

REF_RE = re.compile(r"^@[A-Za-z0-9]+:e\d+$")
MAX_REFS = 400
MAX_BYTES = 200000


def default_runner(args, timeout_s):
    p = subprocess.run(["agent-desktop"] + args, capture_output=True, text=True, timeout=timeout_s)
    return p.returncode, p.stdout, p.stderr


def installed():
    return shutil.which("agent-desktop") is not None


def walk(node):
    """Yield every dict node in a tree without assuming the child key name."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            if isinstance(v, (list, dict)):
                yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


class AgentDesktop:
    def __init__(self, runner=None, timeout_s=15.0, max_refs=MAX_REFS, max_bytes=MAX_BYTES, log=None):
        self.runner, self.timeout_s, self.max_refs, self.max_bytes = runner or default_runner, timeout_s, max_refs, max_bytes
        self.log = log if log is not None else []

    def _exec(self, args):
        t0 = time.time()
        try:
            code, out, err = self.runner(args, self.timeout_s)
        except FileNotFoundError:
            self._note(args, t0, False, "agent-desktop not installed")
            return {"ok": False, "error": {"code": "NOT_INSTALLED"}}
        except subprocess.TimeoutExpired:
            self._note(args, t0, False, "timeout")
            return {"ok": False, "error": {"code": "TIMEOUT"}}
        size = len(out or "")
        try:
            env = json.loads(out)
        except (ValueError, TypeError):
            self._note(args, t0, False, "non-JSON output")
            return {"ok": False, "error": {"code": "BAD_OUTPUT", "stderr": (err or "")[:200]}}
        env["_bytes"] = size
        self._note(args, t0, bool(env.get("ok")), (env.get("error") or {}).get("code"))
        return env

    def _note(self, args, t0, ok, why):
        self.log.append({"op": args[0], "ms": round((time.time() - t0) * 1000, 1), "ok": ok, "why": why})

    def snapshot(self, app, root=None, skeleton=False, compact=True, window_id=None):
        args = ["snapshot", "--app", app, "-i"]
        if compact:
            args.append("--compact")
        if skeleton:
            args.append("--skeleton")
        if root:
            if not REF_RE.match(root):
                return {"ok": False, "fallback": "vision", "reason": "invalid root ref"}
            args += ["--root", root]
        if window_id:
            args += ["--window-id", str(window_id)]
        env = self._exec(args)
        if not env.get("ok"):
            return {"ok": False, "fallback": "vision", "reason": (env.get("error") or {}).get("code", "error"), "error": env.get("error")}
        data = env.get("data") or {}
        n_refs = data.get("ref_count")
        if (n_refs is not None and n_refs > self.max_refs) or env.get("_bytes", 0) > self.max_bytes:
            return {"ok": False, "fallback": "scope_or_vision", "reason": "snapshot too large (%s refs, %d bytes); "
                    "use skeleton then --root on a target branch, else vision" % (n_refs, env.get("_bytes", 0)),
                    "snapshot_id": data.get("snapshot_id")}
        return {"ok": True, "snapshot_id": data.get("snapshot_id"), "complete": data.get("complete"), "tree": data.get("tree"),
                "ref_count": n_refs}

    @staticmethod
    def resolve(tree, role=None, name=None):
        """Local lookup in an already fetched tree (no extra process call). Returns ref_id or None; ambiguous -> None."""
        hits = [n for n in walk(tree) if n.get("ref_id") and (role is None or n.get("role") == role)
                and (name is None or (n.get("name") or "").strip().lower() == name.strip().lower())]
        return hits[0]["ref_id"] if len(hits) == 1 else None

    def click(self, ref, app=None, role=None, name=None):
        """Click with stale-reference recovery: on STALE_REF re-snapshot (scoped to app) and re-resolve by role+name once,
        only when the error says retry is safe. Failure returns fallback=vision, never an exception."""
        if not REF_RE.match(ref or ""):
            return {"ok": False, "fallback": "vision", "reason": "invalid ref (need @<snapshot>:e<n>)"}
        env = self._exec(["click", ref])
        if env.get("ok"):
            return {"ok": True, "ref": ref}
        err = env.get("error") or {}
        safe = (err.get("disposition") or {}).get("retry") == "safe"
        if err.get("code") in ("STALE_REF", "AMBIGUOUS_TARGET") and safe and app and (role or name):
            snap = self.snapshot(app)
            if snap.get("ok"):
                new = self.resolve(snap["tree"], role, name)
                if new:
                    env2 = self._exec(["click", new])
                    if env2.get("ok"):
                        return {"ok": True, "ref": new, "recovered": True}
        return {"ok": False, "fallback": "vision", "reason": err.get("code", "error")}
