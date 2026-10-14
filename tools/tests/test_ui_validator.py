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


def rect(fid, go_id, father, amin=(0.5, 0.5), amax=(0.5, 0.5), size=(100, 100), pos=(0, 0), pivot=(0.5, 0.5)):
    return ("--- !u!224 &%d\nRectTransform:\n  m_GameObject: {fileID: %d}\n  m_Father: {fileID: %d}\n"
            "  m_AnchorMin: {x: %s, y: %s}\n  m_AnchorMax: {x: %s, y: %s}\n  m_AnchoredPosition: {x: %s, y: %s}\n"
            "  m_SizeDelta: {x: %s, y: %s}\n  m_Pivot: {x: %s, y: %s}\n"
            % (fid, go_id, father, amin[0], amin[1], amax[0], amax[1], pos[0], pos[1], size[0], size[1], pivot[0], pivot[1]))


def button(fid, go_id):
    return ("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Transition: 1\n"
            "  m_OnClick:\n    m_PersistentCalls:\n      m_Calls: []\n" % (fid, go_id))


def image(fid, go_id, raycast=1):
    return ("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Sprite: {fileID: 1, guid: a, type: 3}\n"
            "  m_PreserveAspect: 0\n  m_RaycastTarget: %d\n" % (fid, go_id, raycast))


def canvas(fid, go_id):
    return "--- !u!223 &%d\nCanvas:\n  m_GameObject: {fileID: %d}\n  m_RenderMode: 0\n" % (fid, go_id)


def prefab(children):
    """children: list of (name, rect kwargs, component kinds). A child with father=<fileID> nests under another."""
    parts = [go(1, "Canvas", [101, 102]), rect(101, 1, 0, amin=(0, 0), amax=(1, 1), size=(0, 0)), canvas(102, 1)]
    fid = 10
    for name, kw, extras in children:
        kw = dict(kw)
        gid, rid = fid, fid + 1
        comp_ids, bodies = [rid], []
        for kind in extras:
            cid = fid + 2 + len(bodies)
            comp_ids.append(cid)
            if kind == "button":
                bodies.append(button(cid, gid))
            elif kind == "scroll":
                bodies.append("--- !u!114 &%d\nMonoBehaviour:\n  m_GameObject: {fileID: %d}\n  m_Content: {fileID: 1}\n  m_Viewport: {fileID: 2}\n" % (cid, gid))
            else:
                bodies.append(image(cid, gid, 1 if kind == "image" else 0))
        parts.append(go(gid, name, comp_ids))
        parts.append(rect(rid, gid, kw.pop("father", 101), **kw))
        parts += bodies
        fid += 10
    return "%YAML 1.1\n" + "".join(parts)


def write_prefab(d, children, name="t.prefab"):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(prefab(children))
    return p


def run(children, **opts):
    with tempfile.TemporaryDirectory() as d:
        nodes = uv.nodes_from_prefab(write_prefab(d, children))
        return uv.validate(nodes, **opts)


def rules(findings, level=None):
    return sorted({f.rule for f in findings if level is None or f.level == level})


class ResolveTests(unittest.TestCase):
    def test_rect_resolution_centered(self):
        with tempfile.TemporaryDirectory() as d:
            nodes = uv.nodes_from_prefab(write_prefab(d, [("A", dict(size=(200, 100), pos=(10, 20)), ["button"])]))
            a = [n for n in nodes if n.name == "A"][0]
            r = uv.resolve_rects(nodes, (1920, 1080))[a.id]
            self.assertEqual(r, (960 + 10 - 100, 540 + 20 - 50, 960 + 10 + 100, 540 + 20 + 50))

    def test_stretch_with_offsets(self):
        with tempfile.TemporaryDirectory() as d:
            nodes = uv.nodes_from_prefab(write_prefab(d, [("S", dict(amin=(0, 0), amax=(1, 1), size=(-100, -60)), [])]))
            s = [n for n in nodes if n.name == "S"][0]
            self.assertEqual(uv.resolve_rects(nodes, (1000, 800))[s.id], (50, 30, 950, 770))

    def test_expand_canvas_size(self):
        self.assertEqual(uv.canvas_size((1920, 1080), (2400, 1080)), (2400, 1080))
        w, h = uv.canvas_size((1920, 1080), (1600, 1200))
        self.assertAlmostEqual(w, 1920)
        self.assertAlmostEqual(h, 1200 * 1920 / 1600)


