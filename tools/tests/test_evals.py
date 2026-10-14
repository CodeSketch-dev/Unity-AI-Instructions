import os
import re
import unittest
from pathlib import Path

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
SKILLS = set(os.listdir(os.path.join(ROOT, "skills")))


class EvalSuiteTests(unittest.TestCase):
    def cases(self):
        base = os.path.join(ROOT, "evals")
        return [d for d in sorted(os.listdir(base))
                if os.path.isfile(os.path.join(base, d, "prompt.md"))]

    def test_every_case_has_prompt_and_grader(self):
        self.assertGreaterEqual(len(self.cases()), 10)
        for c in self.cases():
            self.assertTrue(os.path.isfile(os.path.join(ROOT, "evals", c, "prompt.md")), c)
            gdir = os.path.join(ROOT, "evals", c, "graders")
            self.assertTrue([f for f in os.listdir(gdir) if f.endswith(".md")], c)

    def test_generated_results_directory_is_not_an_eval_case(self):
        self.assertNotIn("results", self.cases())

    def test_graders_name_an_existing_skill(self):
        for c in self.cases():
            gdir = os.path.join(ROOT, "evals", c, "graders")
            for f in os.listdir(gdir):
                text = Path(gdir, f).read_text(encoding="utf-8")
                names = re.findall(r"`([a-z][a-z0-9-]+)` skill", text)
                self.assertTrue(names, c)
                for n in names:
                    self.assertIn(n, SKILLS, "%s -> %s" % (c, n))


if __name__ == "__main__":
    unittest.main()
