import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills", "roblox-shader-kit")
sys.path.insert(0, os.path.join(SK, "scripts"))

import validate_contract as contract  # noqa: E402


def report(**overrides):
    value = {
        "color_space": "Linear",
        "colors_linear": True,
        "vertex_count": 4,
        "channels": {"vertex_color": 4, "uv0": 4, "uv1": 4, "uv2": 4},
        "surfaces": [{"flags": 3, "slot": 0, "checker_tiling": 4, "emission_strength": 0}],
        "materials": {"count": 1, "shared": True, "static_object_variants": 0},
        "families": [{"name": "map", "count": 1, "justification": ""}],
    }
    value.update(overrides)
    return value


def codes(findings):
    return {finding.code for finding in findings}


class ContractTests(unittest.TestCase):
    def test_valid_shared_material_contract(self):
        self.assertEqual(codes(contract.validate(report())), set())

    def test_channel_length_mismatch_fails(self):
        value = report()
        value["channels"]["uv1"] = 3
        self.assertIn("channel-length", codes(contract.validate(value)))

    def test_illegal_surface_flags_and_slot_fail(self):
        value = report(surfaces=[{"flags": 2, "slot": 5, "checker_tiling": 0, "emission_strength": 0}])
        found = codes(contract.validate(value))
        self.assertIn("surface-flags", found)
        self.assertIn("surface-slot", found)

    def test_gamma_colors_in_linear_project_fail(self):
        self.assertIn("color-space", codes(contract.validate(report(colors_linear=False))))

    def test_static_per_object_material_variants_fail(self):
        value = report(materials={"count": 4, "shared": False, "static_object_variants": 3})
        self.assertIn("static-material-variants", codes(contract.validate(value)))

    def test_justified_material_families_warn_but_do_not_fail(self):
        value = report(
            materials={"count": 2, "shared": False, "static_object_variants": 0},
            families=[
                {"name": "map", "count": 1, "justification": "opaque map"},
                {"name": "water", "count": 1, "justification": "transparent movement"},
            ],
        )
        findings = contract.validate(value)
        self.assertIn("material-families", codes(findings))
        self.assertEqual([f for f in findings if f.level == "ERROR"], [])


if __name__ == "__main__":
    unittest.main()
