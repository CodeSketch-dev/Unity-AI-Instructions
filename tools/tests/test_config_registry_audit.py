import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "config-and-factory-authoring", "scripts"))

import config_registry_audit as audit  # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def asset(root, rel, guid, body=""):
    write(root, rel, "%YAML 1.1\nMonoBehaviour:\n" + body)
    write(root, rel + ".meta", "fileFormatVersion: 2\nguid: %s\n" % guid)


def codes(findings):
    return sorted(f.code for f in findings)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = self.t.name
        self.cfg = "Assets/_Game/Configs/Character/"
        self.sing = "Assets/_Game/Resources/CodeSketch/ScriptableObjectSingletons/Game.Factory_Character.asset"

    def tearDown(self):
        self.t.cleanup()

    def test_registered_asset_ok(self):
        asset(self.r, self.cfg + "A.asset", "a" * 32, "  _skinName: A\n")
        asset(self.r, self.sing, "f" * 32, "  _skins:\n  - {fileID: 11400000, guid: %s, type: 2}\n" % ("a" * 32))
        self.assertEqual(codes(audit.audit(self.r)), [])

    def test_unregistered_asset(self):
        asset(self.r, self.cfg + "A.asset", "a" * 32, "  _skinName: A\n")
        asset(self.r, self.sing, "f" * 32, "  _skins: []\n")
        self.assertEqual(codes(audit.audit(self.r)), ["unregistered-config"])

    def test_duplicate_ids(self):
        asset(self.r, self.cfg + "A.asset", "a" * 32, "  _skinName: Same\n")
        asset(self.r, self.cfg + "B.asset", "b" * 32, "  _skinName: Same\n")
        asset(self.r, self.sing, "f" * 32,
              "  _skins:\n  - {fileID: 1, guid: %s}\n  - {fileID: 1, guid: %s}\n" % ("a" * 32, "b" * 32))
        self.assertEqual(codes(audit.audit(self.r)), ["duplicate-id"])

    def test_null_prefab_and_sprite(self):
        asset(self.r, self.cfg + "A.asset", "a" * 32,
              "  _skinName: A\n  _referencePrefab: {fileID: 0}\n  _thumbnail: {fileID: 0}\n  _other: {fileID: 0}\n")
        asset(self.r, self.sing, "f" * 32, "  _skins:\n  - {fileID: 1, guid: %s}\n" % ("a" * 32))
        c = codes(audit.audit(self.r))
        self.assertEqual(c, ["null-ref", "null-ref"])

    def test_pool_prewarm_exceeds_max(self):
        asset(self.r, "Assets/_Game/Configs/Pool/Pool_Fx_Hit.asset", "c" * 32,
              "  _poolPrewarm: 60\n  _poolCapacity: 50\n  _poolCapacityMax: 50\n")
        asset(self.r, self.sing, "f" * 32, "  _pools:\n  - {fileID: 1, guid: %s}\n" % ("c" * 32))
        self.assertEqual(codes(audit.audit(self.r)), ["pool-prewarm-over-max"])

    def test_audio_folder_skipped_for_registration(self):
        asset(self.r, "Assets/_Game/Configs/Audio/Sfx_Hit.asset", "d" * 32, "  _volume: 1\n")
        self.assertEqual(codes(audit.audit(self.r)), [])

    def test_main_exit_codes(self):
        asset(self.r, self.cfg + "A.asset", "a" * 32, "  _skinName: A\n")
        asset(self.r, self.sing, "f" * 32, "  _skins: []\n")
        self.assertEqual(audit.main([self.r]), 1)
        self.assertEqual(audit.main(["--no-fail", self.r]), 0)

    def test_unity_boilerplate_and_root_files_ignored(self):
        asset(self.r, "Assets/_Game/Configs/Loose.asset", "e" * 32,
              "  m_PrefabAsset: {fileID: 0}\n  m_PrefabInstance: {fileID: 0}\n")
        self.assertEqual(codes(audit.audit(self.r)), [])

    def test_no_configs_folder(self):
        os.makedirs(os.path.join(self.r, "Assets"))
        self.assertEqual(audit.audit(self.r), [])


if __name__ == "__main__":
    unittest.main()
