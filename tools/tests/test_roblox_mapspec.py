import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "skills" / "roblox-shader-kit" / "assets" / "map-spec.schema.json"
REFERENCE = ROOT / "skills" / "roblox-shader-kit" / "references" / "map-spec.md"
sys.path.insert(0, os.fspath(ROOT / "skills" / "roblox-shader-kit" / "scripts"))
import validate_contract as contract  # noqa: E402


class RobloxMapSpecTests(unittest.TestCase):
    def test_schema_and_reference_are_present_and_compact(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema"]["const"], 1)
        self.assertEqual(schema["required"], ["schema", "source", "materials", "surfaces", "parts", "chunks", "camera", "evidence"])
        self.assertLess(len(REFERENCE.read_text(encoding="utf-8")), 12000)

    def test_mapspec_rules_feed_shared_material_contract(self):
        report = {
            "vertex_count": 4,
            "channels": {"vertex_color": 4, "uv0": 4, "uv1": 4, "uv2": 4},
            "color_space": "Linear",
            "colors_linear": True,
            "surfaces": [{"flags": 3, "slot": 0}],
            "materials": {"count": 1, "shared": True, "static_object_variants": 0},
            "families": [{"name": "map", "count": 1}],
        }
        self.assertEqual(contract.validate(report), [])


if __name__ == "__main__":
    unittest.main()
