"""Evaluator for environmental-condition short navigation (TSN/OCN/CLN/EVN/NTN, type 0).

These variants reuse the ShortNav payload and prompt unchanged; only the environmental
condition differs (see tasks/condition.py). The task ID prefix selects the condition and
the report's task_type name (e.g. TSN-* -> ThunderstormNav).
"""

from __future__ import annotations

from typing import Any

from ..condition import ConditionEpisodeMixin, condition_for_task
from ..short_nav import ShortNavEvaluator


class ConditionShortNavEvaluator(ConditionEpisodeMixin, ShortNavEvaluator):
    """ShortNav under a weather / time-of-day condition (prompt unchanged)."""

    task_type = 0

    def __init__(self, task, sandbox, llm, config):
        # Resolve and stash the per-prefix condition BEFORE super().__init__(), whose
        # prefix validation reads the instance's task_id_prefix.
        self._condition = condition_for_task(task, expected_suffix="N")
        prefix = str(task.get("id", "")).split("-", 1)[0].upper()
        self.task_id_prefix = f"{prefix}-"
        super().__init__(task, sandbox, llm, config)

    @property
    def task_name(self) -> str:
        return self._condition[1]

    # build_system_prompt intentionally inherited from ShortNavEvaluator unchanged.

    def task_specific_metrics(self) -> dict[str, Any]:
        return {**super().task_specific_metrics(), **self._condition_metrics()}
