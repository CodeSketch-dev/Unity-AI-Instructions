import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(LINT, "..", ".."))
sys.path.insert(0, LINT)

import engine  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "tools", "skillkit"))
import skill_paths  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
CS = os.path.join("Assets", "_Game", "Scripts", "Logic", "Bootstrap.cs")


class RuleIntegrityTests(unittest.TestCase):
    def test_every_rule_points_to_an_existing_skill(self):
        for r in engine.load_rules():
            self.assertIsNotNone(skill_paths.skill_dir(os.path.join(REPO, "skills"), r.skill), "%s -> missing skill %s" % (r.id, r.skill))

    def test_manager_rule_flags_bad_fixture_at_new_gameobject_line(self):
        v = engine.lint_text(CS, open(os.path.join(FIX, "bad_manager.cs")).read())
        self.assertEqual([(x.rule_id, x.line) for x in v], [("no-runtime-manager-gameobject", 9)])

    def test_manager_rule_passes_good_fixture(self):
        self.assertEqual(engine.lint_text(CS, open(os.path.join(FIX, "good_manager.cs")).read()), [])

    def test_manager_rule_opt_out_for_legit_pooled_spawn(self):
        src = open(os.path.join(FIX, "bad_manager.cs")).read().replace('new GameObject("AudioManager");', 'new GameObject("Tmp"); // lint-ok:no-runtime-manager-gameobject editor-free debug marker')
        self.assertEqual(engine.lint_text(CS, src), [])


if __name__ == "__main__":
    unittest.main()
