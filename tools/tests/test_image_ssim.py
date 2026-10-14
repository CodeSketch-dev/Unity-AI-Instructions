import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-visual-qa", "scripts"))
sys.path.insert(0, HERE)

import image_diff as idf  # noqa: E402
from test_image_diff import solid, paint  # noqa: E402


def noise(w, h, seed):
    out, v = [], seed
    for _ in range(h):
        row = []
        for _ in range(w):
            v = (v * 1103515245 + 12345) & 0x7FFFFFFF
            g = (v >> 8) & 255
            row.append((g, g, g))
        out.append(row)
    return out


class SsimTests(unittest.TestCase):
    def test_identical_is_one(self):
        a = noise(64, 64, 1)
        self.assertAlmostEqual(idf.ssim(a, a), 1.0, places=6)

    def test_flat_identical_is_one(self):
        self.assertAlmostEqual(idf.ssim(solid(32, 32), solid(32, 32)), 1.0, places=6)

    def test_unrelated_noise_is_low(self):
        self.assertLess(idf.ssim(noise(64, 64, 1), noise(64, 64, 2)), 0.3)

    def test_small_change_stays_high(self):
        a = solid(64, 64, (200, 200, 200))
        b = paint(solid(64, 64, (200, 200, 200)), 0, 0, 4, 4, (0, 0, 0))
        self.assertGreater(idf.ssim(a, b), 0.95)

    def test_mask_ignores_region(self):
        a = solid(64, 64)
        b = paint(solid(64, 64), 0, 0, 32, 32, (0, 0, 0))
        self.assertLess(idf.ssim(a, b), 0.9)
        self.assertAlmostEqual(idf.ssim(a, b, masks=[(0, 0, 32, 32)]), 1.0, places=6)

    def test_verdict_uses_ssim_for_mockup(self):
        self.assertEqual(idf.verdict(1.0, "mockup", ssim=0.99), "PASS")
        self.assertEqual(idf.verdict(1.0, "mockup", ssim=0.95), "WARN")
        self.assertEqual(idf.verdict(1.0, "mockup", ssim=0.5), "FAIL")
        self.assertEqual(idf.verdict(0.1, "golden", ssim=0.5), "PASS")  # golden uses pixel % only


if __name__ == "__main__":
    unittest.main()
