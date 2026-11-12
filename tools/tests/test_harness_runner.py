import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from harness import agents, progress, runner, tasks  # noqa: E402

PY = sys.executable
PROFILES = {"repo-edit": {"claude": {"permission_mode": "acceptEdits", "allowed": ["Read", "Edit", "Write", "Bash(python:*)"], "disallowed": ["Bash(git push:*)"], "max_turns": 20}, "codex": {"sandbox": "workspace-write"}}}


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


def make_repo():
    repo = Path(tempfile.mkdtemp())
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("a")
    (repo / "src.txt").write_text("s")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def task(tid="t1", **over):
    code = "import pathlib,sys; sys.exit(0 if pathlib.Path('docs/out.md').exists() else 1)"
    base = dict(id=tid, title="T " + tid, brief="write docs/out.md", owns=["docs/**"], verify=[{"name": "out-exists", "cmd": [PY, "-c", code]}], max_attempts=2)
    base.update(over)
    return tasks.Task(**base)


class Spy(agents.FakeAgent):
    def __init__(self, fn):
        super().__init__(fn)
        self.briefs = []

    def run(self, brief, task, cwd, profile):
        self.briefs.append(brief)
        return super().run(brief, task, cwd, profile)


def writes_out(brief, task, cwd):
    (Path(cwd) / "docs" / "out.md").write_text("done")


class RunTaskTests(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()
        self.log = str(Path(tempfile.mkdtemp()) / "progress.jsonl")

    def run_task(self, t, fn, **kw):
        agent = Spy(fn)
        status = runner.run_task(t, agent, self.repo, self.log, PROFILES, **kw)
        return status, agent, progress.read(self.log)

    def test_pass_path_records_one_pass(self):
        status, agent, recs = self.run_task(task(), writes_out)
        self.assertEqual(status, "pass")
        self.assertEqual([r["status"] for r in recs], ["pass"])
        self.assertEqual(recs[0]["task"], "t1")

    def test_failed_verifier_triggers_rework_brief_with_evidence(self):
        calls = {"n": 0}

        def fn(brief, t, cwd):
            calls["n"] += 1
            if calls["n"] == 2:
                writes_out(brief, t, cwd)

        status, agent, recs = self.run_task(task(), fn)
        self.assertEqual(status, "pass")
        self.assertEqual([r["status"] for r in recs], ["fail-verify", "pass"])
        self.assertIn("out-exists", agent.briefs[1])
        self.assertIn("Verifier failed", agent.briefs[1])
        self.assertTrue(recs[0]["signature"])

    def test_out_of_scope_edit_is_fail_scope_and_verifier_is_not_run(self):
        def fn(brief, t, cwd):
            writes_out(brief, t, cwd)
            (Path(cwd) / "src.txt").write_text("agent touched")

        status, agent, recs = self.run_task(task(max_attempts=1), fn)
        self.assertEqual(status, "fail-scope")
        self.assertIn("src.txt", json.dumps(recs[0]["violations"]))
        self.assertNotIn("verify", recs[0])

    def test_agent_commit_is_fail_scope(self):
        def fn(brief, t, cwd):
            writes_out(brief, t, cwd)
            git(cwd, "add", "-A")
            git(cwd, "commit", "-qm", "sneaky")

        status, _, recs = self.run_task(task(max_attempts=1), fn)
        self.assertEqual(status, "fail-scope")
        self.assertIn("commit", json.dumps(recs[0]["violations"]))

    def test_agent_nonzero_exit_is_fail_agent(self):
        class Bad(agents.FakeAgent):
            def run(self, brief, task, cwd, profile):
                return agents.AgentResult(1, "agent crashed", 0.1)

        status = runner.run_task(task(max_attempts=1), Bad(lambda *a: None), self.repo, self.log, PROFILES)
        self.assertEqual(status, "fail-agent")

    def test_lock_prevents_a_second_runner(self):
        lock_dir = Path(self.log).parent / "locks"
        lock_dir.mkdir(parents=True)
        (lock_dir / "t1.lock").write_text("other runner")
        status, agent, recs = self.run_task(task(), writes_out)
        self.assertEqual(status, "locked")
        self.assertEqual(agent.briefs, [])

    def test_unknown_permission_profile_is_a_clear_error(self):
        with self.assertRaises(ValueError) as cm:
            self.run_task(task(permission="nope"), writes_out)
        self.assertIn("nope", str(cm.exception))


class RunLoopTests(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()
        d = tempfile.mkdtemp()
        self.log = str(Path(d) / "progress.jsonl")
        self.stop = str(Path(d) / "STOP")

    def loop(self, ts, fn, **kw):
        return runner.run_loop(ts, agents.FakeAgent(fn), self.repo, self.log, PROFILES, stop_file=self.stop, **kw)

    def test_stop_file_halts_before_first_task(self):
        Path(self.stop).write_text("stop")
        res = self.loop([task("a")], writes_out)
        self.assertEqual(res["ran"], [])
        self.assertEqual(res["halted"], "stop-file")

    def test_three_consecutive_failures_halt_the_loop(self):
        ts = [task("t%d" % i, max_attempts=1) for i in range(5)]
        res = self.loop(ts, lambda b, t, c: None, max_consecutive_failures=3)
        self.assertEqual(len(res["ran"]), 3)
        self.assertEqual(res["halted"], "consecutive-failures")

    def test_resumes_after_previous_pass_and_respects_max_tasks(self):
        progress.append(self.log, {"task": "a", "status": "pass"})
        ts = [task("a"), task("b"), task("c")]

        def fn(brief, t, cwd):
            (Path(cwd) / "docs" / "out.md").write_text(t.id)

        res = self.loop(ts, fn, max_tasks=1)
        self.assertEqual(res["ran"], [("b", "pass")])
        self.assertEqual(res["halted"], "max-tasks")


class CommandBuilderTests(unittest.TestCase):
    def test_claude_command(self):
        cmd = agents.ClaudeAgent().build_cmd("do x", task(), PROFILES["repo-edit"])
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("do x", cmd)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "acceptEdits")
        self.assertIn("--allowedTools", cmd)
        self.assertIn("--disallowedTools", cmd)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "20")

    def test_codex_command(self):
        cmd = agents.CodexAgent().build_cmd("do x", task(), PROFILES["repo-edit"], cwd="D:/repo")
        self.assertEqual(cmd[:2], ["codex", "exec"])
        self.assertEqual(cmd[cmd.index("--sandbox") + 1], "workspace-write")
        self.assertEqual(cmd[cmd.index("-C") + 1], "D:/repo")
        self.assertEqual(cmd[-1], "do x")


class AgentTimeoutTests(unittest.TestCase):
    def test_hung_agent_command_is_killed_and_reported(self):
        import time
        t0 = time.time()
        res = agents._run([PY, "-c", "import time; time.sleep(60)"], tempfile.mkdtemp(), 1)
        self.assertEqual(res.exit, -1)
        self.assertIn("TIMEOUT", res.tail)
        self.assertLess(time.time() - t0, 20)

    def test_missing_agent_binary_is_a_failed_result_not_a_crash(self):
        res = agents._run(["definitely-not-an-agent-binary"], tempfile.mkdtemp(), 5)
        self.assertEqual(res.exit, 127)


if __name__ == "__main__":
    unittest.main()
