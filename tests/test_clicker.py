import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.ai.solver import AnswerResult, QuestionOption
from auto_answer.automation.clicker import AutoClicker
from auto_answer.config import BoundingBox, ClickerConfig


class TestClickerSafety(unittest.TestCase):
    def setUp(self):
        self.region = BoundingBox(left=100, top=100, width=500, height=500)
        self.option = QuestionOption(index=0, label="A", text="Answer", is_correct=True)

    def test_blocks_low_confidence_and_multi_select(self):
        clicker = AutoClicker(ClickerConfig(enabled=True, dry_run=False, delay_sec=0))
        low = AnswerResult(options=[self.option], correct_option_indices=[0], confidence=0.5)
        with patch.object(clicker, "click_at") as click:
            self.assertFalse(clicker.click_option(self.region, low))
            click.assert_not_called()

        multi = AnswerResult(
            question_type="multi_select",
            options=[self.option, QuestionOption(index=1, label="B", text="Also")],
            correct_option_indices=[0, 1],
            confidence=0.99,
        )
        with patch.object(clicker, "click_at") as click:
            self.assertFalse(clicker.click_option(self.region, multi))
            click.assert_not_called()

    def test_dry_run_never_moves_mouse(self):
        clicker = AutoClicker(ClickerConfig(enabled=True, dry_run=True))
        result = AnswerResult(options=[self.option], correct_option_indices=[0], confidence=0.99)
        with patch.object(clicker, "click_at") as click:
            self.assertTrue(clicker.click_option(self.region, result))
            click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
