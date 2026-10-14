import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills", "character-skin-importer")
sys.path.insert(0, os.path.join(SK, "scripts"))

import skin_validator as sv  # noqa: E402

EXAMPLE = os.path.join(SK, "assets", "character-catalog.example.json")


def load_example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def codes(findings, level=None):
    return sorted({f.code for f in findings if level is None or f.level == level})


class CatalogTests(unittest.TestCase):
    def test_example_is_clean(self):
        self.assertEqual(codes(sv.check_catalog(load_example()), "FAIL"), [])

    def test_hash_is_order_sensitive_and_stable(self):
        a = sv.skeleton_hash(["Hips", "Spine", "Head"])
        self.assertEqual(a, sv.skeleton_hash(["Hips", "Spine", "Head"]))
        self.assertNotEqual(a, sv.skeleton_hash(["Hips", "Head", "Spine"]))
        self.assertIsInstance(a, int)

    def test_duplicate_skin_id_and_unknown_rig(self):
        c = load_example()
        c["skins"].append(dict(c["skins"][0]))
        c["skins"][1]["rig"] = "nope"
        found = codes(sv.check_catalog(c), "FAIL")
        self.assertIn("duplicate-skin-id", found)
        self.assertIn("unknown-rig", found)

    def test_unlock_rules(self):
        c = load_example()
        c["skins"] = [
            {"id": "a", "type": "Normal", "rig": "humanoid", "unlock": "IAP", "price": 0, "iap_id": None, "order": 1},
            {"id": "b", "type": "Normal", "rig": "humanoid", "unlock": "Gem", "price": 0, "iap_id": None, "order": 2},
            {"id": "c", "type": "Normal", "rig": "humanoid", "unlock": "Free", "price": 50, "iap_id": None, "order": 3},
            {"id": "d", "type": "Normal", "rig": "humanoid", "unlock": "Teleport", "price": 0, "iap_id": None, "order": 4}]
        found = codes(sv.check_catalog(c), "FAIL")
        self.assertIn("iap-without-id", found)
        self.assertIn("gem-without-price", found)
        self.assertIn("free-with-price", found)
        self.assertIn("bad-unlock", found)

    def test_unknown_type_and_mode_reference(self):
        c = load_example()
        c["skins"][0]["type"] = "Alien"
        c["allowed_types_per_mode"]["obby"] = ["Ghost"]
        found = codes(sv.check_catalog(c), "FAIL")
        self.assertIn("unknown-type", found)
        self.assertIn("unknown-mode-type", found)

    def test_rig_slot_bone_must_exist(self):
        c = load_example()
        c["rigs"]["humanoid"]["slots"].append({"id": "tail", "bone": "NoSuchBone"})
        self.assertIn("slot-bone-missing", codes(sv.check_catalog(c), "FAIL"))

    def test_rig_exceeding_its_own_limit(self):
        c = load_example()
        c["rigs"]["humanoid"]["max_bones"] = 3
        self.assertIn("rig-over-limit", codes(sv.check_catalog(c), "FAIL"))

    def test_duplicate_order_is_warning(self):
        c = load_example()
        c["skins"].append(dict(c["skins"][0], id="Character_Skin_Copy"))
        self.assertIn("duplicate-order", codes(sv.check_catalog(c), "WARN"))


def go(fid, name, comps):
    return "--- !u!1 &%d\nGameObject:\n  m_Name: %s\n  m_Component:\n%s" % (
        fid, name, "".join("  - component: {fileID: %d}\n" % c for c in comps))


def tr(fid, go_id, father=0):
    return "--- !u!4 &%d\nTransform:\n  m_GameObject: {fileID: %d}\n  m_Father: {fileID: %d}\n" % (fid, go_id, father)


def smr(fid, go_id, bones, materials=1, shadows=0, offscreen=0):
    mats = "".join("  - {fileID: 2100000, guid: m, type: 2}\n" for _ in range(materials))
    bl = "".join("  - {fileID: %d}\n" % b for b in bones)
    return ("--- !u!137 &%d\nSkinnedMeshRenderer:\n  m_GameObject: {fileID: %d}\n  m_CastShadows: %d\n  m_Materials:\n%s"
            "  m_UpdateWhenOffscreen: %d\n  m_Bones:\n%s" % (fid, go_id, shadows, mats, offscreen, bl))


def animator(fid, go_id, cull=2, controller="c" * 32):
    return ("--- !u!95 &%d\nAnimator:\n  m_GameObject: {fileID: %d}\n  m_Controller: {fileID: 9100000, guid: %s, type: 2}\n"
            "  m_CullingMode: %d\n" % (fid, go_id, controller, cull))


def simple(cls, name, fid, go_id):
    return "--- !u!%d &%d\n%s:\n  m_GameObject: {fileID: %d}\n" % (cls, fid, name, go_id)


BONES = ["Hips", "Spine", "Head"]


