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
    def test_settled_frame_skips_transient_changes_but_solves_new_content(self):
        for mode in ("scroll", "next_page"):
            for returns_to_original in (True, False):
                with self.subTest(mode=mode, returns_to_original=returns_to_original):
                    original = Image.new("RGB", (64, 64), "white")
                    changed = Image.new("RGB", (64, 64), "black")
                    settled = original if returns_to_original else changed
                    solver = Mock()
                    solver.solve_image.return_value = AnswerResult(is_valid_question=False)
                    scanner = RealtimeScanner(AppConfig(scan_mode=mode), solver, Mock())
                    with patch("auto_answer.realtime.GlobalHotkeyListener"), patch(
                        "auto_answer.realtime.console"
                    ), patch("auto_answer.realtime.display_answer_terminal"), patch(
                        "auto_answer.realtime.capture_screen_region",
                        side_effect=[original, changed, settled],
                    ), patch.object(scanner._stop_event, "wait", side_effect=[False, False, True]):
                        scanner.start()
                    self.assertEqual(solver.solve_image.call_count, 1 if returns_to_original else 2)
                    if not returns_to_original:
                        self.assertIs(solver.solve_image.call_args.args[0], settled)

    def test_stop_during_settle_prevents_extra_capture_and_request(self):
        solver = Mock()
        solver.solve_image.return_value = AnswerResult(is_valid_question=False)
        scanner = RealtimeScanner(AppConfig(), solver, Mock())
        frames = [Image.new("RGB", (64, 64), color) for color in ("white", "black")]
        with patch("auto_answer.realtime.GlobalHotkeyListener"), patch(
            "auto_answer.realtime.console"
        ), patch("auto_answer.realtime.display_answer_terminal"), patch(
            "auto_answer.realtime.capture_screen_region", side_effect=frames
        ) as capture, patch.object(scanner._stop_event, "wait", side_effect=[False, True]):
            scanner.start()
        self.assertEqual(capture.call_count, 2)
        solver.solve_image.assert_called_once()
        self.assertTrue(scanner._stop_event.is_set())

    def test_scan_mode_switch_resets_detector(self):
        config = AppConfig()
        scanner = RealtimeScanner(config, Mock(), Mock())
        scanner.detector.update_reference(Image.new("RGB", (10, 10), "white"))

        scanner.set_scan_mode("scroll")

        self.assertEqual(config.scan_mode, "scroll")
        self.assertIsNone(scanner.detector._last_thumbnail)

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
