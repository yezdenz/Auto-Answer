"""
Gemini Multimodal Vision Solver.
Sends screen images directly to Gemini's vision models to extract questions,
read options, determine the correct answer, and provide explanations.
"""

from __future__ import annotations
import io
import json
import os
import sys
import warnings
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageOps, ImageEnhance
from pydantic import BaseModel, Field

# Filter SDK deprecation warnings for cleaner console output
warnings.filterwarnings("ignore", category=UserWarning)

from .prompts import SOLVER_SYSTEM_INSTRUCTION, SOLVER_USER_PROMPT


class QuestionOption(BaseModel):
    index: int = Field(default=0, description="0-based physical position from top to bottom (0 for 1st choice, 1 for 2nd...)")
    label: str = Field(default="A", description="Option label, e.g. A, B, C, D or 1, 2, 3, 4")
    text: str = Field(default="", description="The full text of the option choice")
    is_correct: bool = Field(default=False, description="True if this option is correct, False otherwise")
    reasoning: str = Field(default="", description="Why this option is correct or eliminated as a distractor")


class AnswerResult(BaseModel):
    is_valid_question: bool = Field(
        default=True,
        description="True if the image contains an academic or quiz question, False otherwise"
    )
    question_type: str = Field(
        default="multiple_choice",
        description="multiple_choice, multi_select, true_false, fill_in_blank, or short_answer"
    )
    question_text: str = Field(
        default="",
        description="The verbatim question statement extracted from the image"
    )
    is_negative_question: bool = Field(
        default=False,
        description="True if question contains NOT, FALSE, EXCEPT, or LEAST"
    )
    options: List[QuestionOption] = Field(
        default_factory=list,
        description="List of detected answer choices with individual evaluations"
    )
    correct_option_indices: List[int] = Field(
        default_factory=list,
        description="List of 0-based indices of the winning options, e.g. [0]"
    )
    correct_option_labels: str = Field(
        default="",
        description="The letter or label of the correct choice(s) (e.g., 'A' or 'A, C')"
    )
    correct_answer_text: str = Field(
        default="",
        description="The full text of the correct answer"
    )
    click_instruction: str = Field(
        default="",
        description="Direct instruction on which physical UI element to click on screen"
    )
    confidence: float = Field(
        default=0.95,
        description="Confidence level between 0.0 and 1.0"
    )
    explanation: str = Field(
        default="",
        description="Concise 1-2 sentence explanation justifying why this answer is correct"
    )


def prompt_for_api_key() -> Optional[str]:
    """Prompts the user for their Gemini API key via GUI or terminal and saves it to .env."""
    key = None

    try:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        key = simpledialog.askstring(
            "Gemini API Key Required",
            "Enter your Google Gemini API Key:\n(Get one free at https://aistudio.google.com/app/apikey)",
            parent=root
        )
        root.destroy()
    except Exception:
        pass

    if not key and sys.stdin and sys.stdin.isatty():
        print("\n" + "=" * 60)
        print("🔑 GEMINI API KEY REQUIRED")
        print("Get your free API key at: https://aistudio.google.com/app/apikey")
        print("=" * 60)
        try:
            key = input("Paste your Gemini API Key here (or press Enter to cancel): ").strip()
        except Exception:
            pass

    if key and key.strip():
        key = key.strip()
        env_file = Path(".env")
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"\nGEMINI_API_KEY={key}\n")
        os.environ["GEMINI_API_KEY"] = key
        print(f"[✓] Saved GEMINI_API_KEY to {env_file.resolve()}")
        return key

    return None


class GeminiQuestionSolver:
    """Solves quiz and exam questions using Gemini multimodal API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.5-flash-lite", demo_mode: bool = False):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.demo_mode = demo_mode
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                self.api_key = prompt_for_api_key()

            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set!\n"
                    "1. Get a free API key at: https://aistudio.google.com/app/apikey\n"
                    "2. Add it to a .env file: GEMINI_API_KEY=your_key_here\n"
                    "3. Or pass it when prompted."
                )

            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Optimizes image clarity, contrast, and sharpness for vision reasoning."""
        img = image.convert("RGB")
        w, h = img.size

        # Scale up small captures so text and radio buttons are sharp
        if w < 1200:
            scale = 1200 / w
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        # Autocontrast to normalize text vs background
        try:
            img = ImageOps.autocontrast(img, cutoff=1)
        except Exception:
            pass

        # Enhance sharpness
        try:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.25)
        except Exception:
            pass

        return img

    def solve_image(self, image: Image.Image) -> AnswerResult:
        """
        Sends the PIL Image to Gemini Vision and returns structured AnswerResult.
        """
        if self.demo_mode:
            import time
            time.sleep(0.5)
            return AnswerResult(
                is_valid_question=True,
                question_type="multiple_choice",
                question_text="What is the meaning of the term flow as it relates to the OAuth 2.0 authorization framework?",
                is_negative_question=False,
                options=[
                    QuestionOption(
                        index=0, label="A",
                        text="It is a process for an API user to obtain an access token from the authorization server.",
                        is_correct=True,
                        reasoning="In OAuth 2.0 (RFC 6749), an authorization 'flow' defines the protocol interactions used to acquire access tokens."
                    ),
                    QuestionOption(
                        index=1, label="B",
                        text="It is the sequence of data exchanged between a REST API request and a response.",
                        is_correct=False,
                        reasoning="This describes general HTTP request/response exchange, not an OAuth authorization flow."
                    ),
                    QuestionOption(
                        index=2, label="C",
                        text="It is a process for an API request to send authentication credentials to a web service.",
                        is_correct=False,
                        reasoning="This refers to basic credential delivery, not OAuth authorization flows."
                    ),
                    QuestionOption(
                        index=3, label="D",
                        text="It is the number of requests contained in the token bucket.",
                        is_correct=False,
                        reasoning="Token bucket is a rate limiting algorithm, unrelated to OAuth authorization."
                    )
                ],
                correct_option_indices=[0],
                correct_option_labels="A",
                correct_answer_text="It is a process for an API user to obtain an access token from the authorization server.",
                click_instruction="Click the 1st radio button from the top",
                confidence=1.0,
                explanation="In OAuth 2.0 (RFC 6749), an authorization 'flow' specifies the exact procedure used by an application to secure an access token from the authorization server."
            )

        from google.genai import types

        # Preprocess frame
        processed_img = self.preprocess_image(image)

        # Convert PIL image to PNG bytes
        buffer = io.BytesIO()
        processed_img.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()

        image_part = types.Part.from_bytes(data=png_bytes, mime_type="image/png")

        config = types.GenerateContentConfig(
            system_instruction=SOLVER_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=AnswerResult,
            temperature=0.0,
        )

        candidate_models = [self.model]
        for fallback in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for model_name in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=[image_part, SOLVER_USER_PROMPT],
                    config=config,
                )

                if hasattr(response, "parsed") and response.parsed:
                    if isinstance(response.parsed, AnswerResult):
                        return response.parsed
                    elif isinstance(response.parsed, dict):
                        return AnswerResult(**response.parsed)

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

            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str or "404" in err_str:
                    last_error = e
                    continue
                raise e

        if last_error:
            raise last_error

        raise RuntimeError("No valid response received from Gemini API.")
