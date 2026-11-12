import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skillkit"))
import skill_loop  # noqa: E402

GOOD = '---\nname: demo\ndescription: "Demo skill used for tests. Use when testing the loop helper."\ntriggers: demo, loop\n---\n\n# Demo\nbody line\n'
BAD = GOOD.replace("name: demo", "name: wrong")


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.skills = os.path.join(self.root, "skills")
        os.makedirs(os.path.join(self.skills, "demo"))
        self.md = os.path.join(self.skills, "demo", "SKILL.md")
        self.write(GOOD)

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, text):
        with open(self.md, "w", encoding="utf-8") as f:
            f.write(text)

    def test_clean_scores_100_and_spec_failure_costs_10(self):
        self.assertEqual(skill_loop.score(self.skills, "demo")["score"], 100)
        os.makedirs(os.path.join(self.root, "tools", "evals", "skill-specs"))
        with open(os.path.join(self.root, "tools", "evals", "skill-specs", "demo.json"), "w") as f:
            json.dump({"must_contain": ["absent phrase"], "triggers_any": ["loop"]}, f)
        r = skill_loop.score(self.skills, "demo")
        self.assertEqual(r["score"], 90)
        self.assertEqual(len(r["spec"]), 1)

    def test_keep_revert_cycle(self):
        skill_loop.snapshot(self.skills, "demo")
        self.write(GOOD + "more text\n")
        self.assertEqual(skill_loop.decide(self.skills, "demo")["verdict"], "KEEP")
        self.write(BAD)
        self.assertEqual(skill_loop.decide(self.skills, "demo")["verdict"], "REVERT")
        self.assertEqual(skill_loop.decide(self.skills, "demo", apply=True)["verdict"], "REVERTED")
        with open(self.md, encoding="utf-8") as f:
            self.assertEqual(f.read(), GOOD)

    def test_no_baseline(self):
        self.assertEqual(skill_loop.decide(self.skills, "demo")["verdict"], "NO-BASELINE")


if __name__ == "__main__":
    unittest.main()
