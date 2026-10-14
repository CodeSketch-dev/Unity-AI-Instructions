import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-validator", "scripts"))

import ui_validator as uv  # noqa: E402


def go(fid, name, comps):
    return "--- !u!1 &%d\nGameObject:\n  m_Name: %s\n  m_Component:\n%s" % (
        fid, name, "".join("  - component: {fileID: %d}\n" % c for c in comps))


def rect(fid, go_id, father, amin=(0.5, 0.5), amax=(0.5, 0.5), size=(100, 100), pos=(0, 0), scale=(1, 1, 1)):
    return ("--- !u!224 &%d\nRectTransform:\n  m_GameObject: {fileID: %d}\n  m_LocalScale: {x: %s, y: %s, z: %s}\n  m_Father: {fileID: %d}\n"
            "  m_AnchorMin: {x: %s, y: %s}\n  m_AnchorMax: {x: %s, y: %s}\n  m_AnchoredPosition: {x: %s, y: %s}\n"
            "  m_SizeDelta: {x: %s, y: %s}\n  m_Pivot: {x: 0.5, y: 0.5}\n"
            % (fid, go_id, scale[0], scale[1], scale[2], father, amin[0], amin[1], amax[0], amax[1], pos[0], pos[1], size[0], size[1]))


def mono(fid, go_id, body, script="{fileID: 11500000, guid: %s, type: 3}" % ("c" * 32)):
    return "--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Script: %s\n%s" % (fid, go_id, script, body)


BUTTON = "  m_Transition: 1\n  m_OnClick:\n    m_PersistentCalls:\n      m_Calls: []\n"
STRETCH = dict(amin=(0, 0), amax=(1, 1), size=(0, 0))


def image(sprite="a" * 32, raycast=0):
    return "  m_Sprite: {fileID: 21300000, guid: %s, type: 3}\n  m_Type: 1\n  m_PreserveAspect: 0\n  m_RaycastTarget: %d\n" % (sprite, raycast)


def text(t="Hi", size=36):
    return "  m_text: %s\n  m_fontSize: %d\n  m_fontSizeMin: 18\n  m_enableAutoSizing: 0\n  m_RaycastTarget: 0\n" % (t, size)


def make(items, canvas_root=True):
    """items: list of dicts name, father(index of item or None), rect kwargs, comps (list of mono bodies or None)."""
    parts = []
    ids = {}
    fid = 10
    for idx, it in enumerate(items):
        gid, rid = fid, fid + 1
        ids[idx] = (gid, rid)
        comp_ids = [rid]
        bodies = []
        for k, body in enumerate(it.get("comps", [])):
            cid = fid + 2 + k
            comp_ids.append(cid)
            bodies.append(mono(cid, gid, body) if not isinstance(body, tuple) else mono(cid, gid, body[0], script=body[1]))
        father = ids[it["father"]][1] if it.get("father") is not None else 0
        parts.append(go(gid, it["name"], comp_ids))
        parts.append(rect(rid, gid, father, **it.get("rect", {})))
        parts += bodies
        fid += 20
    return "%YAML 1.1\n" + "".join(parts)


def nodes(items):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.prefab")
        with open(p, "w", encoding="utf-8") as f:
            f.write(make(items))
        return uv.nodes_from_prefab(p)


def rules(findings, level=None):
    return sorted({f.rule for f in findings if level is None or f.level == level})


def popup(root_rect=None, root_comps=None, extra=None):
    items = [dict(name="Feature_Popup", rect=STRETCH, comps=[]),
             dict(name="Root", father=0, rect=root_rect or STRETCH, comps=root_comps or [])]
    return items + (extra or [])


class StructTests(unittest.TestCase):
    def test_good_popup(self):
        self.assertEqual(rules(uv.struct_findings(nodes(popup()), "popup")), [])

    def test_missing_root(self):
        items = [dict(name="Feature_Popup", rect=STRETCH, comps=[]), dict(name="Board", father=0, rect=STRETCH, comps=[])]
        self.assertIn("UI-STRUCT", rules(uv.struct_findings(nodes(items), "popup"), "FAIL"))

    def test_root_not_stretched(self):
        f = uv.struct_findings(nodes(popup(root_rect=dict(size=(100, 100)))), "popup")
        self.assertIn("UI-STRUCT", rules(f, "FAIL"))

    def test_root_with_graphic(self):
        f = uv.struct_findings(nodes(popup(root_comps=[image()])), "popup")
        self.assertIn("UI-STRUCT", rules(f, "FAIL"))

    def test_second_child_besides_root(self):
        f = uv.struct_findings(nodes(popup(extra=[dict(name="Other", father=0, rect=STRETCH, comps=[])])), "popup")
        self.assertIn("UI-STRUCT", rules(f, "FAIL"))


