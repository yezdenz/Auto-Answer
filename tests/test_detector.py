import unittest
from pathlib import Path
import sys
from PIL import Image
from PIL import ImageDraw

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.capture.detector import ScreenChangeDetector


class TestDetector(unittest.TestCase):
    @staticmethod
    def make_question_frame() -> Image.Image:
        image = Image.new("L", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        for y, width in ((7, 45), (14, 36), (28, 50), (38, 42), (49, 47)):
            draw.rectangle((5, y, 5 + width, y + 2), fill="black")
        return image.convert("RGB")

    @staticmethod
    def shift_up(image: Image.Image, amount: int) -> Image.Image:
        shifted = Image.new(image.mode, image.size, "white")
        shifted.paste(image.crop((0, amount, image.width, image.height)), (0, 0))
        return shifted

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

    def test_vertical_scroll_is_not_a_new_question(self):
        detector = ScreenChangeDetector(threshold=4.0)
        original = self.make_question_frame()
        detector.update_reference(original)

        kind, difference = detector.classify_change(self.shift_up(original, 10))

        self.assertEqual(kind, "scroll")
        self.assertLessEqual(difference, detector.scroll_match_threshold)

    def test_different_question_is_still_detected(self):
        detector = ScreenChangeDetector(threshold=4.0)
        original = self.make_question_frame()
        changed = Image.new("RGB", original.size, "black")
        detector.update_reference(original)

        kind, _ = detector.classify_change(changed)

        self.assertEqual(kind, "changed")


if __name__ == "__main__":
    unittest.main()

