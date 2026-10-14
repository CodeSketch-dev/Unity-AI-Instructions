import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "ui-visual-qa", "scripts"))
sys.path.insert(0, HERE)

import image_diff as idf  # noqa: E402
import ui_contrast as uc  # noqa: E402
from test_image_diff import solid, paint  # noqa: E402


def frame(w, h, box, fg=(255, 255, 255), bg=(0, 0, 0)):
    return paint(solid(w, h, bg), box[0], box[1], box[2], box[3], fg)


class EdgeTests(unittest.TestCase):
    def test_identical_zero(self):
        a = frame(64, 64, (10, 10, 40, 40))
        self.assertEqual(idf.edge_diff(a, a)["mismatch_pct"], 0.0)

    def test_flat_has_no_edges(self):
        r = idf.edge_diff(solid(32, 32), solid(32, 32))
        self.assertEqual(r["mismatch_pct"], 0.0)

    def test_one_pixel_shift_tolerated(self):
        a = frame(64, 64, (10, 10, 40, 40))
        b = frame(64, 64, (11, 10, 41, 40))
        self.assertLess(idf.edge_diff(a, b)["mismatch_pct"], 5.0)

    def test_big_shift_detected(self):
        a = frame(64, 64, (10, 10, 30, 30))
        b = frame(64, 64, (30, 30, 50, 50))
        self.assertGreater(idf.edge_diff(a, b)["mismatch_pct"], 50.0)

    def test_mask(self):
        a = frame(64, 64, (10, 10, 30, 30))
        b = solid(64, 64, (0, 0, 0))
        self.assertGreater(idf.edge_diff(a, b)["mismatch_pct"], 50.0)
        self.assertEqual(idf.edge_diff(a, b, masks=[(0, 0, 64, 64)])["mismatch_pct"], 0.0)

    def test_verdict_with_edges(self):
        self.assertEqual(idf.verdict(0.5, "mockup", ssim=0.99, edge=5.0), "PASS")
        self.assertEqual(idf.verdict(0.5, "mockup", ssim=0.99, edge=20.0), "WARN")
        self.assertEqual(idf.verdict(0.5, "mockup", ssim=0.99, edge=60.0), "FAIL")


class ContrastTests(unittest.TestCase):
    def test_ratio_extremes(self):
        self.assertAlmostEqual(uc.contrast_ratio(1.0, 0.0), 21.0, places=3)
        self.assertAlmostEqual(uc.contrast_ratio(0.5, 0.5), 1.0, places=3)

    def test_high_contrast_region(self):
        img = frame(100, 60, (30, 20, 70, 40))
        r = uc.region_contrast(img, (10, 10, 90, 50))
        self.assertGreater(r, 15)

    def test_low_contrast_region(self):
        img = frame(100, 60, (30, 20, 70, 40), fg=(130, 130, 130), bg=(120, 120, 120))
        self.assertLess(uc.region_contrast(img, (10, 10, 90, 50)), 3)

    def test_flat_region_is_one(self):
        self.assertAlmostEqual(uc.region_contrast(solid(50, 50, (90, 90, 90)), (0, 0, 50, 50)), 1.0, places=3)

    def test_canvas_rect_to_pixels(self):
        # canvas 200x100, image 400x200 (scale 2), canvas y up -> image y down
        self.assertEqual(uc.to_pixels([10, 20, 60, 40], (200, 100), (400, 200)), (20, 120, 120, 160))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            img = os.path.join(d, "s.png")
            idf.write_png(img, frame(200, 100, (60, 30, 140, 70), fg=(130, 130, 130), bg=(120, 120, 120)))
            texts = os.path.join(d, "t.json")
            json.dump({"canvas": [200, 100], "texts": [{"path": "A/Label", "rect": [30, 30, 170, 70], "font_size": 36}]}, open(texts, "w"))
            self.assertEqual(uc.main([img, texts]), 0)            # soft: warns but exits 0
            self.assertEqual(uc.main([img, texts, "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
