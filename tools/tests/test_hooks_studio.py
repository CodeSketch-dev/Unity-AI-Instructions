import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(HERE, "..", "..", "hooks", "scripts")
sys.path.insert(0, HOOKS)

import agent_artifact_check  # noqa: E402
import agent_audit_log  # noqa: E402
import big_read_guard  # noqa: E402


def run(script, event, project):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project)
    return subprocess.run([sys.executable, "-I", os.path.join(HOOKS, script)], input=json.dumps(event), capture_output=True,
                          text=True, env=env, timeout=30)


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.environ["CLAUDE_PROJECT_DIR"] = self.d

    def tearDown(self):
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
        shutil.rmtree(self.d)


class ArtifactTests(Base):
    def transcript(self, prompt):
        p = os.path.join(self.d, "t.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
        return p

    def ev(self, prompt):
        return {"agent_type": "qa-tester", "agent_transcript_path": self.transcript(prompt), "cwd": self.d}

    def test_missing_report_warns(self):
        msg = agent_artifact_check.decide(self.ev("Do X. Report file: `docs/reports/a.md`"))
        self.assertIn("docs/reports/a.md", msg)

    def test_present_report_ok(self):
        os.makedirs(os.path.join(self.d, "docs", "reports"))
        with open(os.path.join(self.d, "docs", "reports", "a.md"), "w") as f:
            f.write("done")
        self.assertIsNone(agent_artifact_check.decide(self.ev("Write your report to `docs/reports/a.md`")))

    def test_placeholder_and_no_contract_ignored(self):
        self.assertIsNone(agent_artifact_check.decide(self.ev("Report file: `<path>`")))
        self.assertIsNone(agent_artifact_check.decide(self.ev("just do it")))

    def test_cli_is_advisory(self):
        r = run("agent_artifact_check.py", self.ev("Report file: `x/missing.md`"), self.d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("systemMessage", r.stdout)
        self.assertEqual(run("agent_artifact_check.py", {}, self.d).returncode, 0)


class AuditTests(Base):
    def test_log_written_and_untyped_skipped(self):
        r = run("agent_audit_log.py", {"hook_event_name": "SubagentStop", "agent_type": "reviewer", "agent_id": "a1",
                                       "last_assistant_message": "all   good\nline"}, self.d)
        self.assertEqual(r.returncode, 0)
        run("agent_audit_log.py", {"agent_id": "internal"}, self.d)
        with open(os.path.join(self.d, "docs", "pipeline", "agent-log.jsonl"), encoding="utf-8") as f:
            rows = [json.loads(x) for x in f]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["summary"], "all good line")

    def test_garbage_stdin_never_fails(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.d)
        r = subprocess.run([sys.executable, "-I", os.path.join(HOOKS, "agent_audit_log.py")], input="not json", capture_output=True,
                           text=True, env=env)
        self.assertEqual(r.returncode, 0)


class ReadGuardTests(Base):
    def big(self, name="big.md", kb=100):
        p = os.path.join(self.d, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write("# Title\n" + ("text line\n" * 10) + "## Section B\n" + "x" * 1023 + "\n") 
            for _ in range(kb):
                f.write("y" * 1023 + "\n")
        return p

    def ev(self, p, **kw):
        return {"tool_name": "Read", "tool_input": dict({"file_path": p}, **kw), "cwd": self.d}

    def test_refuses_then_allows_repeat(self):
        p = self.big()
        msg = big_read_guard.decide(self.ev(p))
        self.assertIn("## Section B", msg)
        self.assertIsNone(big_read_guard.decide(self.ev(p)))  # second attempt passes

    def test_bounded_small_code_and_off(self):
        p = self.big()
        self.assertIsNone(big_read_guard.decide(self.ev(p, limit=200)))
        self.assertIsNone(big_read_guard.decide(self.ev(self.big("a.cs"))))
        small = os.path.join(self.d, "s.md")
        with open(small, "w") as f:
            f.write("# hi\n")
        self.assertIsNone(big_read_guard.decide(self.ev(small)))
        os.environ["STUDIO_READ_GUARD"] = "off"
        try:
            self.assertIsNone(big_read_guard.decide(self.ev(self.big("c.md"))))
        finally:
            os.environ.pop("STUDIO_READ_GUARD")

    def test_cli_exit_codes(self):
        p = self.big("d.md")
        self.assertEqual(run("big_read_guard.py", self.ev(p), self.d).returncode, 2)
        self.assertEqual(run("big_read_guard.py", {"tool_name": "Bash"}, self.d).returncode, 0)


class SessionStartTests(Base):
    def test_backlog_and_rigor(self):
        f = os.path.join(self.d, "docs", "factory")
        os.makedirs(f)
        with open(os.path.join(f, "STUDIO-LOOP-2026-01-01.md"), "w") as fh:
            fh.write("- [x] a\n- [ ] do next thing\n## LOG\n- did stuff\n")
        with open(os.path.join(self.d, "AGENTS.md"), "w") as fh:
            fh.write("rigor: standard\n")
        r = run("session_start.py", {"cwd": self.d}, self.d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("1 open", r.stdout)
        self.assertIn("do next thing", r.stdout)
        self.assertIn("rigor (AGENTS.md): rigor: standard", r.stdout)


if __name__ == "__main__":
    unittest.main()
