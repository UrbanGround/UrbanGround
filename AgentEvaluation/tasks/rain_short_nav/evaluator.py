"""Evaluator for rainy-day short-range navigation (RN task IDs, serialized as type 0).

RN payloads reuse the ShortNav schema (startPoint/endPoint) so the sandbox loads them
through the same /task/enter path; the RN- task ID prefix routes them here instead of
ShortNavEvaluator (see tasks/registry.py). The episode is a standard short-range
navigation run except the weather is switched to rain after the teleport, and the
metrics additionally report the share of action time the agent spent being rained on
(and sheltered).
"""

from __future__ import annotations

from typing import Any

from ..rain import RainEpisodeMixin
from ..short_nav import ShortNavEvaluator
from .prompt import SYSTEM_PROMPT


class RainShortNavEvaluator(RainEpisodeMixin, ShortNavEvaluator):
    """Evaluate short-range navigation under rainy weather with rain-exposure metrics."""

    task_type = 0
    task_name = "RainShortNav"
    task_id_prefix = "RN-"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def task_specific_metrics(self) -> dict[str, Any]:
        return {**super().task_specific_metrics(), **self._rain_metrics()}
