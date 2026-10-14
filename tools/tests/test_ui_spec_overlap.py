import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-builder", "scripts"))

import ui_spec_tool as ust  # noqa: E402


def spec(*els, w=1920, h=1080):
    return {"id": "T", "type": "ui_screen", "reference_canvas": {"w": w, "h": h}, "elements": list(els)}


def el(n, name, anchor, pos=None, size=None, **kw):
    d = {"n": n, "name": name, "anchor": anchor}
    if pos is not None:
        d["pos"] = pos
    if size is not None:
        d["size"] = size
    d.update(kw)
    return d


def codes(s):
    return sorted(f.code for f in ust.lint(s))


class RectTests(unittest.TestCase):
    def test_center_and_corner_anchors(self):
        r = ust.element_rects(spec(el(1, "A", "center", [0, 0], [200, 100]), el(2, "B", "top-left", [100, -50], [200, 100])))
        self.assertEqual(r["A"], (860, 490, 1060, 590))
        self.assertEqual(r["B"], (0, 980, 200, 1080))

    def test_stretch_rect(self):
        r = ust.element_rects(spec(el(1, "S", "stretch-top", rect={"top": 0, "left": 0, "right": 0, "bottom": 905})))
        self.assertEqual(r["S"], (0, 905, 1920, 1080))


class OverlapTests(unittest.TestCase):
    def test_overlap_detected(self):
        s = spec(el(1, "A", "center", [0, 0], [200, 100]), el(2, "B", "center", [100, 0], [200, 100]))
        self.assertIn("overlap", codes(s))

    def test_touching_or_gap_is_fine(self):
        s = spec(el(1, "A", "center", [0, 0], [200, 100]), el(2, "B", "center", [204, 0], [200, 100]))
        self.assertNotIn("overlap", codes(s))

    def test_container_and_state_elements_skipped(self):
        s = spec(el(1, "Board", "center", [0, 0], [800, 600], container=True), el(2, "A", "center", [0, 0], [200, 100]),
                 el(3, "Alt", "center", [0, 0], [200, 100], state="language"))
        self.assertNotIn("overlap", codes(s))

    def test_offscreen_element_flagged(self):
        s = spec(el(1, "A", "center", [900, 0], [400, 100]))
        self.assertIn("offscreen", codes(s))

    def test_offscreen_container_allowed(self):
        s = spec(el(1, "Art", "center", [900, 0], [400, 100], container=True))
        self.assertNotIn("offscreen", codes(s))


if __name__ == "__main__":
    unittest.main()
