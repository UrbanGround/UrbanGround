"""Evaluator for pedestrian-enabled short-range navigation (PD task IDs, type 0).

PD payloads reuse the ShortNav schema (startPoint/endPoint) and the PD- task ID prefix
routes them here (see tasks/registry.py). Per spec the prompt and task semantics are
identical to plain ShortNav -- the only difference is that pedestrian simulation is
enabled for the episode, and the metrics additionally report how often the agent
collided with pedestrians.

Note: this prefix was originally PS- and was renamed to PD- once the official
place-type-search (PS) tasks appeared, since the Unity editor owns the PS- prefix.
"""

from __future__ import annotations

from typing import Any

from ..pedestrians import PedestrianEpisodeMixin
from ..short_nav import ShortNavEvaluator


class PedestrianShortNavEvaluator(PedestrianEpisodeMixin, ShortNavEvaluator):
    """Short-range navigation with pedestrians enabled and collision metrics."""

    task_type = 0
    task_name = "PedestrianShortNav"
    task_id_prefix = "PD-"

    # build_system_prompt / task_instructions intentionally inherited from
    # ShortNavEvaluator unchanged: pedestrians are an environmental condition, not
    # part of the task text.

    def task_specific_metrics(self) -> dict[str, Any]:
        return {**super().task_specific_metrics(), **self._pedestrian_metrics()}
