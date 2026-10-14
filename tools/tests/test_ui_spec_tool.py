import json
import math
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-builder", "scripts"))

import ui_spec_tool as ust  # noqa: E402

SPEC = """\
id: UI-10-skin-shop
type: ui_screen
kind: popup_fullscreen
fidelity: exact
reference_canvas: {w: 1080, h: 1920, match: 0.5}
# a comment
elements:
  - {n: 1, name: BtnBack, anchor: top-left, pos: [92, -87], size: [179, 161], behaviour: close}
  - {n: 2, name: Tabs_Main, anchor: top-center, pos: [0, -200], size: [509, 92], children: [BtnShop, BtnCustom]}
  - n: 3
    name: ItemList
    anchor: stretch-bottom
    rect: {top: 958, bottom: 223}
    kind: scroll_grid
  - {n: 5, name: BtnShop, anchor: top-left, pos: [100, -200], size: [200, 80]}
  - {n: 6, name: BtnCustom, anchor: top-right, pos: [-100, -200], size: [200, 80]}
  - {n: 4, name: BtnBuy, anchor: bottom-center, pos: [0, 110], size: [811, 141], text: {key: ui.buy, auto_size: true}}
states: [default, item_owned]
"""


class ParseTests(unittest.TestCase):
    def test_parse_yaml_subset(self):
        d = ust.loads(SPEC)
        self.assertEqual(d["id"], "UI-10-skin-shop")
        self.assertEqual(d["reference_canvas"], {"w": 1080, "h": 1920, "match": 0.5})
        self.assertEqual(len(d["elements"]), 6)
        self.assertEqual(d["elements"][0]["pos"], [92, -87])
        self.assertEqual(d["elements"][1]["children"], ["BtnShop", "BtnCustom"])
        self.assertEqual(d["elements"][2]["rect"], {"top": 958, "bottom": 223})
        self.assertEqual(d["elements"][5]["text"], {"key": "ui.buy", "auto_size": True})
        self.assertEqual(d["states"], ["default", "item_owned"])

    def test_scalars(self):
        d = ust.loads("a: null\nb: true\nc: 1.5\nd: 'x y'\ne: ~\n")
        self.assertEqual(d, {"a": None, "b": True, "c": 1.5, "d": "x y", "e": None})

    def test_json_accepted(self):
        self.assertEqual(ust.loads('{"a": [1, 2]}'), {"a": [1, 2]})


class LintTests(unittest.TestCase):
    def codes(self, spec):
        return sorted(f.code for f in ust.lint(spec))

    def test_clean(self):
        self.assertEqual(self.codes(ust.loads(SPEC)), [])

    def test_duplicate_name_and_number(self):
        s = ust.loads(SPEC)
        s["elements"][1]["name"] = "BtnBack"
        s["elements"][2]["n"] = 1
        c = self.codes(s)
        self.assertIn("duplicate-name", c)
        self.assertIn("duplicate-number", c)

    def test_unknown_anchor_and_missing_size(self):
        s = ust.loads(SPEC)
        s["elements"][0]["anchor"] = "middle-ish"
        del s["elements"][5]["size"]
        c = self.codes(s)
        self.assertIn("bad-anchor", c)
        self.assertIn("missing-size", c)

    def test_stretch_needs_rect(self):
        s = ust.loads(SPEC)
        del s["elements"][2]["rect"]
        self.assertIn("missing-rect", self.codes(s))

    def test_missing_top_level(self):
        self.assertIn("missing-key", self.codes({"elements": []}))

    def test_text_needs_localization_key(self):
        s = ust.loads(SPEC)
        s["elements"][5]["text"] = {"auto_size": True}
        self.assertIn("text-no-key", self.codes(s))

    def test_bad_reference_canvas(self):
        s = ust.loads(SPEC)
        s["reference_canvas"] = {"w": 0, "h": 1920}
        self.assertIn("bad-canvas", self.codes(s))

    def test_unknown_child(self):
        s = ust.loads(SPEC)
        s["elements"][1]["children"] = ["Nope"]
        self.assertIn("unknown-child", self.codes(s))


class AnchorTests(unittest.TestCase):
    def test_scale_factor(self):
        # same aspect: pure ratio
        self.assertAlmostEqual(ust.scale_factor((1080, 1920), (1920, 1080), 0.5),
                               math.sqrt(1920 / 1080 * 1080 / 1920), places=6)
        self.assertAlmostEqual(ust.scale_factor((1920, 1080), (1920, 1080), 0.5), 1.0)
        self.assertAlmostEqual(ust.scale_factor((960, 540), (1920, 1080), 0.0), 2.0)
        self.assertAlmostEqual(ust.scale_factor((960, 540), (1920, 1080), 1.0), 2.0)

    def test_top_left_fixed(self):
        r = ust.to_rect({"anchor": "top-left", "pos": [92, -87], "size": [179, 161]}, 1.0)
        self.assertEqual(r, {"anchorMin": [0, 1], "anchorMax": [0, 1], "pivot": [0.5, 0.5],
                             "anchoredPosition": [92, -87], "sizeDelta": [179, 161]})

    def test_bottom_center_and_scale(self):
        r = ust.to_rect({"anchor": "bottom-center", "pos": [0, 110], "size": [811, 141]}, 2.0)
        self.assertEqual(r["anchorMin"], [0.5, 0])
        self.assertEqual(r["anchoredPosition"], [0, 220])
        self.assertEqual(r["sizeDelta"], [1622, 282])

    def test_stretch_bottom_rect(self):
        r = ust.to_rect({"anchor": "stretch-bottom", "rect": {"top": 958, "bottom": 223}}, 1.0)
        self.assertEqual(r["anchorMin"], [0, 0])
        self.assertEqual(r["anchorMax"], [1, 1])
        self.assertEqual(r["offsetMin"], [0, 223])
        self.assertEqual(r["offsetMax"], [0, -958])

    def test_build_json_contains_scaled_rects(self):
        out = ust.build_json(ust.loads(SPEC), (1920, 1080))
        self.assertEqual(out["id"], "UI-10-skin-shop")
        self.assertEqual([e["name"] for e in out["elements"]], ["BtnBack", "Tabs_Main", "ItemList", "BtnShop", "BtnCustom", "BtnBuy"])
        self.assertIn("rect", out["elements"][0])
        self.assertAlmostEqual(out["scale"], 1.0, places=6)


class CliTests(unittest.TestCase):
    def test_lint_and_build_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            ok = os.path.join(d, "ok.yaml")
            bad = os.path.join(d, "bad.yaml")
            out = os.path.join(d, "out.json")
            open(ok, "w", encoding="utf-8").write(SPEC)
            open(bad, "w", encoding="utf-8").write(SPEC.replace("top-left", "nowhere"))
            self.assertEqual(ust.main(["lint", ok]), 0)
            self.assertEqual(ust.main(["lint", bad]), 1)
            self.assertEqual(ust.main(["build", ok, "--canvas", "1920x1080", "--out", out]), 0)
            data = json.load(open(out, encoding="utf-8"))
            self.assertEqual(len(data["elements"]), 6)
            self.assertEqual(ust.main(["build", bad, "--canvas", "1920x1080", "--out", out]), 1)


if __name__ == "__main__":
    unittest.main()
