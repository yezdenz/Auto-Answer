"""
Gemini Multimodal Vision Solver.
Sends screen images directly to Gemini's vision models to extract questions,
read options, determine the correct answer, and provide explanations.
"""

from __future__ import annotations
import io
import json
import os
from typing import List, Optional
from PIL import Image
from pydantic import BaseModel, Field

from .prompts import SOLVER_SYSTEM_INSTRUCTION, SOLVER_USER_PROMPT


class QuestionOption(BaseModel):
    label: str = Field(description="Option label, e.g. A, B, C, D or 1, 2, 3, 4")
    text: str = Field(description="The full text of the option choice")


class AnswerResult(BaseModel):
    is_valid_question: bool = Field(
        default=True,
        description="True if the image contains an academic or quiz question, False otherwise"
    )
    question_text: str = Field(
        default="",
        description="The verbatim or cleaned question statement extracted from the image"
    )
    options: List[QuestionOption] = Field(
        default_factory=list,
        description="List of detected answer choices/options"
    )
    correct_option_label: str = Field(
        default="",
        description="The letter or label of the correct choice (e.g., 'A', 'B', 'C', 'D')"
    )
    correct_answer_text: str = Field(
        default="",
        description="The full text of the correct answer"
    )
    confidence: float = Field(
        default=0.95,
        description="Confidence level between 0.0 and 1.0"
    )
    explanation: str = Field(
        default="",
        description="Concise 1-2 sentence explanation justifying why this answer is correct"
    )


class GeminiQuestionSolver:
    """Solves quiz and exam questions using Gemini multimodal API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", demo_mode: bool = False):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.demo_mode = demo_mode
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set! Please set it in your .env file or environment variable.\n"
                    "Get a key for free at https://aistudio.google.com/app/apikey\n"
                    "(Tip: You can run with --demo to test the UI and sample answer without an API key!)"
                )
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def solve_image(self, image: Image.Image) -> AnswerResult:
        """
        Sends the PIL Image to Gemini Vision and returns structured AnswerResult.
        """
        if self.demo_mode:
            import time
            time.sleep(0.8) # simulate network latency
            return AnswerResult(
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
                explanation="In OAuth 2.0, an authorization 'flow' (or grant type) specifies the exact process through which a client application secures an access token from the authorization server."
            )

        from google.genai import types

        # Convert PIL image to PNG bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        image_part = types.Part.from_bytes(data=png_bytes, mime_type="image/png")

        config = types.GenerateContentConfig(
            system_instruction=SOLVER_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=AnswerResult,
            temperature=0.1,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=[image_part, SOLVER_USER_PROMPT],
            config=config,
        )

        # Parse response
        if hasattr(response, "parsed") and response.parsed:
            if isinstance(response.parsed, AnswerResult):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return AnswerResult(**response.parsed)

        # Fallback to json parsing if response.text
        if response.text:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            data = json.loads(cleaned_text.strip())
            return AnswerResult(**data)

        raise RuntimeError("No valid response received from Gemini API.")
