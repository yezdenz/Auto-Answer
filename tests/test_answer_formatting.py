import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.ai.solver import AnswerResult, QuestionOption
from auto_answer.ui.formatting import format_selected_answers, selected_answer_lines


class TestAnswerFormatting(unittest.TestCase):
    def test_multiple_answers_render_one_labeled_line_each(self):
        result = AnswerResult(
            question_type="multi_select",
            options=[
                QuestionOption(index=0, label="A", text="Answer 1", is_correct=True),
                QuestionOption(index=1, label="B", text="Distractor"),
                QuestionOption(index=2, label="C", text="Answer 3", is_correct=True),
            ],
            correct_option_indices=[0, 2],
            correct_option_labels="A, C",
            correct_answer_text="Answer 1; Answer 3",
        )
        self.assertEqual(selected_answer_lines(result), ["A. Answer 1", "C. Answer 3"])
        self.assertEqual(format_selected_answers(result), "A. Answer 1\nC. Answer 3")

    def test_single_answer_uses_same_format(self):
        result = AnswerResult(
            options=[QuestionOption(index=0, label="A", text="Answer 1")],
            correct_option_indices=[0],
            correct_option_labels="A",
        )
        self.assertEqual(format_selected_answers(result), "A. Answer 1")


if __name__ == "__main__":
    unittest.main()
