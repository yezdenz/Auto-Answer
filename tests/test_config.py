import unittest
from pathlib import Path
import tempfile
import json
import sys
from pydantic import ValidationError

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.config import AppConfig, BoundingBox


class TestConfig(unittest.TestCase):
    def test_privacy_and_clicker_defaults_are_safe(self):
        cfg = AppConfig()
        self.assertFalse(cfg.save_debug_screenshots)
        self.assertFalse(cfg.clicker.enabled)
        self.assertTrue(cfg.clicker.dry_run)
        self.assertGreaterEqual(cfg.clicker.min_confidence, 0.9)
        self.assertEqual(cfg.scan_mode, "next_page")
        self.assertEqual(cfg.reference_pdf_paths, [])

    def test_invalid_bounds_and_security_values_are_rejected(self):
        with self.assertRaises(ValidationError):
            BoundingBox(width=0, height=100)
        with self.assertRaises(ValidationError):
            AppConfig(hud_opacity=2.0)
        with self.assertRaises(ValidationError):
            AppConfig(clicker={"min_confidence": -0.1})
        with self.assertRaises(ValidationError):
            AppConfig(scan_mode="unknown")

    def test_bounding_box_properties(self):
        bbox = BoundingBox(left=100, top=150, width=500, height=400)
        self.assertEqual(bbox.right, 600)
        self.assertEqual(bbox.bottom, 550)
        self.assertEqual(bbox.to_tuple(), (100, 150, 500, 400))
        self.assertEqual(bbox.to_ltrb(), (100, 150, 600, 550))

    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "test_config.json"
            cfg = AppConfig(
                scan_region=BoundingBox(left=50, top=60, width=400, height=300),
                model="gemini-2.5-flash",
                auto_mode_interval_sec=3.5,
            )
            cfg.save(cfg_file)

            loaded = AppConfig.load(cfg_file)
            self.assertEqual(loaded.scan_region.left, 50)
            self.assertEqual(loaded.scan_region.top, 60)
            self.assertEqual(loaded.scan_region.width, 400)
            self.assertEqual(loaded.scan_region.height, 300)
            self.assertIn("flash", loaded.model)
            self.assertEqual(loaded.auto_mode_interval_sec, 3.5)
            raw = json.loads(cfg_file.read_text(encoding="utf-8"))
            self.assertNotIn("gemini_api_key", raw)


if __name__ == "__main__":
    unittest.main()
