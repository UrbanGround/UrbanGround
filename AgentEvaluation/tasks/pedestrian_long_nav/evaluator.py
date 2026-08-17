"""Evaluator for pedestrian-enabled long-range navigation (PL task IDs, type 2).

PL payloads reuse the LongNav schema (startPoint/endPoint) and the PL- task ID prefix
routes them here (see tasks/registry.py). Per spec the prompt and task semantics are
identical to plain LongNav -- the only difference is that pedestrian simulation is
enabled for the episode, and the metrics additionally report how often the agent
collided with pedestrians.
"""

from __future__ import annotations

from typing import Any

from ..long_nav import LongNavEvaluator
from ..pedestrians import PedestrianEpisodeMixin


class PedestrianLongNavEvaluator(PedestrianEpisodeMixin, LongNavEvaluator):
    """Long-range navigation with pedestrians enabled and collision metrics."""

    task_type = 2
    task_name = "PedestrianLongNav"
    task_id_prefix = "PL-"

    # build_system_prompt / task_instructions intentionally inherited from
    # LongNavEvaluator unchanged: pedestrians are an environmental condition, not
    # part of the task text.

    def task_specific_metrics(self) -> dict[str, Any]:
        return {**super().task_specific_metrics(), **self._pedestrian_metrics()}
