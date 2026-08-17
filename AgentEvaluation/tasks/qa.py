"""Shared parsing and scoring helpers for multiple-choice QA tasks."""

from __future__ import annotations

import re
from typing import Any

LETTERS = "ABCD"


def option_texts(task: dict[str, Any]) -> list[str]:
    options = task.get("qaOptions")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("QA task must contain exactly four qaOptions")
    texts = [str(option.get("text", "")).strip() for option in options]
    if any(not text for text in texts):
        raise ValueError("Every QA option must contain non-empty text")
    return texts


def correct_letter(task: dict[str, Any]) -> str:
    index = task.get("qaAnswerIndex")
    if not isinstance(index, int) or not 0 <= index < 4:
        raise ValueError("qaAnswerIndex must be an integer from 0 to 3")
    return LETTERS[index]


def format_question(task: dict[str, Any]) -> str:
    lines = [str(task.get("description", "")).strip()]
    lines.extend(f"{letter}. {text}" for letter, text in zip(LETTERS, option_texts(task)))
    return "\n".join(lines)


def parse_answer_letter(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    exact = re.fullmatch(r"(?:OPTION\s*)?([A-D])", text)
    return exact.group(1) if exact else None


def score_answer(task: dict[str, Any], answer: str | None) -> dict[str, Any]:
    expected = correct_letter(task)
    return {
        "answer": answer,
        "correct_answer": expected,
        "answer_valid": answer in LETTERS,
        "answer_correct": answer == expected,
    }
