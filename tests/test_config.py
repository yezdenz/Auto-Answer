import unittest
from pathlib import Path
import tempfile
import json
import sys

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.config import AppConfig, BoundingBox


class TestConfig(unittest.TestCase):
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
            self.assertEqual(loaded.model, "gemini-2.5-flash")
            self.assertEqual(loaded.auto_mode_interval_sec, 3.5)


if __name__ == "__main__":
    unittest.main()
