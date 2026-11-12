import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
LINT = os.path.abspath(os.path.join(HERE, "..", "lint"))

from harness import check_added, miner, tasks  # noqa: E402


def rec(task, status, sig, **extra):
    r = {"task": task, "status": status, "signature": sig, "verify": [{"name": "v", "exit": 1, "timeout": False, "tail": "Error: example for " + sig}]}
    r.update(extra)
    return r


class MinerTests(unittest.TestCase):
    def test_same_signature_twice_becomes_one_candidate_ranked_by_count(self):
        recs = [rec("a", "fail-verify", "s1"), rec("b", "fail-verify", "s1"), rec("c", "fail-verify", "s2"), rec("d", "fail-verify", "s2"), rec("e", "fail-verify", "s2"), rec("f", "fail-verify", "once")]
        cands = miner.mine(recs, min_count=2)
        self.assertEqual([(c.signature, c.count) for c in cands], [("s2", 3), ("s1", 2)])
        self.assertEqual(cands[1].task_ids, ["a", "b"])
        self.assertIn("example for s1", cands[1].example)

    def test_passes_and_unsigned_records_are_ignored(self):
        recs = [{"task": "a", "status": "pass"}, {"task": "b", "status": "pass"}, {"task": "c", "status": "fail-agent"}, {"task": "d", "status": "fail-agent"}]
        self.assertEqual(miner.mine(recs), [])

    def test_candidates_file_is_regenerated_idempotently(self):
        md = os.path.join(tempfile.mkdtemp(), "candidates.md")
        cands = miner.mine([rec("a", "fail-verify", "s1"), rec("b", "fail-verify", "s1")])
        miner.write_candidates(cands, md)
        first = open(md, encoding="utf-8").read()
        miner.write_candidates(cands, md)
        self.assertEqual(first, open(md, encoding="utf-8").read())
        self.assertIn("s1", first)

    def test_train_task_is_valid_scoped_and_not_overwritten(self):
        d = tempfile.mkdtemp()
        cand = miner.mine([rec("a", "fail-verify", "s1"), rec("b", "fail-verify", "s1")])[0]
        p = miner.make_train_task(cand, d)
        ts = tasks.load_tasks(d)
        self.assertEqual(len(ts), 1)
        t = ts[0]
        self.assertEqual((t.kind, t.id), ("train", "train-s1"))
        self.assertIn("skills/**", t.owns)
        self.assertIn("tools/lint/rules/**", t.owns)
        self.assertIn("capture-pattern-with-lint", t.brief)
        names = [v["name"] for v in t.verify]
        self.assertIn("adds-new-only", names)
        self.assertIn("lint-tests", names)
        before = Path(p).read_text()
        Path(p).write_text(before + " ")
        miner.make_train_task(cand, d)
        self.assertEqual(Path(p).read_text(), before + " ")


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


class CheckAddedTests(unittest.TestCase):
    def repo(self):
        r = Path(tempfile.mkdtemp())
        git(r, "init", "-q")
        git(r, "config", "user.email", "t@t")
        git(r, "config", "user.name", "t")
        (r / "skills" / "ui" / "old").mkdir(parents=True)
        (r / "skills" / "ui" / "old" / "SKILL.md").write_text("old")
        (r / "tools" / "lint" / "rules").mkdir(parents=True)
        git(r, "add", "-A")
        git(r, "commit", "-qm", "i")
        return r

    def test_new_rule_file_passes(self):
        r = self.repo()
        (r / "tools" / "lint" / "rules" / "new_rule.py").write_text("x")
        self.assertEqual(check_added.check(r), [])

    def test_no_new_file_fails(self):
        self.assertTrue(check_added.check(self.repo()))

    def test_editing_an_existing_skill_fails_even_with_a_new_file(self):
        r = self.repo()
        (r / "tools" / "lint" / "rules" / "new_rule.py").write_text("x")
        (r / "skills" / "ui" / "old" / "SKILL.md").write_text("edited")
        v = check_added.check(r)
        self.assertTrue(any("existing" in m and "old" in m for m in v), v)


class LintHitsTests(unittest.TestCase):
    BAD = "class A { void U(){ var g = new GameObject(\"M\"); g.AddComponent<M>(); } }\n"

    def run_lint(self, f, hits, cap="524288"):
        env = dict(os.environ, STUDIO_LINT_HITS=hits, STUDIO_LINT_HITS_MAX=cap)
        return subprocess.run([sys.executable, os.path.join(LINT, "run_lint.py"), f], capture_output=True, text=True, env=env)

    def test_hits_are_logged_counted_and_capped(self):
        d = tempfile.mkdtemp()
        f = os.path.join(d, "M.cs")
        open(f, "w").write(self.BAD)
        hits = os.path.join(d, "hits.jsonl")
        self.assertEqual(self.run_lint(f, hits).returncode, 2)
        self.run_lint(f, hits)
        c = miner.mine_lint_hits([hits])
        self.assertEqual(c["no-runtime-manager-gameobject"], 2)
        size = os.path.getsize(hits)
        self.run_lint(f, hits, cap=str(size))  # at the cap: no further writes
        self.assertEqual(os.path.getsize(hits), size)


if __name__ == "__main__":
    unittest.main()
