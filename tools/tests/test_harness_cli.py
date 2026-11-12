import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

from harness import cli, tasks  # noqa: E402


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class ShippedDataTests(unittest.TestCase):
    def test_profiles_parse_and_every_task_uses_a_known_profile(self):
        profiles = json.load(open(os.path.join(REPO, "data", "harness", "permissions.json"), encoding="utf-8"))
        for name, p in profiles.items():
            self.assertIn("permission_mode", p["claude"], name)
            self.assertIn("sandbox", p["codex"], name)
        for t in tasks.load_tasks(os.path.join(REPO, "data", "harness", "tasks")):
            self.assertIn(t.permission, profiles, t.id)

    def test_repo_edit_profile_forbids_commit_and_push(self):
        p = json.load(open(os.path.join(REPO, "data", "harness", "permissions.json"), encoding="utf-8"))["repo-edit"]["claude"]
        text = " ".join(p["disallowed"])
        self.assertIn("git commit", text)
        self.assertIn("git push", text)


class CliTests(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        self.paths = ["--progress", str(d / "log" / "progress.jsonl"), "--stop-file", str(d / "STOP"), "--ledger", str(d / "ledger.md")]
        (d / "ledger.md").write_text("| OR-1 | d | words | area | OPEN | x |\n| OR-2 | d | words | area | DONE | x |\n| OR-3 | d | words | area | IN PROGRESS | x |\n", encoding="utf-8")
        self.d = d

    def test_status_on_empty_progress(self):
        code, out = run(["status"] + self.paths)
        self.assertEqual(code, 0)
        self.assertIn("no progress yet", out)
        self.assertIn("open ledger rows: 2", out)
        self.assertIn("stop file: absent", out)

    def test_status_shows_stop_file(self):
        (self.d / "STOP").write_text("x")
        self.assertIn("stop file: PRESENT", run(["status"] + self.paths)[1])

    def test_run_with_fake_agent_records_failures_and_halts(self):
        code, out = run(["run", "--agent", "fake", "--max-tasks", "1", "--no-train"] + self.paths)
        recs = [json.loads(l) for l in open(self.d / "log" / "progress.jsonl", encoding="utf-8")]
        self.assertTrue(recs)
        self.assertEqual(recs[0]["agent"], "fake")
        self.assertIn("halted", out)


if __name__ == "__main__":
    unittest.main()
