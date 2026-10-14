import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-design-tokens", "scripts"))

import ui_miner as um  # noqa: E402


def go(fid, name, comps):
    lines = ["--- !u!1 &%d" % fid, "GameObject:", "  m_Name: %s" % name, "  m_IsActive: 1", "  m_Component:"]
    lines += ["  - component: {fileID: %d}" % c for c in comps]
    return "\n".join(lines) + "\n"


def rect(fid, go_id, father, amin=(0.5, 0.5), amax=(0.5, 0.5), size=(100, 100), pos=(0, 0)):
    return ("--- !u!224 &%d\nRectTransform:\n  m_GameObject: {fileID: %d}\n  m_Father: {fileID: %d}\n"
            "  m_AnchorMin: {x: %s, y: %s}\n  m_AnchorMax: {x: %s, y: %s}\n"
            "  m_AnchoredPosition: {x: %s, y: %s}\n  m_SizeDelta: {x: %s, y: %s}\n  m_Pivot: {x: 0.5, y: 0.5}\n"
            % (fid, go_id, father, amin[0], amin[1], amax[0], amax[1], pos[0], pos[1], size[0], size[1]))


def mono(fid, go_id, guid, body):
    return ("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Script: {fileID: 11500000, guid: %s, type: 3}\n%s"
            % (fid, go_id, guid, body))


def canvas(fid, go_id, mode=0, order=100):
    return "--- !u!223 &%d\nCanvas:\n  m_GameObject: {fileID: %d}\n  m_RenderMode: %d\n  m_SortingOrder: %d\n" % (fid, go_id, mode, order)


SCALER = "  m_UiScaleMode: 1\n  m_ReferenceResolution: {x: 1920, y: 1080}\n  m_ScreenMatchMode: 0\n"
BUTTON = "  m_Transition: 1\n  m_OnClick:\n    m_PersistentCalls:\n      m_Calls: []\n"
IMAGE = "  m_Sprite: {fileID: 21300000, guid: aaa, type: 3}\n  m_Type: 1\n  m_PreserveAspect: 0\n  m_RaycastTarget: %d\n"
TMP = "  m_fontSize: 36\n  m_fontSizeMin: 18\n  m_fontSizeMax: 50\n  m_enableAutoSizing: 1\n  m_RaycastTarget: %d\n"
SCROLL = "  m_Content: {fileID: 9}\n  m_Viewport: {fileID: 8}\n  m_Horizontal: 0\n"
HLG = "  m_ChildAlignment: 4\n  m_Spacing: 10\n  m_ChildControlWidth: 1\n  m_ChildControlHeight: 0\n"
GRID = "  m_CellSize: {x: 266, y: 267}\n  m_Spacing: {x: 49, y: 55}\n"


