import unittest
from pathlib import Path
import sys
from pydantic import ValidationError

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.ai.solver import AnswerResult, QuestionOption


class TestSolverSchema(unittest.TestCase):
    def test_gemini_schema_omits_unsupported_additional_properties(self):
        """Gemini rejects Pydantic's extra='forbid' schema keyword with HTTP 400."""
        schema = AnswerResult.model_json_schema()

        def assert_compatible(value):
            if isinstance(value, dict):
                self.assertNotIn("additionalProperties", value)
                for nested in value.values():
                    assert_compatible(nested)
            elif isinstance(value, list):
                for nested in value:
                    assert_compatible(nested)

        assert_compatible(schema)

    def test_rejects_unsafe_or_inconsistent_model_output(self):
        with self.assertRaises(ValidationError):
            AnswerResult(confidence=1.5)
        with self.assertRaises(ValidationError):
            AnswerResult(
                question_type="multiple_choice",
                options=[QuestionOption(index=0, label="A", text="one")],
                correct_option_indices=[-1],
            )
        with self.assertRaises(ValidationError):
            AnswerResult(
                question_type="multiple_choice",
                options=[QuestionOption(index=0, label="A", text="one")],
                correct_option_indices=[1],
            )

    def test_answer_result_model(self):
        result = AnswerResult(
            is_valid_question=True,
            question_type="multiple_choice",
            question_text="What is the meaning of the term flow as it relates to the OAuth 2.0 authorization framework?",
            is_negative_question=False,
            options=[
                QuestionOption(index=0, label="A", text="It is a process for an API user to obtain an access token from the authorization server.", is_correct=True, reasoning="OAuth 2.0 authorization grant."),
                QuestionOption(index=1, label="B", text="It is the sequence of data exchanged between a REST API request and a response.", is_correct=False, reasoning="General HTTP."),
                QuestionOption(index=2, label="C", text="It is a process for an API request to send authentication credentials to a web service.", is_correct=False, reasoning="Basic auth."),
                QuestionOption(index=3, label="D", text="It is the number of requests contained in the token bucket.", is_correct=False, reasoning="Rate limiting.")
            ],
            correct_option_indices=[0],
            correct_option_labels="A",
            correct_answer_text="It is a process for an API user to obtain an access token from the authorization server.",
            click_instruction="Click the 1st radio button from the top",
            confidence=0.99,
            explanation="OAuth 2.0 defines flows (like Authorization Code flow) specifically to authorize clients and obtain access tokens."
        )

        self.assertTrue(result.is_valid_question)
        self.assertEqual(len(result.options), 4)
        self.assertEqual(result.correct_option_labels, "A")
        self.assertEqual(result.correct_option_indices, [0])
        self.assertIn("1st radio button", result.click_instruction)
        self.assertIn("OAuth 2.0", result.explanation)


if __name__ == "__main__":
    unittest.main()
