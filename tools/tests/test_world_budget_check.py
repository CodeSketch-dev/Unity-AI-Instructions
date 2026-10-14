import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills", "mobile-urp-lighting-baseline")
sys.path.insert(0, os.path.join(SK, "scripts"))

import world_budget_check as wb  # noqa: E402

BUDGETS = os.path.join(SK, "assets", "world-budgets.json")


class BudgetTests(unittest.TestCase):
    def test_within_budget_passes(self):
        r = wb.check({"batches": 50, "verts": 70000, "materials": 1}, "Low", wb.load_budgets(BUDGETS))
        self.assertEqual([x for x in r if x.status == "FAIL"], [])

    def test_over_budget_fails(self):
        r = wb.check({"batches": 90, "materials": 3}, "Low", wb.load_budgets(BUDGETS))
        failed = sorted(x.metric for x in r if x.status == "FAIL")
        self.assertEqual(failed, ["batches", "materials"])

    def test_unknown_metric_ignored_and_missing_reported(self):
        r = wb.check({"batches": 10, "banana": 5}, "Mid", wb.load_budgets(BUDGETS))
        self.assertEqual([x.metric for x in r], ["batches"])

    def test_unknown_tier_raises(self):
        with self.assertRaises(KeyError):
            wb.check({"batches": 1}, "Ultra", wb.load_budgets(BUDGETS))

    def test_main_exit_codes_and_device_label(self):
        with tempfile.TemporaryDirectory() as d:
            ok = os.path.join(d, "ok.json")
            bad = os.path.join(d, "bad.json")
            json.dump({"batches": 10, "measured_on": "editor"}, open(ok, "w"))
            json.dump({"batches": 999, "measured_on": "device"}, open(bad, "w"))
            self.assertEqual(wb.main(["Low", ok]), 0)
            self.assertEqual(wb.main(["Low", bad]), 1)

    def test_missing_measured_on_is_flagged(self):
        r = wb.check({"batches": 10}, "Low", wb.load_budgets(BUDGETS))
        self.assertTrue(wb.measurement_note({"batches": 10}).startswith("UNLABELLED"))
        self.assertIn("editor", wb.measurement_note({"measured_on": "editor"}))


if __name__ == "__main__":
    unittest.main()