class RuleTests(unittest.TestCase):
    def test_clean(self):
        f = run([("A", dict(size=(200, 100), pos=(-300, 0)), ["button"]),
                 ("B", dict(size=(200, 100), pos=(300, 0)), ["button"])])
        self.assertEqual(rules(f, "FAIL"), [])

    def test_overlap(self):
        f = run([("A", dict(size=(200, 100)), ["button"]), ("B", dict(size=(200, 100), pos=(50, 0)), ["button"])])
        self.assertIn("UI-OVERLAP", rules(f, "FAIL"))

    def test_overlap_ignores_parent_child(self):
        f = run([("A", dict(size=(400, 300)), ["button"]), ("B", dict(size=(100, 100), father=11), ["button"])])
        self.assertNotIn("UI-OVERLAP", rules(f))

    def test_safe_area(self):
        f = run([("A", dict(amin=(0, 1), amax=(0, 1), size=(100, 100), pos=(50, -50)), ["button"])],
                safe_inset=(0, 0, 0, 0), edge_margin=24)
        self.assertIn("UI-SAFE", rules(f, "FAIL"))

    def test_background_exempt_from_safe(self):
        f = run([("Background", dict(amin=(0, 0), amax=(1, 1), size=(0, 0)), ["image-off"])])
        self.assertNotIn("UI-SAFE", rules(f))

    def test_banner_clearance_for_hud(self):
        child = [("A", dict(amin=(0.5, 0), amax=(0.5, 0), size=(100, 100), pos=(0, 100)), ["button"])]
        self.assertIn("UI-BANNER", rules(run(child, hud=True, banner=200), "FAIL"))
        self.assertNotIn("UI-BANNER", rules(run(child, hud=False, banner=200)))

    def test_child_equals_parent(self):
        f = run([("Frame", dict(size=(300, 300)), ["image"]), ("Inner", dict(size=(300, 300), father=11), ["image-off"])])
        self.assertIn("UI-CHILD-EQ-PARENT", rules(f, "FAIL"))

    def test_raycast_on_decorative_graphic(self):
        self.assertIn("UI-RAYCAST", rules(run([("Deco", dict(size=(100, 100)), ["image"])]), "FAIL"))
        self.assertNotIn("UI-RAYCAST", rules(run([("Deco", dict(size=(100, 100)), ["image-off"])])))

    def test_container_panel_with_button_may_block_raycast(self):
        f = run([("Board", dict(size=(600, 400)), ["image"]), ("Btn", dict(size=(100, 100), father=11), ["button"])])
        self.assertNotIn("UI-RAYCAST", rules(f))

    def test_graphic_under_scroll_rect_may_raycast(self):
        f = run([("Scroll", dict(size=(600, 400)), ["scroll"]), ("Viewport", dict(size=(500, 300), father=11), ["image"])])
        self.assertNotIn("UI-RAYCAST", rules(f))

    def test_child_eq_parent_needs_graphic_child(self):
        f = run([("Frame", dict(size=(300, 300)), ["image-off"]), ("Content", dict(size=(300, 300), father=11), [])])
        self.assertNotIn("UI-CHILD-EQ-PARENT", rules(f))

    def test_inactive_state_panels_skip_overlap_unless_requested(self):
        text = prefab([("A", dict(size=(200, 100)), ["button"]), ("B", dict(size=(200, 100), pos=(50, 0)), ["button"])])
        text = text.replace("m_Name: B\n", "m_Name: B\n  m_IsActive: 0\n")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.prefab")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            nodes = uv.nodes_from_prefab(p)
        self.assertNotIn("UI-OVERLAP", rules(uv.validate(nodes)))
        self.assertIn("UI-OVERLAP", rules(uv.validate(nodes, include_inactive=True)))

    def test_touch_target_is_soft_and_needs_reason(self):
        children = [("Small", dict(size=(40, 40)), ["button"])]
        self.assertIn("UI-TOUCH", rules(run(children), "WARN"))
        ok = [{"rule": "UI-TOUCH", "path": "Canvas/Small", "reason": "matches reference", "owner": "x"}]
        self.assertNotIn("UI-TOUCH", rules(run(children, exceptions=ok)))

    def test_exception_without_reason_is_ignored(self):
        f = run([("Small", dict(size=(40, 40)), ["button"])], exceptions=[{"rule": "UI-TOUCH", "path": "Canvas/Small"}])
        self.assertIn("UI-TOUCH", rules(f))

    def test_multiple_aspects(self):
        with tempfile.TemporaryDirectory() as d:
            nodes = uv.nodes_from_prefab(write_prefab(d, [("A", dict(size=(200, 100), pos=(-300, 0)), ["button"])]))
            res = uv.validate_aspects(nodes, ref=(1920, 1080))
        self.assertEqual(sorted(res), ["1600x1200", "1920x1080", "2400x1080"])


class CliTests(unittest.TestCase):
    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            ok = write_prefab(d, [("A", dict(size=(200, 100), pos=(-300, 0)), ["button"])], "ok.prefab")
            bad = write_prefab(d, [("A", dict(size=(200, 100)), ["button"]), ("B", dict(size=(200, 100)), ["button"])], "bad.prefab")
            self.assertEqual(uv.main([ok]), 0)
            self.assertEqual(uv.main([bad]), 1)


if __name__ == "__main__":
    unittest.main()
