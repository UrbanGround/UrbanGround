"""Evaluator for TaskType.ConstrainedNav (type 11, CN task IDs).

The agent is told about every road closure ("restrictedZones") up front, before it takes its
first step, and must reach the destination without ever crossing one of the closure lines.
Crossing a closure at any point during the episode is an immediate, unconditional failure --
see `BaseNavEvaluator.run` for the shared crossing-detection/early-stop machinery.
"""

from __future__ import annotations

from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from ..geo import describe_closures
from .prompt import SYSTEM_PROMPT


class ConstrainedNavEvaluator(BaseNavEvaluator):
    """Evaluate navigation that must avoid one or more disclosed road closures throughout."""

    task_type = 11
    task_name = "ConstrainedNav"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_instructions(self) -> str:
        return (
            "[Constrained Navigation Task]\n"
            f"Start: {format_geo_point(self.task['startPoint'])}\n"
            f"Goal:  {format_geo_point(self.task['endPoint'])}\n\n"
            f"{self.task.get('description', '').strip()}\n\n"
            "Road closures in effect for the entire task (never cross any of these lines):\n"
            f"{describe_closures(self.task.get('restrictedZones'))}\n\n"
            "Open the map before setting off to see these closures relative to your position "
            "and the destination, and plan a route around them from the very first step."
        )

    def _closure_check_active(self, elapsed_seconds: float) -> bool:
        # Disclosed from the start: the restriction is active immediately, from step 1.
        return True

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
