import unittest
from pathlib import Path
import sys
from PIL import Image

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.capture.detector import ScreenChangeDetector


class TestDetector(unittest.TestCase):
    def test_detector_initial_and_identical(self):
        detector = ScreenChangeDetector(threshold=4.0)
        img1 = Image.new("RGB", (200, 200), color="white")

        # First frame is always considered a change/baseline
        self.assertTrue(detector.has_changed(img1))

        # Identical image should return False
        self.assertFalse(detector.has_changed(img1))

    def test_detector_significant_change(self):
        detector = ScreenChangeDetector(threshold=4.0)
        img_white = Image.new("RGB", (200, 200), color="white")
        img_black = Image.new("RGB", (200, 200), color="black")

        detector.has_changed(img_white)
        # Black image has huge difference compared to white
        self.assertTrue(detector.has_changed(img_black))


if __name__ == "__main__":
    unittest.main()

