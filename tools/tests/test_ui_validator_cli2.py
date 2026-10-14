import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-validator", "scripts"))
sys.path.insert(0, HERE)

import ui_validator as uv  # noqa: E402
from test_ui_validator_rules2 import make, popup, text, STRETCH  # noqa: E402


class CliKindTests(unittest.TestCase):
    def write(self, d, items, name="p.prefab"):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(make(items))
        return p

    def test_popup_structure_checked_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            ok = self.write(d, popup())
            bad = self.write(d, [dict(name="Feature_Popup", rect=STRETCH, comps=[]), dict(name="Board", father=0, rect=STRETCH, comps=[])], "bad.prefab")
            self.assertEqual(uv.main([ok]), 0)
            self.assertEqual(uv.main([bad]), 1)
            self.assertEqual(uv.main([bad, "--kind", "none"]), 0)

    def test_dump_rects(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.write(d, popup(extra=[dict(name="Label", father=1, rect=dict(size=(200, 50)), comps=[text()])]))
            out = os.path.join(d, "t.json")
            uv.main([p, "--dump-rects", out])
            data = json.load(open(out, encoding="utf-8"))
            self.assertEqual(data["canvas"], [1920, 1080])
            self.assertEqual(data["texts"][0]["path"], "Feature_Popup/Root/Label")


if __name__ == "__main__":
    unittest.main()
