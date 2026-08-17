"""Evaluators for environmental-condition Level-1 QA (numeric types 7/8/9).

These variants reuse each source QA payload and prompt unchanged; only the environmental
condition differs (see tasks/condition.py). The task ID prefix selects the condition and
the report's task_type name (e.g. TSQ-* -> ThunderstormQA), while the numeric type keeps
LandmarkQA, OrientationQA, and SpatialQA routed to their corresponding behavior/metrics.
"""

from __future__ import annotations

from typing import Any

from ..condition import ConditionEpisodeMixin, condition_for_task
from ..landmark_qa import LandmarkQAEvaluator
from ..orientation_qa import OrientationQAEvaluator
from ..search_qa import SpatialQAEvaluator


class _ConditionQAMixin(ConditionEpisodeMixin):
    def __init__(self, task, sandbox, llm, config):
        # Resolve and stash the per-prefix condition BEFORE super().__init__(), whose
        # prefix validation reads the instance's task_id_prefix.
        self._condition = condition_for_task(task, expected_suffix="Q")
        prefix = str(task.get("id", "")).split("-", 1)[0].upper()
        self.task_id_prefix = f"{prefix}-"
        super().__init__(task, sandbox, llm, config)

    @property
    def task_name(self) -> str:
        return self._condition[1]

    # build_system_prompt intentionally inherited from LandmarkQAEvaluator unchanged.

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        return {**super().task_specific_metrics(answer), **self._condition_metrics()}


class ConditionExplorationQAEvaluator(_ConditionQAMixin, LandmarkQAEvaluator):
    """LandmarkQA under a weather / time-of-day condition (prompt unchanged)."""

    task_type = 7


class ConditionOrientationQAEvaluator(_ConditionQAMixin, OrientationQAEvaluator):
    """OrientationQA under a weather / time-of-day condition (prompt unchanged)."""

    task_type = 8


class ConditionSpatialQAEvaluator(_ConditionQAMixin, SpatialQAEvaluator):
    """SpatialQA under a weather / time-of-day condition (prompt unchanged)."""

    task_type = 9