class CanvasTests(unittest.TestCase):
    def write(self, d, mode=0, scale_mode=1, match=1, ref="1920, y: 1080"):
        text_ = ("%YAML 1.1\n" + go(1, "Canvas", [2, 3, 4])
                 + rect(2, 1, 0, **STRETCH)
                 + "--- !u!223 &3\nCanvas:\n  m_GameObject: {fileID: 1}\n  m_RenderMode: %d\n" % mode
                 + mono(4, 1, "  m_UiScaleMode: %d\n  m_ReferenceResolution: {x: %s}\n  m_ScreenMatchMode: %d\n" % (scale_mode, ref, match)))
        p = os.path.join(d, "c.prefab")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text_)
        return p

    def test_ok(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(uv.canvas_findings(self.write(d)), [])

    def test_bad_values(self):
        with tempfile.TemporaryDirectory() as d:
            f = uv.canvas_findings(self.write(d, mode=2, scale_mode=0, match=0))
            self.assertEqual(rules(f, "FAIL"), ["UI-STRUCT"])
            self.assertEqual(len(f), 3)


class MirrorMissingTests(unittest.TestCase):
    def test_mirrored_text(self):
        n = nodes([dict(name="Label", rect=dict(scale=(-1, 1, 1)), comps=[text()])])
        self.assertIn("UI-MIRROR", rules(uv.validate(n), "FAIL"))

    def test_mirror_inherited_from_parent(self):
        n = nodes([dict(name="Flip", rect=dict(scale=(-1, 1, 1)), comps=[]),
                   dict(name="Label", father=0, rect=dict(size=(100, 50)), comps=[text()])])
        self.assertIn("UI-MIRROR", rules(uv.validate(n), "FAIL"))

    def test_mirrored_non_text_is_fine(self):
        n = nodes([dict(name="Arrow", rect=dict(scale=(-1, 1, 1)), comps=[image()])])
        self.assertNotIn("UI-MIRROR", rules(uv.validate(n)))

    def test_missing_script(self):
        n = nodes([dict(name="X", comps=[("  foo: 1\n", "{fileID: 0}")])])
        self.assertIn("UI-MISSING", rules(uv.validate(n), "FAIL"))

    def test_missing_sprite_reference(self):
        n = nodes([dict(name="X", comps=[image("d" * 32)])])
        self.assertIn("UI-MISSING", rules(uv.validate(n, project_guids={"a" * 32, "c" * 32}), "FAIL"))
        self.assertNotIn("UI-MISSING", rules(uv.validate(n, project_guids={"d" * 32, "c" * 32})))

    def test_builtin_sprite_guid_not_missing(self):
        builtin = "0000000000000000f000000000000000"
        n = nodes([dict(name="X", comps=[image(builtin)])])
        self.assertNotIn("UI-MISSING", rules(uv.validate(n, project_guids={"a" * 32, "c" * 32})))

    def test_project_guids_reads_meta(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "Assets"))
            with open(os.path.join(d, "Assets", "a.png.meta"), "w") as f:
                f.write("guid: %s\n" % ("e" * 32))
            self.assertIn("e" * 32, uv.project_guids(d))


class SoftRuleTests(unittest.TestCase):
    def row(self, xs, w=200):
        return [dict(name="B%d" % i, rect=dict(size=(w, 100), pos=(x, 0)), comps=[BUTTON]) for i, x in enumerate(xs)]

    def test_uneven_spacing_warns(self):
        n = nodes(self.row([-500, -250, 100]))   # gaps 50 and 150
        self.assertIn("UI-SPACING", rules(uv.validate(n), "WARN"))

    def test_even_spacing_ok(self):
        n = nodes(self.row([-400, 0, 400]))
        self.assertNotIn("UI-SPACING", rules(uv.validate(n)))

    def icon_label(self, icon_h, text_dy=0):
        return [dict(name="Btn", rect=dict(size=(300, 100)), comps=[BUTTON]),
                dict(name="Icon", father=0, rect=dict(size=(icon_h, icon_h), pos=(-80, 0)), comps=[image()]),
                dict(name="Text", father=0, rect=dict(size=(160, 50), pos=(40, text_dy)), comps=[text("Buy", 36)])]

    def test_icon_label_ratio_warns_when_icon_huge(self):
        self.assertIn("UI-ICON-LABEL", rules(uv.validate(nodes(self.icon_label(100))), "WARN"))

    def test_icon_label_ok(self):
        self.assertNotIn("UI-ICON-LABEL", rules(uv.validate(nodes(self.icon_label(40)))))

    def test_icon_label_vertical_offset_warns(self):
        self.assertIn("UI-ICON-LABEL", rules(uv.validate(nodes(self.icon_label(40, text_dy=12))), "WARN"))

    def test_center_free_only_for_hud(self):
        n = nodes([dict(name="Mid", rect=dict(size=(200, 100)), comps=[BUTTON])])
        self.assertIn("UI-CENTER-FREE", rules(uv.validate(n, hud=True), "WARN"))
        self.assertNotIn("UI-CENTER-FREE", rules(uv.validate(n, hud=False)))


class DumpTests(unittest.TestCase):
    def test_text_rects_dump(self):
        n = nodes([dict(name="Label", rect=dict(size=(200, 50), pos=(10, 20)), comps=[text()])])
        d = uv.text_rects(n, (1920, 1080))
        self.assertEqual(d[0]["path"], "Label")
        self.assertEqual(d[0]["rect"], [870, 535, 1070, 585])


if __name__ == "__main__":
    unittest.main()
