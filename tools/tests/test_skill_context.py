import json
import os
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
import sys
sys.path.insert(0, os.path.join(ROOT, "skills", "game-orchestrator", "scripts"))
import skill_context  # noqa: E402


class SkillContextTests(unittest.TestCase):
    def test_selects_only_requested_and_always_on(self):
        result = skill_context.select(["clone-pipeline", "unity-mcp-workflow"], ["game-orchestrator"], ["clone-pipeline", "game-orchestrator", "unity-mcp-workflow", "unused"])
        self.assertEqual(result["active"], ["clone-pipeline", "game-orchestrator", "unity-mcp-workflow"])
        self.assertEqual(result["unload"], ["unused"])

    def test_rejects_missing_skill(self):
        with self.assertRaises(ValueError):
            skill_context.select(["missing-skill"], [], available=["game-orchestrator"])

    def test_writes_compact_manifest_without_skill_bodies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "active-skills.json")
            data = skill_context.write_manifest(path, ["unity-mcp-workflow"], ["game-orchestrator"], "phase-1")
            self.assertEqual(data["phase"], "phase-1")
            self.assertNotIn("body", data)
            with open(path, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream), data)


if __name__ == "__main__":
    unittest.main()
