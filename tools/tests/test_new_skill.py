import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skillkit"))
sys.path.insert(0, os.path.join(HERE, "..", "publish"))

import new_skill as ns  # noqa: E402
import skill_lint  # noqa: E402
import repo_layout_lint as rl  # noqa: E402

DESC = "Use when a scaffolded demo skill is needed to prove the generator output passes the skill linter."


class NewSkillTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        (self.repo / "skills").mkdir()
        (self.repo / "AGENTS.md").write_text("x")

    def test_creates_skill_in_group_and_passes_skill_lint_and_layout_lint(self):
        p = ns.create_skill(self.repo / "skills", "demo-skill", "ui", DESC, "demo, scaffold, tao skill")
        self.assertEqual(Path(p), self.repo / "skills" / "ui" / "demo-skill" / "SKILL.md")
        errors = [f for f in skill_lint.lint_dir(str(self.repo / "skills")) if f.severity == "error"]
        self.assertEqual(errors, [])
        self.assertEqual(rl.check_layout(self.repo), [])

    def test_rejects_unknown_group_bad_name_and_duplicates(self):
        with self.assertRaises(ValueError):
            ns.create_skill(self.repo / "skills", "demo-skill", "nope", DESC, "")
        with self.assertRaises(ValueError):
            ns.create_skill(self.repo / "skills", "Bad_Name", "ui", DESC, "")
        ns.create_skill(self.repo / "skills", "demo-skill", "ui", DESC, "")
        with self.assertRaises(ValueError):
            ns.create_skill(self.repo / "skills", "demo-skill", "gameplay", DESC, "")

    def test_rejects_description_that_does_not_start_with_use_when(self):
        with self.assertRaises(ValueError):
            ns.create_skill(self.repo / "skills", "demo-skill", "ui", "A skill about things that is long enough to pass the length check easily okay.", "")


if __name__ == "__main__":
    unittest.main()
