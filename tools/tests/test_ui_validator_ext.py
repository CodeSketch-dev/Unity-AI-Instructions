import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-validator", "scripts"))
sys.path.insert(0, HERE)

import ui_validator as uv  # noqa: E402
from test_ui_validator import go, rect, canvas  # noqa: E402

GUID_SLICED = "1" * 32
GUID_PLAIN = "2" * 32


def sprite_image(fid, go_id, guid, img_type=0, raycast=0):
    return ("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Sprite: {fileID: 21300000, guid: %s, type: 3}\n"
            "  m_Type: %d\n  m_PreserveAspect: 0\n  m_RaycastTarget: %d\n" % (fid, go_id, guid, img_type, raycast))


def tmp_text(fid, go_id, text, size=36, mn=18, auto=0):
    return ("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_text: %s\n  m_fontSize: %d\n"
            "  m_fontSizeMin: %d\n  m_enableAutoSizing: %d\n  m_RaycastTarget: 0\n" % (fid, go_id, text, size, mn, auto))


def build(items):
    """items: list of (name, rect kwargs, component body builder taking (cid, gid))."""
    parts = [go(1, "Canvas", [101, 102]), rect(101, 1, 0, amin=(0, 0), amax=(1, 1), size=(0, 0)), canvas(102, 1)]
    fid = 10
    for name, kw, make in items:
        kw = dict(kw)
        gid, rid, cid = fid, fid + 1, fid + 2
        parts.append(go(gid, name, [rid, cid]))
        parts.append(rect(rid, gid, kw.pop("father", 101), **kw))
        parts.append(make(cid, gid))
        fid += 10
    return "%YAML 1.1\n" + "".join(parts)


def nodes(items):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.prefab")
        with open(p, "w", encoding="utf-8") as f:
            f.write(build(items))
        return uv.nodes_from_prefab(p)


def rules(findings, level=None):
    return sorted({f.rule for f in findings if level is None or f.level == level})


class SpriteBorderTests(unittest.TestCase):
    def test_borders_from_meta(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "Assets", "Art"))
            with open(os.path.join(d, "Assets", "Art", "frame.png.meta"), "w") as f:
                f.write("fileFormatVersion: 2\nguid: %s\nTextureImporter:\n  spriteBorder: {x: 20, y: 10, z: 20, w: 10}\n" % GUID_SLICED)
            with open(os.path.join(d, "Assets", "Art", "plain.png.meta"), "w") as f:
                f.write("fileFormatVersion: 2\nguid: %s\nTextureImporter:\n  spriteBorder: {x: 0, y: 0, z: 0, w: 0}\n" % GUID_PLAIN)
            b = uv.sprite_borders(d)
        self.assertEqual(b, {GUID_SLICED: (20.0, 10.0, 20.0, 10.0)})

    def test_borders_scaled_by_sprite_ppu(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "Assets"))
            with open(os.path.join(d, "Assets", "big.png.meta"), "w") as f:
                f.write("guid: %s\nspritePixelsToUnits: 200\nspriteBorder: {x: 40, y: 20, z: 40, w: 20}\n" % GUID_SLICED)
            self.assertEqual(uv.sprite_borders(d), {GUID_SLICED: (20.0, 10.0, 20.0, 10.0)})

    def test_bordered_sprite_must_be_sliced(self):
        n = nodes([("Frame", dict(size=(300, 200)), lambda c, g: sprite_image(c, g, GUID_SLICED, img_type=0))])
        f = uv.validate(n, sprite_borders={GUID_SLICED: (20, 10, 20, 10)})
        self.assertIn("UI-9SLICE", rules(f, "FAIL"))

    def test_sliced_ok_and_plain_ignored(self):
        n = nodes([("Frame", dict(size=(300, 200)), lambda c, g: sprite_image(c, g, GUID_SLICED, img_type=1))])
        self.assertNotIn("UI-9SLICE", rules(uv.validate(n, sprite_borders={GUID_SLICED: (20, 10, 20, 10)})))
        n2 = nodes([("Plain", dict(size=(300, 200)), lambda c, g: sprite_image(c, g, GUID_PLAIN, img_type=0))])
        self.assertNotIn("UI-9SLICE", rules(uv.validate(n2, sprite_borders={GUID_SLICED: (20, 10, 20, 10)})))

    def test_rect_smaller_than_border_sum(self):
        n = nodes([("Tiny", dict(size=(30, 200)), lambda c, g: sprite_image(c, g, GUID_SLICED, img_type=1))])
        self.assertIn("UI-9SLICE", rules(uv.validate(n, sprite_borders={GUID_SLICED: (20, 10, 20, 10)}), "WARN"))


class OverflowTests(unittest.TestCase):
    def test_long_text_in_small_rect_warns(self):
        n = nodes([("Title", dict(size=(100, 40)), lambda c, g: tmp_text(c, g, "A very long title that cannot fit", size=36))])
        self.assertIn("UI-OVERFLOW", rules(uv.validate(n), "WARN"))

    def test_short_text_ok(self):
        n = nodes([("Title", dict(size=(300, 60)), lambda c, g: tmp_text(c, g, "Play", size=36))])
        self.assertNotIn("UI-OVERFLOW", rules(uv.validate(n)))

    def test_autosize_uses_min_font(self):
        text = "Equipped now"
        small = nodes([("T", dict(size=(150, 60)), lambda c, g: tmp_text(c, g, text, size=60, mn=18, auto=1))])
        self.assertNotIn("UI-OVERFLOW", rules(uv.validate(small)))
        nofit = nodes([("T", dict(size=(150, 60)), lambda c, g: tmp_text(c, g, text, size=60, mn=18, auto=0))])
        self.assertIn("UI-OVERFLOW", rules(uv.validate(nofit)))

    def test_min_font_below_18_warns(self):
        n = nodes([("T", dict(size=(400, 60)), lambda c, g: tmp_text(c, g, "Hi", size=36, mn=10, auto=1))])
        self.assertIn("UI-FONT-MIN", rules(uv.validate(n), "WARN"))


class RefMatchTests(unittest.TestCase):
    def test_match_and_mismatch(self):
        ref = nodes([("Btn", dict(size=(200, 80), pos=(10, 20)), lambda c, g: sprite_image(c, g, GUID_PLAIN))])
        same = nodes([("Btn", dict(size=(201, 80), pos=(11, 20)), lambda c, g: sprite_image(c, g, GUID_PLAIN))])
        off = nodes([("Btn", dict(size=(240, 80), pos=(10, 20)), lambda c, g: sprite_image(c, g, GUID_SLICED))])
        self.assertEqual(uv.ref_match(ref, same, (1920, 1080)), [])
        f = uv.ref_match(ref, off, (1920, 1080))
        self.assertEqual({x.rule for x in f}, {"UI-REF-MATCH"})
        self.assertEqual(len(f), 2)  # size and sprite

    def test_missing_element(self):
        ref = nodes([("Btn", dict(size=(200, 80)), lambda c, g: sprite_image(c, g, GUID_PLAIN))])
        act = nodes([("Other", dict(size=(200, 80)), lambda c, g: sprite_image(c, g, GUID_PLAIN))])
        f = uv.ref_match(ref, act, (1920, 1080))
        self.assertTrue(any("missing" in x.message for x in f))


if __name__ == "__main__":
    unittest.main()
