import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-validator", "scripts"))
sys.path.insert(0, HERE)

import ui_validator as uv  # noqa: E402
from test_ui_validator_rules2 import make, text, image, BUTTON  # noqa: E402


def nodes(items, inactive=()):
    body = make(items)
    for name in inactive:
        body = body.replace("m_Name: %s\n" % name, "m_Name: %s\n  m_IsActive: 0\n" % name)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.prefab")
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        return uv.nodes_from_prefab(p)


def rules(findings, level=None):
    return sorted({f.rule for f in findings if level is None or f.level == level})


class CalibrationTests(unittest.TestCase):
    def test_degenerate_rect_skipped(self):
        # stretched parent with huge negative offsets gives a negative width: no SAFE/TOUCH findings
        n = nodes([dict(name="Weird", rect=dict(amin=(0, 0), amax=(1, 1), size=(-4000, -4000)), comps=[BUTTON])])
        self.assertEqual(rules(uv.validate(n)), [])

    def test_inactive_panel_skips_raycast_and_safe(self):
        items = [dict(name="Demo", rect=dict(amin=(0, 0), amax=(1, 1), size=(0, 0)), comps=[image(raycast=1)])]
        self.assertIn("UI-RAYCAST", rules(uv.validate(nodes(items)), "FAIL"))
        self.assertNotIn("UI-RAYCAST", rules(uv.validate(nodes(items, inactive=["Demo"]))))
        self.assertIn("UI-RAYCAST", rules(uv.validate(nodes(items, inactive=["Demo"]), include_inactive=True)))

    def test_viewport_is_not_a_double_frame(self):
        items = [dict(name="ScrollRect", rect=dict(size=(500, 300)), comps=[image()]),
                 dict(name="Viewport", father=0, rect=dict(size=(500, 300)), comps=[image()])]
        self.assertNotIn("UI-CHILD-EQ-PARENT", rules(uv.validate(nodes(items))))

    def test_overflow_mode_overflow_without_autosize_is_not_flagged(self):
        t = text("A very long title that cannot fit", 36).replace("m_RaycastTarget: 0\n", "m_RaycastTarget: 0\n  m_overflowMode: 0\n")
        n = nodes([dict(name="T", rect=dict(size=(100, 40)), comps=[t])])
        self.assertNotIn("UI-OVERFLOW", rules(uv.validate(n)))
        t2 = text("A very long title that cannot fit", 36).replace("m_RaycastTarget: 0\n", "m_RaycastTarget: 0\n  m_overflowMode: 1\n")
        n2 = nodes([dict(name="T", rect=dict(size=(100, 40)), comps=[t2])])
        self.assertIn("UI-OVERFLOW", rules(uv.validate(n2), "WARN"))

    def test_stacked_icon_and_label_not_checked(self):
        items = [dict(name="Card", rect=dict(size=(300, 400)), comps=[]),
                 dict(name="Icon", father=0, rect=dict(size=(200, 200), pos=(0, 80)), comps=[image()]),
                 dict(name="Text", father=0, rect=dict(size=(200, 50), pos=(0, -120)), comps=[text("Name", 36)])]
        self.assertNotIn("UI-ICON-LABEL", rules(uv.validate(nodes(items))))


if __name__ == "__main__":
    unittest.main()
