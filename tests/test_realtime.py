import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.ai.solver import AnswerResult
from auto_answer.config import AppConfig
from auto_answer.realtime import RealtimeScanner


class TestRealtimeScanner(unittest.TestCase):
    def test_precaptured_frame_is_reused_without_capture_or_sound(self):
        config = AppConfig(save_debug_screenshots=False)
        solver = Mock()
        solver.solve_image.return_value = AnswerResult(is_valid_question=False)
        scanner = RealtimeScanner(config, solver, Mock())
        frame = Image.new("RGB", (30, 20), "white")

        with patch("auto_answer.realtime.capture_screen_region") as capture, patch(
            "auto_answer.realtime.display_answer_terminal"
        ):
            result = scanner.trigger_scan("test", captured_image=frame)

        capture.assert_not_called()
        solver.solve_image.assert_called_once_with(frame)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
