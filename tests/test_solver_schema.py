import unittest
from pathlib import Path
import sys

# Ensure src in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auto_answer.ai.solver import AnswerResult, QuestionOption


class TestSolverSchema(unittest.TestCase):
    def test_answer_result_model(self):
        result = AnswerResult(
            is_valid_question=True,
            question_text="What is the meaning of the term flow as it relates to the OAuth 2.0 authorization framework?",
            options=[
                QuestionOption(label="A", text="It is a process for an API user to obtain an access token from the authorization server."),
                QuestionOption(label="B", text="It is the sequence of data exchanged between a REST API request and a response."),
                QuestionOption(label="C", text="It is a process for an API request to send authentication credentials to a web service."),
                QuestionOption(label="D", text="It is the number of requests contained in the token bucket.")
            ],
            correct_option_label="A",
            correct_answer_text="It is a process for an API user to obtain an access token from the authorization server.",
            confidence=0.99,
            explanation="OAuth 2.0 defines flows (like Authorization Code flow) specifically to authorize clients and obtain access tokens."
        )

        self.assertTrue(result.is_valid_question)
        self.assertEqual(len(result.options), 4)
        self.assertEqual(result.correct_option_label, "A")
        self.assertIn("OAuth 2.0", result.explanation)


if __name__ == "__main__":
    unittest.main()
