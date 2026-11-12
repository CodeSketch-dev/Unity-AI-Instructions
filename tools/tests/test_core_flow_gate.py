import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/studio-process/studio-boss-quality-bar/SKILL.md"
AGENTS = ROOT / "AGENTS.md"
RULES = ROOT / "data/studio_rules.json"


class CoreFlowFoundationPromotionTest(unittest.TestCase):
    def test_boss_skill_requires_natural_critical_journey_before_expansion(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Core-flow first", text)
        self.assertRegex(text, r"(?is)natural.{0,80}(?:player|critical).{0,80}journey")
        self.assertRegex(text, r"(?is)seeded.{0,50}(?:wallet|currency).{0,100}(?:not|cannot|cannot replace)")
        self.assertIn("optional SDK, monetization, or polish", text)
        self.assertIn("blocked core journey", text)
        self.assertRegex(text, r"(?is)save.{0,50}(?:reload|resume)")

    def test_always_on_rule_and_prompt_injection_route_blocked_core_flow(self):
        agents = AGENTS.read_text(encoding="utf-8")
        self.assertIn("Core-flow first", agents)
        rules = json.loads(RULES.read_text(encoding="utf-8"))["rules"]
        rule = next(item for item in rules if item.get("id") == "core_flow_first")
        self.assertEqual(rule["event"], "UserPromptSubmit")
        self.assertIn("core.?flow", rule["match"])
        self.assertIn("natural", rule["inject"].lower())
        self.assertIn("seeded", rule["inject"].lower())
        self.assertIn("optional SDK", rule["inject"])
        self.assertIn("core path is blocked", rule["inject"])
        prompts = [
            "Only one or two blocks spawn, then stop; should I continue SDK work?",
            "The player journey is blocked; should I polish monetization?",
            "Basic gameplay is blocked; should we add optional systems?",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertIsNotNone(re.search(rule["match"], prompt.lower()))


if __name__ == "__main__":
    unittest.main()

