import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, LINT)

import engine  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
CS = os.path.join("Assets", "_Game", "Scripts", "Logic", "Enemy", "Enemy_Chase.cs")
RULE_ID = "no-find-in-update"


def read(name):
    with open(os.path.join(FIX, name)) as f:
        return f.read()


class NoFindInUpdateTests(unittest.TestCase):
    def test_bad_fixture_flagged_at_find_line(self):
        v = engine.lint_text(CS, read("bad_find_in_update.cs"))
        self.assertEqual([(x.rule_id, x.line) for x in v], [(RULE_ID, 9)])

    def test_good_fixture_is_clean(self):
        self.assertEqual(engine.lint_text(CS, read("good_find_in_update.cs")), [])

    def test_find_outside_per_frame_file_is_not_flagged(self):
        src = "using UnityEngine;\nclass Boot : MonoBehaviour {\n void Awake() { var p = FindObjectOfType<Player>(); }\n}\n"
        self.assertEqual(engine.lint_text(CS, src), [])

    def test_new_unity_find_names_are_flagged(self):
        src = "class A : MonoBehaviour {\n void Update() {\n var p = FindFirstObjectByType<Player>();\n var g = GameObject.Find(\"Hud\");\n }\n}\n"
        v = engine.lint_text(CS, src)
        self.assertEqual([(x.rule_id, x.line) for x in v], [(RULE_ID, 3), (RULE_ID, 4)])

    def test_opt_out_comment_suppresses(self):
        src = read("bad_find_in_update.cs").replace(
            "Object.FindObjectOfType<Player>();",
            "Object.FindObjectOfType<Player>(); // lint-ok:no-find-in-update one-time debug probe")
        self.assertEqual(engine.lint_text(CS, src), [])


if __name__ == "__main__":
    unittest.main()
