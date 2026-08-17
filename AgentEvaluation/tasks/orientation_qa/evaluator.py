"""Evaluator for TaskType.OrientationQA (type 8)."""

from __future__ import annotations

from typing import Any

from ..base import BaseTaskEvaluator
from .prompt import SYSTEM_PROMPT


def angular_distance(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


class OrientationQAEvaluator(BaseTaskEvaluator):
    task_type = 8
    task_name = "OrientationQA"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        start_yaw = float(self.task["qaStartPoint"].get("yaw", 0.0))
        yaw_values = [float(record.get("state_after", {}).get("yaw", start_yaw)) for record in self.records]
        max_deviation = max((angular_distance(yaw, start_yaw) for yaw in yaw_values), default=0.0)
        look_steps = sum(record["action"].get("action") in {"look", "map_orbit"} for record in self.records)
        displacement_steps = sum(record["action"].get("action") in {"move", "sprint"} for record in self.records)
        return {
            "initial_reference_yaw_degrees": round(start_yaw, 3),
            "maximum_yaw_deviation_degrees": round(max_deviation, 3),
            "orientation_inspection_step_count": look_steps,
            "movement_step_count": displacement_steps,
        }
