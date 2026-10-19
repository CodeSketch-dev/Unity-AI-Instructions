import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "..", "skills", "game-orchestrator", "scripts")
SKILLS = os.path.join(HERE, "..", "..", "skills")
sys.path.insert(0, SCRIPTS)

import gdd_lint  # noqa: E402
import gen_task_graph  # noqa: E402


EXAMPLE = os.path.join(SKILLS, "gdd-schema", "assets", "example-sky-climb", "gdd")


class BalanceIntegrationTests(unittest.TestCase):
    def test_balance_task_is_before_core_loop_gate(self):
        graph = gen_task_graph.generate(gdd_lint.load_gdd(EXAMPLE), 16)
        balance = next(task for task in graph["tasks"] if task["key"] == "balance")
        gate = next(task for task in graph["tasks"] if task["key"] == "gate2")
        self.assertEqual(balance["phase"], 2)
        self.assertIn("auto-balance-game", balance["skills"])
        self.assertIn("auto-balance-loop", balance["skills"])
        self.assertIn(balance["id"], gate["depends_on"])

    def test_balance_task_has_machine_evidence_target(self):
        graph = gen_task_graph.generate(gdd_lint.load_gdd(EXAMPLE), 16)
        balance = next(task for task in graph["tasks"] if task["key"] == "balance")
        self.assertIn("file:gdd/_generated/balance-plan.json", balance["claims"])
        self.assertTrue(any("simulation" in item for item in balance["verify"]))


if __name__ == "__main__":
    unittest.main()