def prefab_text():
    parts = [
        go(1, "Canvas", [101, 102, 103]), rect(101, 1, 0, size=(0, 0)), canvas(102, 1, 0, 2506),
        mono(103, 1, "scaler00000000000000000000000000", SCALER),
        go(2, "Btn_Close", [201, 202, 203, 204]), rect(201, 2, 101, size=(100, 100)),
        mono(202, 2, "image000000000000000000000000000", IMAGE % 1),
        mono(203, 2, "button00000000000000000000000000", BUTTON),
        mono(204, 2, "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "  _target: {fileID: 0}\n"),
        go(3, "Text_Title", [301, 302]), rect(301, 3, 201, size=(200, 50)),
        mono(302, 3, "tmp0000000000000000000000000000", TMP % 0),
        go(4, "Btn_Buy", [401, 402, 403]), rect(401, 4, 101, size=(280, 100)),
        mono(402, 4, "button00000000000000000000000000", BUTTON),
        mono(403, 4, "image000000000000000000000000000", IMAGE % 1),
        go(5, "ScrollRect", [501, 502]), rect(501, 5, 101, amin=(0, 0), amax=(1, 1), size=(-60, -120)),
        mono(502, 5, "scroll00000000000000000000000000", SCROLL),
        go(6, "Layout", [601, 602]), rect(601, 6, 101, size=(300, 80)),
        mono(602, 6, "hlg0000000000000000000000000000", HLG),
        go(7, "Grid", [701, 702]), rect(701, 7, 101, size=(900, 600)),
        mono(702, 7, "grid000000000000000000000000000", GRID),
    ]
    return "%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n" + "".join(parts)


class MinerTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        p = os.path.join(self.t.name, "Assets", "_Game", "Prefabs", "UI")
        os.makedirs(p)
        with open(os.path.join(p, "Test_Popup.prefab"), "w", encoding="utf-8") as f:
            f.write(prefab_text())
        sp = os.path.join(self.t.name, "Assets", "_Game", "Scripts")
        os.makedirs(sp)
        with open(os.path.join(sp, "UIPressPrimeTween.cs.meta"), "w") as f:
            f.write("fileFormatVersion: 2\nguid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n")
        with open(os.path.join(sp, "UIPressPrimeTween.cs"), "w") as f:
            f.write("class UIPressPrimeTween {}\n")
        self.tokens = um.mine(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def test_canvas_and_scaler(self):
        c = self.tokens["canvas"]
        self.assertEqual(c["render_modes"], {"0": 1})
        self.assertEqual(c["sort_orders"], [2506])
        self.assertEqual(c["scalers"][0]["reference_resolution"], [1920, 1080])
        self.assertEqual(c["scalers"][0]["match_mode"], 0)

    def test_button_sizes_quantized(self):
        sizes = {tuple(s["size"]): s["count"] for s in self.tokens["buttons"]["sizes"]}
        self.assertEqual(sizes, {(100, 100): 1, (280, 100): 1})

    def test_button_anatomy_resolves_script_names(self):
        names = {s["script"]: s["buttons_with"] for s in self.tokens["buttons"]["co_scripts"]}
        self.assertEqual(names.get("UIPressPrimeTween"), 1)
        self.assertEqual(self.tokens["buttons"]["total"], 2)

    def test_text_stats(self):
        t = self.tokens["text"]
        self.assertEqual(t["total"], 1)
        self.assertEqual(t["autosize_ratio"], 1.0)
        self.assertEqual(t["min_sizes"], {"18": 1})
        self.assertEqual(t["raycast_off_ratio"], 1.0)

    def test_image_raycast(self):
        self.assertEqual(self.tokens["images"]["total"], 2)
        self.assertEqual(self.tokens["images"]["raycast_off_ratio"], 0.0)

    def test_scroll_inset(self):
        s = self.tokens["scroll"]
        self.assertEqual(s["total"], 1)
        self.assertEqual(s["insets"][0], {"name": "ScrollRect", "horizontal_total": 60, "vertical_total": 120})

    def test_layout_and_grid(self):
        self.assertEqual(self.tokens["layout"]["linear_spacing"], {"10": 1})
        self.assertEqual(self.tokens["layout"]["grids"], [{"cell": [266, 267], "spacing": [49, 55]}])

    def test_naming_prefixes(self):
        n = self.tokens["naming"]["prefixes"]
        self.assertEqual(n.get("Btn"), 2)
        self.assertEqual(n.get("Text"), 1)

    def test_non_ui_prefab_skipped_and_zero_size_ignored(self):
        p = os.path.join(self.t.name, "Assets", "_Game", "Prefabs", "World")
        os.makedirs(p)
        with open(os.path.join(p, "Rock.prefab"), "w", encoding="utf-8") as f:
            f.write("%YAML 1.1\n" + go(1, "Rock_Mesh", []))
        t = um.mine(self.t.name)
        self.assertEqual(t["prefabs_scanned"], 1)
        self.assertNotIn("Rock", t["naming"]["prefixes"])

    def test_empty_project(self):
        with tempfile.TemporaryDirectory() as r:
            os.makedirs(os.path.join(r, "Assets"))
            t = um.mine(r)
            self.assertEqual(t["prefabs_scanned"], 0)
            self.assertEqual(t["buttons"]["total"], 0)

    def test_cli_writes_json(self):
        out = os.path.join(self.t.name, "tokens.json")
        self.assertEqual(um.main([self.t.name, "--out", out]), 0)
        self.assertEqual(json.load(open(out, encoding="utf-8"))["prefabs_scanned"], 1)


if __name__ == "__main__":
    unittest.main()
