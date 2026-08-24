"""Evaluator for TaskType.ShortNav (type 0, SN task IDs)."""

from __future__ import annotations

from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from .prompt import SYSTEM_PROMPT


class ShortNavEvaluator(BaseNavEvaluator):
    """Evaluate short-range point-to-point navigation within visual range."""

    task_type = 0
    task_name = "ShortNav"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_instructions(self) -> str:
        return (
            "[Short Navigation Task]\n"
            f"Start: {format_geo_point(self.task['startPoint'])}\n"
            f"Goal:  {format_geo_point(self.task['endPoint'])}\n\n"
            "The start and end points are within visual range, so navigating purely by "
            "observation is usually fastest, but you may inspect the map if you find it "
            "helpful. No computed route is available."
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
            "used_map": map_steps > 0,
        }
