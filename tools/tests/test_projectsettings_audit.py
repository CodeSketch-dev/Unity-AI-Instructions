import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "projectsettings-baseline", "scripts"))

import projectsettings_audit as audit  # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def make(root, auto_sync=0, reuse=1, time_scale=1, max_dt=0.1, vsync=0, mip=0, srp=1, hdr=0, soft=0,
         matrix="ffffffff" * 32):
    write(root, "ProjectSettings/DynamicsManager.asset",
          "  m_DefaultSolverIterations: 6\n  m_LayerCollisionMatrix: %s\n  m_AutoSyncTransforms: %d\n  m_ReuseCollisionCallbacks: %d\n"
          % (matrix, auto_sync, reuse))
    write(root, "ProjectSettings/TimeManager.asset",
          "  Maximum Allowed Timestep: %s\n  m_TimeScale: %s\n" % (max_dt, time_scale))
    write(root, "ProjectSettings/QualitySettings.asset",
          "    globalTextureMipmapLimit: %d\n    vSyncCount: %d\n" % (mip, vsync))
    write(root, "Assets/Settings/Mobile_RPAsset.asset",
          "  m_SupportsHDR: %d\n  m_UseSRPBatcher: %d\n  m_SoftShadowsSupported: %d\n"
          "  m_MainLightShadowmapResolution: 512\n  m_ShadowDistance: 40\n" % (hdr, srp, soft))


def sev(findings, level):
    return [f.code for f in findings if f.level == level]


class AuditTests(unittest.TestCase):
    def test_clean_project_has_no_fail(self):
        with tempfile.TemporaryDirectory() as r:
            make(r)
            self.assertEqual(sev(audit.audit(r), "FAIL"), [])

    def test_physics_and_time_failures(self):
        with tempfile.TemporaryDirectory() as r:
            make(r, auto_sync=1, reuse=0, time_scale=20)
            fails = sev(audit.audit(r), "FAIL")
            self.assertIn("auto-sync-transforms", fails)
            self.assertIn("reuse-collision-callbacks", fails)
            self.assertIn("time-scale", fails)

    def test_warnings(self):
        with tempfile.TemporaryDirectory() as r:
            make(r, max_dt=0.333, vsync=1, mip=1, hdr=1, soft=1)
            warns = sev(audit.audit(r), "WARN")
            for code in ("max-delta-time", "vsync", "texture-mip-limit", "urp-hdr", "urp-soft-shadows"):
                self.assertIn(code, warns)

    def test_srp_batcher_off_fails(self):
        with tempfile.TemporaryDirectory() as r:
            make(r, srp=0)
            self.assertIn("urp-srp-batcher", sev(audit.audit(r), "FAIL"))

    def test_matrix_count(self):
        # all bits set: every valid pair enabled -> 528 of 528
        self.assertEqual(audit.matrix_enabled_pairs("ffffffff" * 32), (528, 528))
        # layer 0 mask = 1 bit only, others zero
        self.assertEqual(audit.matrix_enabled_pairs("01000000" + "00000000" * 31), (1, 528))

    def test_missing_files_do_not_crash(self):
        with tempfile.TemporaryDirectory() as r:
            os.makedirs(os.path.join(r, "ProjectSettings"))
            self.assertIsInstance(audit.audit(r), list)

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as r:
            make(r)
            self.assertEqual(audit.main([r]), 0)
        with tempfile.TemporaryDirectory() as r:
            make(r, auto_sync=1)
            self.assertEqual(audit.main([r]), 1)


if __name__ == "__main__":
    unittest.main()
