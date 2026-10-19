import json
import os
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
import sys
sys.path.insert(0, os.path.join(ROOT, "skills", "game-orchestrator", "scripts"))
import evidence_index  # noqa: E402


class EvidenceIndexTests(unittest.TestCase):
    def test_indexes_paths_without_loading_image_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, "captures"))
            open(os.path.join(directory, "00-index.md"), "w", encoding="utf-8").write("x")
            open(os.path.join(directory, "captures", "map.png"), "wb").write(b"not decoded")
            data = evidence_index.build(directory)
            self.assertEqual(data["image_count"], 1)
            self.assertEqual(data["images"], ["captures/map.png"])

    def test_missing_images_are_explicit_unknowns(self):
        with tempfile.TemporaryDirectory() as directory:
            data = evidence_index.build(directory)
            self.assertTrue(data["unknowns"])
            self.assertTrue(evidence_index.validate_for_mapspec(data, require_images=True))

    def test_valid_image_index_unblocks_mapspec_preflight(self):
        data = {"schema": 1, "files": ["captures/map.png"], "images": ["captures/map.png"]}
        self.assertEqual(evidence_index.validate_for_mapspec(data, require_images=True), [])

    def test_mapspec_artifact_requires_contract_and_evidence(self):
        self.assertTrue(evidence_index.validate_mapspec_artifact({"schema": 1}))
        spec = {key: {} for key in ("source", "materials", "surfaces", "parts", "chunks", "camera")}
        spec.update({"schema": 1, "evidence": ["captures/map.png"]})
        self.assertEqual(evidence_index.validate_mapspec_artifact(spec), [])

    def test_write_is_json_and_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            out = os.path.join(directory, "generated", "evidence.json")
            evidence_index.write(directory, out)
            with open(out, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream)["schema"], 1)
            self.assertFalse(os.path.exists(out + ".tmp"))

    def test_cli_can_enforce_reference_images(self):
        with tempfile.TemporaryDirectory() as directory:
            out = os.path.join(directory, "generated", "evidence.json")
            self.assertEqual(evidence_index.main([directory, "--out", out, "--require-images"]), 1)
