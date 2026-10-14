import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-visual-qa", "scripts"))

import image_diff as idf  # noqa: E402


def solid(w, h, rgb=(255, 255, 255)):
    return [[rgb] * w for _ in range(h)]


def paint(img, x0, y0, x1, y1, rgb):
    for y in range(y0, y1):
        for x in range(x0, x1):
            img[y][x] = rgb
    return img


def save(path, img):
    idf.write_png(path, img)


class PngTests(unittest.TestCase):
    def test_round_trip(self):
        img = paint(solid(7, 5), 1, 1, 4, 3, (10, 20, 30))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.png")
            save(p, img)
            w, h, px = idf.read_png(p)
        self.assertEqual((w, h), (7, 5))
        self.assertEqual(px, img)

    def test_rejects_non_png(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.png")
            open(p, "wb").write(b"nope")
            with self.assertRaises(ValueError):
                idf.read_png(p)


class DiffTests(unittest.TestCase):
    def test_identical(self):
        a = solid(64, 64)
        r = idf.diff(a, a)
        self.assertEqual(r["differing_pct"], 0.0)
        self.assertEqual(r["regions"], [])

    def test_tolerates_small_channel_noise(self):
        a = solid(32, 32, (100, 100, 100))
        b = solid(32, 32, (108, 100, 100))  # delta 8 <= 12
        self.assertEqual(idf.diff(a, b)["differing_pct"], 0.0)

    def test_detects_block_and_region(self):
        a = solid(100, 100)
        b = paint(solid(100, 100), 10, 10, 30, 20, (0, 0, 0))  # 200 px = 2%
        r = idf.diff(a, b)
        self.assertAlmostEqual(r["differing_pct"], 2.0, places=3)
        self.assertEqual(len(r["regions"]), 1)
        x0, y0, x1, y1 = r["regions"][0]["box"]
        self.assertTrue(x0 <= 10 and y0 <= 10 and x1 >= 30 and y1 >= 20)

    def test_mask_excludes_region(self):
        a = solid(100, 100)
        b = paint(solid(100, 100), 10, 10, 30, 20, (0, 0, 0))
        r = idf.diff(a, b, masks=[(0, 0, 50, 50)])
        self.assertEqual(r["differing_pct"], 0.0)

    def test_size_mismatch(self):
        with self.assertRaises(ValueError):
            idf.diff(solid(10, 10), solid(11, 10))

    def test_verdict_thresholds(self):
        self.assertEqual(idf.verdict(1.0, "mockup"), "PASS")
        self.assertEqual(idf.verdict(2.0, "mockup"), "WARN")
        self.assertEqual(idf.verdict(5.0, "mockup"), "FAIL")
        self.assertEqual(idf.verdict(0.1, "golden"), "PASS")
        self.assertEqual(idf.verdict(0.5, "golden"), "WARN")
        self.assertEqual(idf.verdict(1.5, "golden"), "FAIL")

    def test_diff_png_is_written(self):
        a = solid(40, 40)
        b = paint(solid(40, 40), 5, 5, 15, 15, (0, 0, 0))
        out = idf.overlay(a, b)
        self.assertEqual(out[5][5], (255, 0, 0))
        self.assertNotEqual(out[30][30], (255, 0, 0))


class CliTests(unittest.TestCase):
    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            ref, same, other = (os.path.join(d, n) for n in ("ref.png", "same.png", "other.png"))
            save(ref, solid(80, 80))
            save(same, solid(80, 80))
            save(other, paint(solid(80, 80), 0, 0, 40, 40, (0, 0, 0)))
            out = os.path.join(d, "diff.png")
            self.assertEqual(idf.main([ref, same]), 0)
            self.assertEqual(idf.main([ref, other, "--out", out]), 1)
            self.assertTrue(os.path.isfile(out))
            masks = os.path.join(d, "m.json")
            json.dump([[0, 0, 40, 40]], open(masks, "w"))
            self.assertEqual(idf.main([ref, other, "--mask", masks]), 0)


if __name__ == "__main__":
    unittest.main()
