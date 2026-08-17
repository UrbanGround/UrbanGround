"""Evaluator for TaskType.DynamicClosureNav (type 12, CN task IDs reused with type overridden).

Unlike ConstrainedNav, the closure is *not* disclosed up front: for the first
`CLOSURE_DISCLOSURE_DELAY_SECONDS` of the episode this behaves exactly like a plain point-to-point
navigation task (the agent has no reason to expect any obstruction, and crossing the future
closure's location during this window is not a violation). Once that delay elapses, a one-off
notice is injected into the agent's next observation announcing that the map now shows a newly
closed segment; crossing it after that point is an immediate, unconditional failure for the rest
of the episode. `closureDelayMinutes` on the task payload is intentionally unused -- the
disclosure delay is fixed at 30 seconds of episode wall-clock time per spec.
"""

from __future__ import annotations

from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from ..geo import describe_closures
from .prompt import SYSTEM_PROMPT

CLOSURE_DISCLOSURE_DELAY_SECONDS = 30.0


class DynamicClosureNavEvaluator(BaseNavEvaluator):
    """Evaluate navigation where a road closure dynamically appears partway through the episode."""

    task_type = 12
    task_name = "DynamicClosureNav"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Whether the one-off "a closure just appeared" notice has already been handed to the
        # agent. Guards against re-injecting it on every subsequent turn once elapsed_seconds
        # has crossed the delay.
        self._closure_disclosed = False

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_instructions(self) -> str:
        # Deliberately omits any mention of restrictedZones: for the first 30 seconds this task
        # must read exactly like an ordinary navigation task from the agent's point of view.
        return (
            "[Navigation Task]\n"
            f"Start: {format_geo_point(self.task['startPoint'])}\n"
            f"Goal:  {format_geo_point(self.task['endPoint'])}\n\n"
            f"{self.task.get('description', '').strip()}\n\n"
            "Navigate to the destination. There is no known obstruction right now; use "
            "whichever combination of first-person movement, turning, and map actions you "
            "find most effective."
        )

    def _pending_extra_context(self, elapsed_seconds: float) -> str | None:
        if self._closure_disclosed or elapsed_seconds < CLOSURE_DISCLOSURE_DELAY_SECONDS:
            return None
        self._closure_disclosed = True
        return (
            "NEW SYSTEM NOTICE: A road closure has just appeared on the map. The following "
            "segment(s) are now closed and must not be crossed for the remainder of this task "
            "(crossing was not a violation before this notice, but is a violation from now on):\n"
            f"{describe_closures(self.task.get('restrictedZones'))}\n\n"
            "Open the map now to see exactly where this closure is relative to your current "
            "position and the destination, and replan your route around it."
        )

    def _closure_check_active(self, elapsed_seconds: float) -> bool:
        # Only enforced once the agent has actually been notified (mirrors _closure_disclosed
        # rather than the raw elapsed time, so a slow first post-delay step can't be crossed
        # before the notice text has actually been delivered in that same step).
        return self._closure_disclosed

    def task_specific_metrics(self) -> dict[str, Any]:
        navigate_calls = sum(record["action"].get("action") == "navigate" for record in self.records)
        map_steps = sum(
            record["action"].get("action") in {
                "open_map", "map_select", "map_pan", "map_zoom", "map_orbit",
                "navigate", "clear_route", "close_map",
            }
            for record in self.records
        )
        disclosure_step = next(
            (record["step"] for record in self.records if record.get("closure_notice_injected")),
            None,
        )
        return {
            "navigate_call_count": navigate_calls,
            "used_navigation_api": navigate_calls > 0,
            "map_usage_step_count": map_steps,
            "used_map": map_steps > 0,
            "closure_disclosure_delay_seconds": CLOSURE_DISCLOSURE_DELAY_SECONDS,
            "closure_disclosed": self._closure_disclosed,
            "closure_disclosure_step": disclosure_step,
        }
