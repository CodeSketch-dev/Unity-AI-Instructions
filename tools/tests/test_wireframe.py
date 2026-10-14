import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-pattern-library", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-visual-qa", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-builder", "scripts"))

import wireframe as wf  # noqa: E402
import image_diff as idf  # noqa: E402
import ui_spec_tool as ust  # noqa: E402

DATA = {"canvas": [1920, 1080], "id": "T", "elements": [
    {"n": 1, "name": "Board", "container": True, "state": None, "rect": [560, 240, 1360, 840]},
    {"n": 2, "name": "Btn", "container": False, "state": None, "rect": [860, 300, 1060, 400]},
]}


class WireframeTests(unittest.TestCase):
    def test_render_size_and_content(self):
        img = wf.render(DATA, scale=0.5)
        self.assertEqual((len(img[0]), len(img)), (960, 540))
        # leaf interior is not the background colour; outside is
        self.assertNotEqual(img[540 - 175][480 - 40], wf.BG)
        self.assertEqual(img[5][5], wf.BG)

    def test_digit_glyphs(self):
        self.assertEqual(len(wf.GLYPHS["8"]), 5)
        self.assertTrue(all(len(r) == 3 for r in wf.GLYPHS["0"]))

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            j = os.path.join(d, "r.json")
            out = os.path.join(d, "w.png")
            json.dump(DATA, open(j, "w"))
            self.assertEqual(wf.main([j, out]), 0)
            w, h, px = idf.read_png(out)
            self.assertEqual((w, h), (960, 540))

    def test_rects_command(self):
        spec = {"id": "T", "type": "ui_screen", "reference_canvas": {"w": 1920, "h": 1080},
                "elements": [{"n": 1, "name": "A", "anchor": "center", "pos": [0, 0], "size": [200, 100]}]}
        with tempfile.TemporaryDirectory() as d:
            sp = os.path.join(d, "s.json")
            out = os.path.join(d, "r.json")
            json.dump(spec, open(sp, "w"))
            self.assertEqual(ust.main(["rects", sp, "--out", out]), 0)
            self.assertEqual(json.load(open(out))["elements"][0]["rect"], [860, 490, 1060, 590])


if __name__ == "__main__":
    unittest.main()
