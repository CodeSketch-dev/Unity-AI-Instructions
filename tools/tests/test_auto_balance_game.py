import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "auto-balance-game", "scripts"))

import auto_balance_game as ab  # noqa: E402


class AutoBalanceTests(unittest.TestCase):
    def test_optional_topology_timeline_and_total_target(self):
        result = ab.build_plan(10, 1, ["quest.main_01=2m", "map.center=15m"], ["currency.coins.sinks=upgrade,shop", "player_sessions_per_day=1"], ["combat.enemy_hp_factor=1.2"])
        self.assertEqual(result["target"]["total_play_minutes"], 600)
        self.assertEqual([b["path"] for b in result["milestones"][:2]], ["quest.main_01", "map.center"])
        self.assertEqual([b["target_minutes"] for b in result["milestones"][:2]], [2, 15])
        self.assertEqual(result["constraints"]["currency.coins.sinks"], ["upgrade", "shop"])
        self.assertEqual(result["overrides"]["combat.enemy_hp_factor"], 1.2)
        self.assertIn("coins", result["stats"]["currencies"])
        self.assertIn("enemy_hp", result["stats"]["combat"])
        self.assertEqual(len(result["generated_values"]), len(result["milestones"]))
        self.assertGreater(result["generated_values"][0]["currency"]["unlock_cost"], 0)
        self.assertGreater(result["generated_values"][-1]["combat"]["enemy_hp"], result["generated_values"][0]["combat"]["enemy_hp"])

    def test_no_topology_is_valid_for_open_world(self):
        result = ab.build_plan(2, 1, [], [], [])
        self.assertEqual(result["milestones"], [])
        self.assertEqual(result["target"]["total_play_minutes"], 120)

    def test_discovers_tunable_fields_from_gdd(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "systems.md"), "w", encoding="utf-8") as f:
                f.write("speed: ?\nshop_price: ?\nquest_duration: ?\nart_style: roblox\n")
            result = ab.build_plan(1, 1, [], [], [], d)
            self.assertIn("speed", result["discovered_stats"])
            self.assertIn("shop_price", result["discovered_stats"])
            self.assertNotIn("art_style", result["discovered_stats"])

    def test_rejects_invalid_or_over_target_inputs(self):
        with self.assertRaises(ValueError):
            ab.build_plan(0, 1, [], [], [])
        with self.assertRaises(ValueError):
            ab.build_plan(1, 1, ["1=90m", "2=90m"], [], [])

    def test_cli_writes_machine_readable_plan(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "balance.json")
            self.assertEqual(ab.main(["--full-days", "3", "--hours-per-day", "2", "--milestone", "boss.final=4m", "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["target"]["full_days"], 3)


if __name__ == "__main__":
    unittest.main()
