import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "skills", "ui-pattern-library")
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-builder", "scripts"))

import ui_spec_tool as ust  # noqa: E402

PATTERNS = os.path.join(LIB, "patterns")
NAMES = sorted(d for d in os.listdir(PATTERNS) if os.path.isdir(os.path.join(PATTERNS, d)))
REQUIRED = {"settings", "daily-login", "gacha-box", "jackpot-slot", "rating", "revive-result", "mode-select-card",
            "side-tab-shop", "inventory", "iap-carousel", "vip-pass", "world-list", "rebirth", "spin-wheel", "quests", "skin-shop"}


class PatternLibraryTests(unittest.TestCase):
    def test_all_planned_patterns_exist(self):
        self.assertTrue(REQUIRED <= set(NAMES), REQUIRED - set(NAMES))

    def test_index_lists_every_pattern(self):
        with open(os.path.join(PATTERNS, "index.md"), encoding="utf-8") as f:
            idx = f.read()
        for n in NAMES:
            self.assertIn("`%s`" % n, idx, n)

    def test_each_pattern_has_markdown_within_budget(self):
        for n in NAMES:
            with open(os.path.join(PATTERNS, n, "pattern.md"), encoding="utf-8") as f:
                lines = f.read().splitlines()
            self.assertLessEqual(len(lines), 80, n)
            self.assertTrue(any(l.startswith("## Checks") for l in lines), n + " has no Checks section")

    def test_specs_lint_clean(self):
        for n in NAMES:
            path = os.path.join(PATTERNS, n, "spec.yaml")
            if not os.path.isfile(path):
                continue                                   # skin-shop predates the spec format; it has mockups instead
            with open(path, encoding="utf-8") as f:
                spec = ust.loads(f.read())
            self.assertEqual([x for x in ust.lint(spec)], [], n)

    def test_new_patterns_have_wireframes_and_specs(self):
        for n in REQUIRED - {"skin-shop"}:
            self.assertTrue(os.path.isfile(os.path.join(PATTERNS, n, "spec.yaml")), n)
            self.assertTrue(os.path.getsize(os.path.join(PATTERNS, n, "mockups", "wireframe.png")) > 500, n)

    def test_spec_numbers_start_at_one_and_are_dense(self):
        for n in REQUIRED - {"skin-shop"}:
            with open(os.path.join(PATTERNS, n, "spec.yaml"), encoding="utf-8") as f:
                spec = ust.loads(f.read())
            nums = sorted(e["n"] for e in spec["elements"])
            self.assertEqual(nums, list(range(1, len(nums) + 1)), n)

    def test_builds_for_a_second_game_canvas(self):
        for n in REQUIRED - {"skin-shop"}:
            with open(os.path.join(PATTERNS, n, "spec.yaml"), encoding="utf-8") as f:
                spec = ust.loads(f.read())
            out = ust.build_json(spec, (2400, 1080))
            self.assertEqual(len(out["elements"]), len(spec["elements"]), n)


if __name__ == "__main__":
    unittest.main()