def skin_prefab(bones=BONES, materials=1, shadows=0, cull=2, extra=(), animators=1, offscreen=0, missing_script=False):
    parts, ids, n = [], {}, 10
    for b in bones:
        ids[b] = (n, n + 1)
        parts.append(go(n, b, [n + 1]))
        parts.append(tr(n + 1, n, 0))
        n += 10
    parts.append(go(1, "Mesh", [2, 3]))
    parts.append(tr(2, 1, 0))
    parts.append(smr(3, 1, [ids[b][1] for b in bones], materials, shadows, offscreen))
    parts.append(go(4, "Root", [5]))
    parts.append(tr(5, 4, 0))
    for i in range(animators):
        parts.append(animator(50 + i, 4, cull))
    for cls, name in extra:
        parts.append(simple(cls, name, 70 + cls, 4))
    if missing_script:
        parts.append("--- !u!114 &90\nMonoBehaviour:\n  m_GameObject: {fileID: 4}\n  m_Script: {fileID: 0}\n")
    return "%YAML 1.1\n" + "".join(parts)


def run(text, role="bot", rig=None, **kw):
    cat = load_example()
    rig = rig or dict(cat["rigs"]["humanoid"], required_bones=BONES, max_bones=25)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.prefab")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return sv.check_prefab(p, rig, cat["budgets"][role], role, **kw)


class PrefabTests(unittest.TestCase):
    def test_clean_prefab(self):
        self.assertEqual(codes(run(skin_prefab()), "FAIL"), [])

    def test_bone_mismatch(self):
        self.assertIn("bone-mismatch", codes(run(skin_prefab(bones=["Hips", "Head", "Spine"])), "FAIL"))
        self.assertIn("bone-mismatch", codes(run(skin_prefab(bones=["Hips", "Spine"])), "FAIL"))

    def test_material_and_bone_budget(self):
        self.assertIn("too-many-materials", codes(run(skin_prefab(materials=3)), "FAIL"))
        r = run(skin_prefab(), rig={"required_bones": BONES, "max_bones": 2})
        self.assertIn("too-many-bones", codes(r, "FAIL"))

    def test_bot_shadows_and_culling_warn(self):
        r = run(skin_prefab(shadows=1, cull=0))
        self.assertIn("bot-shadows", codes(r, "WARN"))
        self.assertIn("bot-culling", codes(r, "WARN"))
        self.assertNotIn("bot-shadows", codes(run(skin_prefab(shadows=1, cull=0), role="player")))

    def test_baked_ragdoll_camera_light_forbidden(self):
        r = run(skin_prefab(extra=[(54, "Rigidbody"), (144, "CharacterJoint"), (20, "Camera"), (108, "Light")]))
        found = codes(r, "FAIL")
        self.assertIn("baked-ragdoll", found)
        self.assertIn("camera-or-light", found)

    def test_animator_count_and_offscreen(self):
        self.assertIn("animator-count", codes(run(skin_prefab(animators=2)), "FAIL"))
        self.assertIn("animator-count", codes(run(skin_prefab(animators=0)), "FAIL"))
        self.assertIn("update-offscreen", codes(run(skin_prefab(offscreen=1)), "WARN"))

    def test_missing_script(self):
        self.assertIn("missing-script", codes(run(skin_prefab(missing_script=True)), "FAIL"))

    def test_stats_budget(self):
        r = run(skin_prefab(), stats={"tris": 5000, "texture": 1024})
        self.assertIn("tri-budget", codes(r, "FAIL"))
        self.assertIn("texture-budget", codes(r, "FAIL"))
        self.assertEqual(codes(run(skin_prefab(), stats={"tris": 900, "texture": 256}), "FAIL"), [])

    def test_shared_mesh_flag(self):
        self.assertTrue(any(f.code == "shared-mesh-ok" for f in run(skin_prefab())))


class CliTests(unittest.TestCase):
    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            cat = load_example()
            cat["rigs"]["humanoid"]["required_bones"] = BONES
            cat["rigs"]["humanoid"]["slots"] = [{"id": "head_top", "bone": "Head"}]
            cp = os.path.join(d, "cat.json")
            with open(cp, "w", encoding="utf-8") as f:
                json.dump(cat, f)
            pf = os.path.join(d, "s.prefab")
            with open(pf, "w", encoding="utf-8") as f:
                f.write(skin_prefab())
            self.assertEqual(sv.main(["catalog", cp]), 0)
            self.assertEqual(sv.main(["prefab", pf, "--catalog", cp, "--rig", "humanoid", "--role", "bot"]), 0)
            bad = os.path.join(d, "b.prefab")
            with open(bad, "w", encoding="utf-8") as f:
                f.write(skin_prefab(materials=3))
            self.assertEqual(sv.main(["prefab", bad, "--catalog", cp, "--rig", "humanoid", "--role", "bot"]), 1)


if __name__ == "__main__":
    unittest.main()
