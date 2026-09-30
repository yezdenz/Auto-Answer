"""Presentation helpers shared by the terminal and floating HUD."""

from __future__ import annotations

import re

from ..ai.solver import AnswerResult


def selected_answer_lines(result: AnswerResult) -> list[str]:
    """Return selected answers as stable, human-readable ``A. text`` lines."""
    selected_indices = set(result.correct_option_indices)
    selected_labels = {
        label.strip().upper()
        for label in re.split(r"[,;/]", result.correct_option_labels)
        if label.strip()
    }

    selected = [
        option
        for option in sorted(result.options, key=lambda item: item.index)
        if option.index in selected_indices
        or option.is_correct
        or option.label.strip().upper() in selected_labels
    ]
    if selected:
        return [f"{option.label}. {option.text}" for option in selected]

    if result.correct_answer_text:
        label = result.correct_option_labels.strip()
        return [f"{label}. {result.correct_answer_text}" if label else result.correct_answer_text]
    return []


def format_selected_answers(result: AnswerResult) -> str:
    """Format one or several selected answers on separate lines."""
    return "\n".join(selected_answer_lines(result))
