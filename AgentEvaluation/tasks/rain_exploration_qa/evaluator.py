"""Evaluators for rainy-day Level-1 QA (RQ task IDs, numeric types 7/8/9).

RQ payloads reuse the Level-1 QA schema (qaStartPoint + four-choice qaOptions +
qaAnswerIndex) so the sandbox loads them through the source task's /task/enter path; the RQ- task
ID prefix routes them here instead of LandmarkQAEvaluator (see tasks/registry.py). The
episode is a standard active-exploration QA run except the weather is switched to rain
after the teleport, and the metrics additionally report the share of action time the
agent spent being rained on (and sheltered).
"""

from __future__ import annotations

from typing import Any

from ..landmark_qa import LandmarkQAEvaluator
from ..orientation_qa import OrientationQAEvaluator
from ..rain import RainEpisodeMixin
from ..search_qa import SpatialQAEvaluator
from .prompt import SYSTEM_PROMPT

RAIN_QA_NOTICE = (
    "It is currently raining in the scene. Rain exposure is measured; when it does not "
    "compromise gathering the visual evidence needed for this question, prefer overhead cover "
    "such as arcades, awnings, covered walkways, and footbridges."
)


class _RainQAMixin(RainEpisodeMixin):
    task_name = "RainExplorationQA"
    task_id_prefix = "RQ-"

    def build_system_prompt(self) -> str:
        return f"{super().build_system_prompt()}\n\n{RAIN_QA_NOTICE}"

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        return {**super().task_specific_metrics(answer), **self._rain_metrics()}


class RainExplorationQAEvaluator(_RainQAMixin, LandmarkQAEvaluator):
    """Evaluate LandmarkQA under rainy weather with rain-exposure metrics."""

    task_type = 7

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT


class RainOrientationQAEvaluator(_RainQAMixin, OrientationQAEvaluator):
    """Evaluate OrientationQA under rainy weather with rain-exposure metrics."""

    task_type = 8


class RainSpatialQAEvaluator(_RainQAMixin, SpatialQAEvaluator):
    """Evaluate SpatialQA under rainy weather with rain-exposure metrics."""

    task_type = 9
