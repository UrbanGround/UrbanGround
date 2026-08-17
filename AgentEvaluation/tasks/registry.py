"""Registry that maps serialized Unity task types to Python evaluators."""

from __future__ import annotations

from typing import Any, Union

from api import LLMClient
from sandbox import AgentClient

from .base import BaseNavEvaluator, BaseTaskEvaluator, TaskEpisodeConfig
from .condition import CONDITION_NAV_PREFIXES, CONDITION_QA_PREFIXES
from .condition_nav import ConditionShortNavEvaluator
from .condition_qa import (
    ConditionExplorationQAEvaluator,
    ConditionOrientationQAEvaluator,
    ConditionSpatialQAEvaluator,
)
from .constrained_nav import ConstrainedNavEvaluator
from .dynamic_closure_nav import DynamicClosureNavEvaluator
from .implicit_intent_nav import ImplicitIntentNavEvaluator
from .instruction_nav import InstructionNavEvaluator
from .landmark_qa import LandmarkQAEvaluator
from .long_nav import LongNavEvaluator
from .multipoint_nav import MultipointNavEvaluator
from .orientation_qa import OrientationQAEvaluator
from .pedestrian_long_nav import PedestrianLongNavEvaluator
from .place_search import PlaceSearchEvaluator
from .pedestrian_short_nav import PedestrianShortNavEvaluator
from .rain_exploration_qa import (
    RainExplorationQAEvaluator,
    RainOrientationQAEvaluator,
    RainSpatialQAEvaluator,
)
from .rain_short_nav import RainShortNavEvaluator
from .schedule_window_nav import ScheduleWindowNavEvaluator
from .search_qa import SpatialQAEvaluator
from .short_nav import ShortNavEvaluator

AnyTaskEvaluator = Union[BaseTaskEvaluator, BaseNavEvaluator]

EVALUATORS: dict[int, type[AnyTaskEvaluator]] = {
    # Keep type-12 entries out of this numeric mapping: both DynamicClosureNav (CN IDs) and
    # ImplicitIntentNav (II IDs) currently share numeric type 12, so create_evaluator must
    # inspect the ID prefix before falling back to one evaluator class.
    LandmarkQAEvaluator.task_type: LandmarkQAEvaluator,
    OrientationQAEvaluator.task_type: OrientationQAEvaluator,
    SpatialQAEvaluator.task_type: SpatialQAEvaluator,
    ShortNavEvaluator.task_type: ShortNavEvaluator,
    LongNavEvaluator.task_type: LongNavEvaluator,
    InstructionNavEvaluator.task_type: InstructionNavEvaluator,
    ConstrainedNavEvaluator.task_type: ConstrainedNavEvaluator,
    # Type 5 is used exclusively by SF-* schedule-following payloads, type 3 by PS-*
    # place-search payloads, and type 13 exclusively by MP-* multipoint payloads, so no
    # ID-prefix disambiguation is needed here (unlike the shared type 12).
    ScheduleWindowNavEvaluator.task_type: ScheduleWindowNavEvaluator,
    MultipointNavEvaluator.task_type: MultipointNavEvaluator,
    PlaceSearchEvaluator.task_type: PlaceSearchEvaluator,
}

CONDITION_QA_EVALUATORS: dict[int, type[AnyTaskEvaluator]] = {
    7: ConditionExplorationQAEvaluator,
    8: ConditionOrientationQAEvaluator,
    9: ConditionSpatialQAEvaluator,
}

RAIN_QA_EVALUATORS: dict[int, type[AnyTaskEvaluator]] = {
    7: RainExplorationQAEvaluator,
    8: RainOrientationQAEvaluator,
    9: RainSpatialQAEvaluator,
}


def create_evaluator(task: dict[str, Any], sandbox: AgentClient, llm: LLMClient,
                     config: TaskEpisodeConfig) -> AnyTaskEvaluator:
    task_type = int(task["type"])
    task_id_prefix = str(task.get("id", "")).split("-", 1)[0].upper()
    # Rainy-day variants reuse the Level-1 QA (7/8/9) / ShortNav (0) numeric types, and
    # pedestrian-enabled variants reuse ShortNav (0) / LongNav (2), so the sandbox loads
    # them through the stock /task/enter path; the ID prefixes route them to the
    # instrumented evaluators instead.
    if task_id_prefix == "RQ":
        evaluator_class: type[AnyTaskEvaluator] | None = RAIN_QA_EVALUATORS.get(task_type)
    elif task_id_prefix == "RN":
        evaluator_class = RainShortNavEvaluator
    elif task_id_prefix == "PD":
        evaluator_class = PedestrianShortNavEvaluator
    elif task_id_prefix == "PL":
        evaluator_class = PedestrianLongNavEvaluator
    elif task_id_prefix in CONDITION_QA_PREFIXES:
        evaluator_class = CONDITION_QA_EVALUATORS.get(task_type)
    elif task_id_prefix in CONDITION_NAV_PREFIXES:
        evaluator_class = ConditionShortNavEvaluator
    elif task_type == 12:
        evaluator_class = (
            ImplicitIntentNavEvaluator if task_id_prefix == "II" else DynamicClosureNavEvaluator
        )
    else:
        evaluator_class = EVALUATORS.get(task_type)
    if evaluator_class is None:
        raise ValueError(f"No evaluator is registered for task type {task_type}")
    return evaluator_class(task, sandbox, llm, config)
