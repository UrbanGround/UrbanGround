"""Evaluator for TaskType.LongNav (type 2, LN task IDs)."""

from __future__ import annotations

from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from .prompt import SYSTEM_PROMPT


class LongNavEvaluator(BaseNavEvaluator):
    """Evaluate long-range navigation from first-person and map observations."""

    task_type = 2
    task_name = "LongNav"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_instructions(self) -> str:
        return (
            "[Long-Range Navigation Task]\n"
            f"Start: {format_geo_point(self.task['startPoint'])}\n"
            f"Goal:  {format_geo_point(self.task['endPoint'])}\n\n"
            "The destination is far away. Use first-person observations and the interactive "
            "map to determine and execute a route. No computed or highlighted route is available."
        )

    def task_specific_metrics(self) -> dict[str, Any]:
        navigate_calls = sum(record["action"].get("action") == "navigate" for record in self.records)
        map_steps = sum(
            record["action"].get("action") in {
                "open_map", "map_select", "map_pan", "map_zoom", "map_orbit",
                "navigate", "clear_route", "close_map",
            }
            for record in self.records
        )
        return {
            "navigate_call_count": navigate_calls,
            "used_navigation_api": navigate_calls > 0,
            "map_usage_step_count": map_steps,
        }
