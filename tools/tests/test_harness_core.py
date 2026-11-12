import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from harness import progress, tasks  # noqa: E402


def write_task(d, name, **over):
    t = {"id": name, "title": "T " + name, "brief": "do it", "owns": ["docs/**"], "verify": [{"name": "ok", "cmd": ["python", "-c", "pass"]}], "permission": "repo-edit"}
    t.update(over)
    Path(d, name + ".json").write_text(json.dumps(t), encoding="utf-8")


class TasksTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_load_sorted_and_defaults(self):
        write_task(self.d, "b-task")
        write_task(self.d, "a-task", max_attempts=3, kind="train")
        ts = tasks.load_tasks(self.d)
        self.assertEqual([t.id for t in ts], ["a-task", "b-task"])
        self.assertEqual((ts[0].max_attempts, ts[0].kind), (3, "train"))
        self.assertEqual((ts[1].max_attempts, ts[1].kind), (2, "work"))

    def test_validation_names_the_bad_field(self):
        write_task(self.d, "bad", verify=[])
        with self.assertRaises(ValueError) as cm:
            tasks.load_tasks(self.d)
        self.assertIn("bad", str(cm.exception))
        self.assertIn("verify", str(cm.exception))

    def test_verify_cmd_must_be_an_argument_list(self):
        write_task(self.d, "shellish", verify=[{"name": "x", "cmd": "echo hi"}])
        with self.assertRaises(ValueError) as cm:
            tasks.load_tasks(self.d)
        self.assertIn("cmd", str(cm.exception))


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.p = os.path.join(tempfile.mkdtemp(), "log", "progress.jsonl")

    def test_append_and_read_skips_corrupt_lines(self):
        progress.append(self.p, {"task": "a", "status": "fail-verify"})
        with open(self.p, "a", encoding="utf-8") as f:
            f.write("{not json\n")
        progress.append(self.p, {"task": "a", "status": "pass"})
        recs = progress.read(self.p)
        self.assertEqual([r["status"] for r in recs], ["fail-verify", "pass"])
        self.assertTrue(all("ts" in r for r in recs))

    def test_read_missing_file_is_empty(self):
        self.assertEqual(progress.read(self.p), [])

    def test_next_task_skips_passed(self):
        d = tempfile.mkdtemp()
        write_task(d, "a")
        write_task(d, "b")
        ts = tasks.load_tasks(d)
        recs = [{"task": "a", "status": "pass"}]
        self.assertEqual(progress.next_task(ts, recs).id, "b")
        recs.append({"task": "b", "status": "pass"})
        self.assertIsNone(progress.next_task(ts, recs))

    def test_summary_lists_last_status_per_task(self):
        md = os.path.join(tempfile.mkdtemp(), "progress.md")
        recs = [{"task": "a", "status": "fail-verify", "ts": "t1"}, {"task": "a", "status": "pass", "ts": "t2"}, {"task": "b", "status": "fail-scope", "ts": "t3"}]
        progress.write_summary(recs, md)
        text = open(md, encoding="utf-8").read()
        self.assertIn("| a | pass |", text)
        self.assertIn("| b | fail-scope |", text)


if __name__ == "__main__":
    unittest.main()
