import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "auto-balance-game", "scripts"))

import auto_balance_game as balance  # noqa: E402
import econ_sim  # noqa: E402


class EconSimulationTests(unittest.TestCase):
    def plan(self):
        return balance.build_plan(0.5, 1, ["start=10m", "finish=20m"], [], [])

    def test_simulate_reports_target_and_milestones(self):
        result = econ_sim.simulate(self.plan())
        self.assertTrue(result["simulated"])
        self.assertEqual(result["milestones"], 2)
        self.assertAlmostEqual(result["total_minutes"], 30.0, places=3)
        self.assertAlmostEqual(result["target_minutes"], 30.0, places=3)
        self.assertTrue(result["within_tolerance"])

    def test_tune_converges_with_bounded_iterations(self):
        plan = balance.build_plan(1, 1, ["start=10m", "finish=20m", "end=30m"], [], [])
        result = econ_sim.tune(plan, initial={"income_factor": 2.0}, tolerance=0.01, max_iterations=8)
        self.assertEqual(result["status"], "converged")
        self.assertLessEqual(result["iterations"], 8)
        self.assertTrue(result["metrics"]["within_tolerance"])

    def test_open_world_without_milestones_is_explicitly_inconclusive(self):
        result = econ_sim.tune(balance.build_plan(1, 1), max_iterations=2)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIn("milestones", result["reason"])

    def test_cli_writes_machine_readable_report(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = os.path.join(directory, "plan.json")
            out_path = os.path.join(directory, "sim.json")
            with open(plan_path, "w", encoding="utf-8") as handle:
                json.dump(self.plan(), handle)
            self.assertEqual(econ_sim.main([plan_path, "--mode", "simulate", "--out", out_path]), 0)
            with open(out_path, encoding="utf-8") as handle:
                self.assertTrue(json.load(handle)["simulated"])


if __name__ == "__main__":
    unittest.main()
