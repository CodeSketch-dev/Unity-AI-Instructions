"""Agent adapters. The harness talks to Claude Code and Codex only through their non-interactive CLIs
(`claude -p`, `codex exec`) so the same task file works for either. Command builders are pure and unit-tested;
nothing here trusts the agent's own claim of success (verify.py and scope.py decide)."""
import json
import subprocess
import sys
import time
from dataclasses import dataclass

from . import verify


@dataclass
class AgentResult:
    exit: int
    tail: str
    seconds: float


def load_profiles(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _run(cmd, cwd, timeout):
    started = time.time()
    try:
        kwargs = {} if sys.platform == "win32" else {"start_new_session": True}
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", **kwargs)
    except (FileNotFoundError, OSError) as e:
        return AgentResult(127, "agent command not found or not runnable: %s" % e, 0.0)
    try:
        out, _ = proc.communicate(timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        verify._kill_tree(proc)
        out = verify.finish_killed(proc)
        code = -1
        out = "TIMEOUT after %ss\n%s" % (timeout, out or "")
    return AgentResult(code, (out or "")[-verify.TAIL_CHARS:], round(time.time() - started, 2))


class Agent:
    name = "agent"

    def run(self, brief, task, cwd, profile):  # pragma: no cover - interface
        raise NotImplementedError


class FakeAgent(Agent):
    """Test double: runs fn(brief, task, cwd) and reports success."""
    name = "fake"

    def __init__(self, fn):
        self.fn = fn

    def run(self, brief, task, cwd, profile):
        self.fn(brief, task, cwd)
        return AgentResult(0, "fake agent ok", 0.0)


class ClaudeAgent(Agent):
    name = "claude"

    def __init__(self, model=""):
        self.model = model

    def build_cmd(self, brief, task, profile):
        c = profile["claude"]
        cmd = ["claude", "-p", brief, "--permission-mode", c["permission_mode"], "--output-format", "json", "--max-turns", str(c["max_turns"])]
        if self.model:
            cmd += ["--model", self.model]
        if c.get("allowed"):
            cmd += ["--allowedTools", *c["allowed"]]
        if c.get("disallowed"):
            cmd += ["--disallowedTools", *c["disallowed"]]
        return cmd

    def run(self, brief, task, cwd, profile):
        return _run(self.build_cmd(brief, task, profile), cwd, task.extra.get("agent_timeout", 1800))


class CodexAgent(Agent):
    name = "codex"

    def build_cmd(self, brief, task, profile, cwd="."):
        return ["codex", "exec", "--sandbox", profile["codex"]["sandbox"], "-C", str(cwd), brief]

    def run(self, brief, task, cwd, profile):
        return _run(self.build_cmd(brief, task, profile, cwd), cwd, task.extra.get("agent_timeout", 1800))


def make_agent(name, model=""):
    if name == "claude":
        return ClaudeAgent(model)
    if name == "codex":
        return CodexAgent()
    raise ValueError("unknown agent '%s' (claude or codex)" % name)
