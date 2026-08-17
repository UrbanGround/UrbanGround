"""Evaluator for TaskType.SpatialQA (type 9, SQ task IDs)."""

from __future__ import annotations

from typing import Any

from ..base import BaseTaskEvaluator
from .prompt import SYSTEM_PROMPT


class SpatialQAEvaluator(BaseTaskEvaluator):
    """Evaluate questions that require active visual exploration of the nearby area."""

    task_type = 9
    task_name = "SpatialQA"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        movement_steps = sum(
            record["action"].get("action") in {"move", "sprint"}
            for record in self.records
        )
        inspection_steps = sum(
            record["action"].get("action") in {"look", "map_orbit"}
            for record in self.records
        )
        map_steps = sum(
            record["action"].get("action") in {
                "open_map", "map_select", "map_pan", "map_zoom", "map_orbit", "close_map"
            }
            for record in self.records
        )
        evidence_terms = (
            "sign", "street", "road", "shop", "store", "school", "station",
            "building", "facility", "name", "text", "logo", "entrance",
        )
        evidence_steps = sum(
            any(term in record["observation"].lower() for term in evidence_terms)
            for record in self.records
        )
        total = len(self.records)
        return {
            "active_search_movement_step_count": movement_steps,
            "active_search_inspection_step_count": inspection_steps,
            "active_search_map_step_count": map_steps,
            "active_search_evidence_step_count": evidence_steps,
            "active_search_evidence_step_ratio": round(evidence_steps / total, 4) if total else 0.0,
            "performed_active_displacement": movement_steps > 0,
        }
