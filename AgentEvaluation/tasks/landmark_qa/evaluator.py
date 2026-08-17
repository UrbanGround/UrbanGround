"""Evaluator for TaskType.LandmarkQA (type 7)."""

from __future__ import annotations

from typing import Any

from ..base import BaseTaskEvaluator
from .prompt import SYSTEM_PROMPT


class LandmarkQAEvaluator(BaseTaskEvaluator):
    task_type = 7
    task_name = "LandmarkQA"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        observations = " ".join(record["observation"] for record in self.records).lower()
        evidence_terms = ("sign", "building", "shop", "store", "logo", "text", "color", "facility", "object")
        evidence_steps = sum(
            any(term in record["observation"].lower() for term in evidence_terms)
            for record in self.records
        )
        return {
            "landmark_evidence_step_count": evidence_steps,
            "landmark_evidence_step_ratio": round(evidence_steps / len(self.records), 4) if self.records else 0.0,
            "mentioned_visible_landmark_evidence": any(term in observations for term in evidence_terms),
        }
