import unittest
from pathlib import Path
import sys

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.config import BoundingBox
from auto_answer.capture.screen import capture_screen_region, get_virtual_screen_geometry


class TestCapture(unittest.TestCase):
    def test_virtual_screen_geometry(self):
        left, top, width, height = get_virtual_screen_geometry()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_capture_small_region(self):
        box = BoundingBox(left=0, top=0, width=100, height=80)
        img = capture_screen_region(box)
        self.assertEqual(img.size, (100, 80))
        self.assertEqual(img.mode, "RGB")


if __name__ == "__main__":
    unittest.main()
