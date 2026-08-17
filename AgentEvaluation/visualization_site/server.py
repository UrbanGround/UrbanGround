"""Standalone visualization server for AgentEvaluation runs.

Serves a small read-only JSON API plus a static single-page front end for browsing every
model's evaluation output under `AgentEvaluation/output/tasks/<model>/`: per-model summary
statistics, per-task-type breakdowns, and per-task detail (every ReAct step, every recorded
frame, and the encoded episode video), including frame-level completion/closure-violation
status for the ConstrainedNav / DynamicClosureNav task types and implicit-intent navigation.

Deliberately uses only the Python standard library (`http.server`) so it runs anywhere the
evaluation pipeline itself runs, with no extra pip dependencies.

Usage:
    python3 AgentEvaluation/visualization_site/server.py --port 8000
    # then open http://localhost:8000/ in a browser
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import urllib.parse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../AgentEvaluation
OUTPUT_ROOT = PROJECT_ROOT / "output" / "tasks"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Optional offline Cesium 3D Tiles directory, served under /3d-tiles/ when configured.
_tileset_dir = os.environ.get("URBANGROUND_TILESET_DIR")
TILESET_DIR = Path(_tileset_dir).resolve() if _tileset_dir else None

# CN-* task IDs are reused for both ConstrainedNav (11) and DynamicClosureNav (12), while II-*
# task IDs currently also serialize as numeric type 12 but mean ImplicitIntentNav. Every other
# prefix maps 1:1 to a single task type. Used only to derive a stable, human-friendly grouping
# label when report.json is missing/unreadable (e.g. a hard-failed task with no report yet).
TASK_ID_PREFIX_RE = re.compile(r"^([A-Za-z]+)-")


@dataclass(frozen=True)
class TaskRunStatus:
    status: str  # "completed" | "running" | "failed"
    task_type: str | None
    metrics: dict[str, Any] | None


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_models() -> list[str]:
    if not OUTPUT_ROOT.is_dir():
        return []
    return sorted(
        entry.name for entry in OUTPUT_ROOT.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def list_task_dirs(model: str) -> list[Path]:
    model_dir = OUTPUT_ROOT / model
    if not model_dir.is_dir():
        return []
    return sorted(
        entry for entry in model_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def task_status(task_dir: Path) -> TaskRunStatus:
    """Classify one task output directory using the same convention run_task.py writes.

    - `run_failure.json` present -> the sandbox/episode raised before a report could be
      produced (or produced one mid-episode); always "failed" regardless of any partial report.
    - `report.json` with a non-null "metrics" -> the episode ran to completion ("completed").
    - `report.json` with "metrics": null -> a partial report from `_write_partial` while the
      episode was still in progress when the process last touched disk ("running").
    - Neither file -> nothing has been persisted for this task yet; treated as "running" so it
      still shows up (this should not normally happen once a directory exists).
    """
    failure_path = task_dir / "run_failure.json"
    report_path = task_dir / "report.json"
    if failure_path.is_file():
        failure = _safe_json_load(failure_path) or {}
        task_type_id = failure.get("task_type")
        return TaskRunStatus(
            status="failed",
            task_type=_task_type_label_for_failure(task_dir.name, task_type_id),
            metrics=None,
        )
    report = _safe_json_load(report_path) if report_path.is_file() else None
    if report is not None:
        metrics = report.get("metrics")
        status = "completed" if metrics is not None else "running"
        return TaskRunStatus(status=status, task_type=report.get("task_type"), metrics=metrics)
    return TaskRunStatus(status="running", task_type=None, metrics=None)


# Ordered from the simplest task level to the most complex; this fixed ordering (rather than
# alphabetical) is what the UI groups tasks by, since it mirrors the benchmark's difficulty
# progression (a plain short-distance walk is "level 1", a dynamic road-closure detour with
# constrained navigation is the hardest "level").
_TASK_TYPE_NAMES = {
    0: "ShortNav", 2: "LongNav", 3: "PlaceSearch", 5: "ScheduleWindowNav",
    7: "LandmarkQA", 8: "OrientationQA", 9: "SpatialQA",
    10: "InstructionNav", 11: "ConstrainedNav", 12: "DynamicClosureNav",
    13: "MultipointNav",
    "II": "ImplicitIntentNav",
}
_TASK_TYPE_ORDER = list(_TASK_TYPE_NAMES.values())
_TASK_GROUP_SORT_INDEX = {name: index for index, name in enumerate(_TASK_TYPE_ORDER)}


def _task_group_sort_key(group: str) -> tuple[int, str]:
    """Sort groups by benchmark difficulty level, unknown groups sorted last alphabetically."""
    return (_TASK_GROUP_SORT_INDEX.get(group, len(_TASK_TYPE_ORDER)), group)


def _task_type_label(type_id: Any) -> str | None:
    try:
        return _TASK_TYPE_NAMES.get(int(type_id))
    except (TypeError, ValueError):
        return None


# Environmental-condition variant prefixes (kept in sync with tasks/condition.py's
# CONDITIONS table; duplicated here because this server deliberately depends on the
# standard library only).
_CONDITION_PREFIX_NAMES = {
    "TSQ": "ThunderstormQA", "TSN": "ThunderstormNav",
    "OCQ": "OvercastQA", "OCN": "OvercastNav",
    "CLQ": "CloudyQA", "CLN": "CloudyNav",
    "EVQ": "DuskQA", "EVN": "DuskNav",
    "NTQ": "NightQA", "NTN": "NightNav",
}


def _task_type_label_for_failure(task_id: str, type_id: Any) -> str | None:
    """Recover a readable task type for run_failure.json records.

    Numeric type 12 is ambiguous between DynamicClosureNav (CN IDs) and ImplicitIntentNav
    (II IDs), and rainy-day / pedestrian / condition variants reuse types 7/0/2, so use
    the ID prefix whenever the payload only contains the serialized number.
    """
    task_id = str(task_id)
    prefix = task_id.split("-", 1)[0].upper() if "-" in task_id else ""
    condition_types = {"7", "8", "9"} if prefix.endswith("Q") else {"0"}
    if prefix in _CONDITION_PREFIX_NAMES and str(type_id) in condition_types:
        return _CONDITION_PREFIX_NAMES[prefix]
    if task_id.startswith("II-") and str(type_id) == "12":
        return "ImplicitIntentNav"
    if task_id.startswith("RQ-") and str(type_id) in {"7", "8", "9"}:
        return "RainExplorationQA"
    if task_id.startswith("RN-") and str(type_id) == "0":
        return "RainShortNav"
    if task_id.startswith("PD-") and str(type_id) == "0":
        return "PedestrianShortNav"
    if task_id.startswith("PL-") and str(type_id) == "2":
        return "PedestrianLongNav"
    return _task_type_label(type_id)


# ---------------------------------------------------------------------------------------------
# Metric metadata: one-line human descriptions plus a curated "meaningful" subset per task group.
#
# Every evaluator can emit a fairly large `metrics` dict (see AgentEvaluation/tasks/metrics.py,
# tasks/qa.py, and each evaluator's task_specific_metrics()), but several fields are internal
# bookkeeping, redundant with another field, or a fixed task/config constant rather than an
# actual measured result. METRIC_DEFINITIONS documents every field that *can* appear; only the
# keys listed per task group in TASK_GROUP_METRICS are surfaced in the UI.
# ---------------------------------------------------------------------------------------------

MetricFormat = str  # "percent" | "meters" | "seconds" | "count" | "ratio" | "boolean" | "text"

METRIC_DEFINITIONS: dict[str, dict[str, str]] = {
    "task_completed": {
        "label": "Task Completed",
        "format": "boolean",
        "description": "Whether the evaluator's task-specific success condition became true.",
    },
    "steps_completed": {
        "label": "Total Steps",
        "format": "count",
        "description": "Total ReAct decision steps recorded before the episode ended.",
    },
    "completion_step": {
        "label": "Completion Step",
        "format": "count",
        "description": "First recorded step at which the task-specific success condition became true.",
    },
    "completion_elapsed_seconds": {
        "label": "Time to Completion",
        "format": "seconds",
        "description": "Episode wall-clock seconds elapsed when the task first became successful.",
    },
    "completion_event": {
        "label": "Completion Event",
        "format": "text",
        "description": "Evaluator event that established success, such as final_answer or destination_reached.",
    },
    "agent_terminated": {
        "label": "Agent Terminated",
        "format": "boolean",
        "description": "Whether the agent explicitly chose the terminate action.",
    },
    "agent_termination_step": {
        "label": "Termination Step",
        "format": "count",
        "description": "Step on which the agent explicitly chose terminate.",
    },
    "agent_termination_elapsed_seconds": {
        "label": "Time to Termination",
        "format": "seconds",
        "description": "Episode wall-clock seconds elapsed when the agent chose terminate.",
    },
    "steps_completed_at_termination": {
        "label": "Steps at Termination",
        "format": "count",
        "description": "Total ReAct decision steps made when terminate ended the episode, including the terminate step.",
    },
    "reached_destination": {
        "label": "Arrival Success",
        "format": "boolean",
        "description": "Whether the agent's final position fell within the arrival radius of the labeled destination.",
    },
    "remaining_distance_ratio": {
        "label": "Remaining Distance Ratio",
        "format": "ratio",
        "description": "Final distance to the destination divided by the original start-to-destination distance; 0 means arrival, 1 means no net progress.",
    },
    "original_distance_meters": {
        "label": "Task Distance",
        "format": "meters",
        "description": "Straight-line distance from the labeled start point to the destination, i.e. how far this task required traveling.",
    },
    "distance_to_destination_meters": {
        "label": "Final Distance to Goal",
        "format": "meters",
        "description": "Straight-line distance between the agent's final position and the destination.",
    },
    "path_length_meters": {
        "label": "Path Length",
        "format": "meters",
        "description": "Total straight-line distance summed across every recorded movement step, i.e. how far the agent actually traveled.",
    },
    "elapsed_action_seconds": {
        "label": "Action Time",
        "format": "seconds",
        "description": "Total wall-clock time spent executing actions in the sandbox across the whole episode.",
    },
    "sidewalk_time_ratio": {
        "label": "Sidewalk Compliance",
        "format": "percent",
        "description": "Fraction of action time during which the agent's reported position was on a sidewalk rather than a road.",
    },
    "map_usage_step_count": {
        "label": "Map Usage Steps",
        "format": "count",
        "description": "Number of steps in which the agent issued a map-mode action (opening/panning/zooming the map or querying a route).",
    },
    "answer_correct": {
        "label": "Answer Correct",
        "format": "boolean",
        "description": "Whether the agent's final multiple-choice answer matched the labeled correct option.",
    },
    "closure_violated": {
        "label": "Closure Violated",
        "format": "boolean",
        "description": "Whether the agent's movement crossed a disclosed road-closure line at any point, which unconditionally fails the task.",
    },
    "poi_evidence_step_ratio": {
        "label": "POI Evidence Ratio",
        "format": "percent",
        "description": "Fraction of steps whose visual observation mentions candidate POI names, signs, logos, or entrances while inferring the destination.",
    },
    "poi_inspection_step_count": {
        "label": "POI Inspection Steps",
        "format": "count",
        "description": "Number of steps spent deliberately turning or orbiting to inspect nearby places while inferring the intended destination.",
    },
    "closure_disclosure_step": {
        "label": "Closure Disclosure Step",
        "format": "count",
        "description": "The step index at which the agent was notified that a road closure had newly appeared on the map.",
    },
    "schedule_stop_arrival_ratio": {
        "label": "Schedule Stops Reached",
        "format": "percent",
        "description": "Fraction of scheduled appointment stops the agent reached in the scheduled order.",
    },
    "schedule_on_time_ratio": {
        "label": "On-Time Stop Ratio",
        "format": "percent",
        "description": "Fraction of timed appointment stops reached before their scheduled deadline; an unreached timed stop counts as not on time.",
    },
    "schedule_order_violation_count": {
        "label": "Order Violations",
        "format": "count",
        "description": "How many times the agent entered a later appointment's arrival radius before completing the earlier ones.",
    },
    "schedule_max_lateness_seconds": {
        "label": "Worst Lateness",
        "format": "seconds",
        "description": "Largest per-stop lateness against the scheduled deadline across all reached timed stops.",
    },
    "schedule_all_on_time": {
        "label": "All Stops On Time",
        "format": "boolean",
        "description": "Whether every timed appointment stop was reached before its scheduled deadline.",
    },
    "schedule_finished_within_total_deadline": {
        "label": "Within Total Deadline",
        "format": "boolean",
        "description": "For errand-chain schedules with one overall deadline, whether the whole schedule was finished in time.",
    },
    "rain_exposure_time_ratio": {
        "label": "Rain Exposure Ratio",
        "format": "percent",
        "description": "Fraction of action time during which the agent's position was directly rained on (no overhead shelter).",
    },
    "rain_exposure_seconds": {
        "label": "Rain Exposure Time",
        "format": "seconds",
        "description": "Total action time during which the agent's position was directly rained on.",
    },
    "sheltered_time_ratio": {
        "label": "Sheltered Ratio",
        "format": "percent",
        "description": "Fraction of action time during which the agent's position had overhead shelter from the rain.",
    },
    "rain_exposure_counter_seconds": {
        "label": "Rain Exposure (Sandbox Counter)",
        "format": "seconds",
        "description": "Rain exposure measured by the sandbox's own cumulative counter across the episode.",
    },
    "pedestrian_collision_count": {
        "label": "Pedestrian Collisions",
        "format": "count",
        "description": "Number of times the agent collided with a pedestrian during the episode (sandbox counter delta).",
    },
    "pedestrian_collided": {
        "label": "Collided With Pedestrian",
        "format": "boolean",
        "description": "Whether the agent collided with any pedestrian during the episode.",
    },
    "pedestrian_count_mean": {
        "label": "Mean Crowd Size",
        "format": "count",
        "description": "Average number of simulated pedestrians present across the episode's recorded states.",
    },
    "pedestrian_count_max": {
        "label": "Peak Crowd Size",
        "format": "count",
        "description": "Maximum number of simulated pedestrians present in any recorded state.",
    },
    "multipoint_completion_ratio": {
        "label": "Targets Completion",
        "format": "percent",
        "description": "Fraction of the multi-point route's targets the agent physically visited.",
    },
    "multipoint_targets_visited": {
        "label": "Targets Visited",
        "format": "count",
        "description": "How many of the route's targets the agent physically visited.",
    },
    "multipoint_all_completed": {
        "label": "All Targets Visited",
        "format": "boolean",
        "description": "Whether the agent visited every target of the multi-point route.",
    },
    "multipoint_route_efficiency": {
        "label": "Route Efficiency",
        "format": "ratio",
        "description": "MST lower-bound route length divided by the agent's actual path length; higher means less wasted travel.",
    },
    "multipoint_optimal_lower_bound_meters": {
        "label": "Route Lower Bound",
        "format": "meters",
        "description": "Minimum spanning tree length over start + targets; any route visiting all targets must travel at least this far.",
    },
    "placesearch_found": {
        "label": "Place Found",
        "format": "boolean",
        "description": "Whether the LLM judge decided the agent's final view counts as having arrived at the requested place type.",
    },
    "placesearch_target_mention_step_ratio": {
        "label": "Target Mention Ratio",
        "format": "percent",
        "description": "Fraction of steps whose observation mentions the requested place's significant terms.",
    },
    "placesearch_map_step_count": {
        "label": "Map Usage Steps",
        "format": "count",
        "description": "Number of steps in which the agent used a map-mode action while searching.",
    },
    "placesearch_inspection_step_count": {
        "label": "Inspection Steps",
        "format": "count",
        "description": "Number of steps spent turning/orbiting to inspect the surroundings while searching.",
    },
    "condition_applied": {
        "label": "Condition Applied",
        "format": "boolean",
        "description": "Whether the environmental condition (weather and/or clock) was successfully applied in the sandbox for this episode.",
    },
    "condition_weather": {
        "label": "Condition Weather",
        "format": "text",
        "description": "The weather the episode was configured to run under.",
    },
    "condition_clock": {
        "label": "Condition Clock",
        "format": "text",
        "description": "The in-simulation clock time the episode was configured to start at, if any.",
    },
}

# Fields intentionally left out of every group below (and why), for maintainers:
#   sidewalk_seconds, sidewalk_state_ratio  -> redundant with sidewalk_time_ratio
#   displacement_meters                     -> redundant/confusable with path_length_meters
#   map_step_count, first_person_step_count -> redundant with map_usage_step_count
#   remaining_distance_meters               -> duplicate of distance_to_destination_meters
#   arrival_radius_meters                   -> fixed config constant, not a measured result
#   navigate_call_count, used_map, used_navigation_api -> the `navigate` action has been removed
#                                            from the current action space; no longer meaningful
#   closure_checked_step_count, closure_edge_count,
#   closure_disclosure_delay_seconds        -> internal bookkeeping / fixed task constants
#   closure_disclosed                       -> redundant with closure_disclosure_step (non-null iff disclosed)
#   answer_valid                            -> almost always true; not a meaningful comparison axis
CONDITION_METRICS = ["condition_applied", "condition_weather", "condition_clock"]
LIFECYCLE_METRICS = [
    "task_completed", "steps_completed", "completion_step", "completion_elapsed_seconds",
    "completion_event", "agent_terminated", "agent_termination_step",
    "agent_termination_elapsed_seconds", "steps_completed_at_termination",
]
QA_METRICS = ["answer_correct", *LIFECYCLE_METRICS]
NAV_METRICS = [
    "reached_destination", "remaining_distance_ratio", "original_distance_meters",
    "path_length_meters", "elapsed_action_seconds", "sidewalk_time_ratio",
    "map_usage_step_count", *LIFECYCLE_METRICS,
]
CLOSURE_NAV_METRICS = NAV_METRICS + ["closure_violated"]
DYNAMIC_CLOSURE_NAV_METRICS = CLOSURE_NAV_METRICS + ["closure_disclosure_step"]
IMPLICIT_INTENT_NAV_METRICS = NAV_METRICS + ["poi_evidence_step_ratio", "poi_inspection_step_count"]
SCHEDULE_WINDOW_NAV_METRICS = [
    "reached_destination", "schedule_stop_arrival_ratio", "schedule_on_time_ratio",
    "schedule_all_on_time", "schedule_order_violation_count",
    "schedule_max_lateness_seconds", "schedule_finished_within_total_deadline",
    "original_distance_meters", "path_length_meters", "elapsed_action_seconds",
    "sidewalk_time_ratio", *LIFECYCLE_METRICS,
]
RAIN_METRICS = [
    "rain_exposure_time_ratio", "rain_exposure_seconds", "sheltered_time_ratio",
    "rain_exposure_counter_seconds",
]
PEDESTRIAN_METRICS = [
    "pedestrian_collision_count", "pedestrian_collided", "pedestrian_count_mean",
    "pedestrian_count_max",
]
MULTIPOINT_METRICS = [
    "multipoint_completion_ratio", "multipoint_targets_visited",
    "multipoint_all_completed", "multipoint_route_efficiency",
    "multipoint_optimal_lower_bound_meters", "path_length_meters",
    "elapsed_action_seconds", "sidewalk_time_ratio", *LIFECYCLE_METRICS,
]
PLACE_SEARCH_METRICS = [
    "answer_correct", "placesearch_found", "placesearch_target_mention_step_ratio",
    "placesearch_map_step_count", "placesearch_inspection_step_count",
    "path_length_meters", "elapsed_action_seconds", "sidewalk_time_ratio",
    *LIFECYCLE_METRICS,
]

TASK_GROUP_METRICS: dict[str, list[str]] = {
    "LandmarkQA": QA_METRICS,
    "OrientationQA": QA_METRICS,
    "SpatialQA": QA_METRICS,
    "ShortNav": NAV_METRICS,
    "LongNav": NAV_METRICS,
    "InstructionNav": NAV_METRICS,
    "ConstrainedNav": CLOSURE_NAV_METRICS,
    "DynamicClosureNav": DYNAMIC_CLOSURE_NAV_METRICS,
    "ImplicitIntentNav": IMPLICIT_INTENT_NAV_METRICS,
    "ScheduleWindowNav": SCHEDULE_WINDOW_NAV_METRICS,
    "RainExplorationQA": QA_METRICS + RAIN_METRICS,
    "RainShortNav": NAV_METRICS + RAIN_METRICS,
    "PedestrianShortNav": NAV_METRICS + PEDESTRIAN_METRICS,
    "PedestrianLongNav": NAV_METRICS + PEDESTRIAN_METRICS,
    "MultipointNav": MULTIPOINT_METRICS,
    "PlaceSearch": PLACE_SEARCH_METRICS,
    "ThunderstormQA": QA_METRICS + CONDITION_METRICS,
    "ThunderstormNav": NAV_METRICS + CONDITION_METRICS,
    "OvercastQA": QA_METRICS + CONDITION_METRICS,
    "OvercastNav": NAV_METRICS + CONDITION_METRICS,
    "CloudyQA": QA_METRICS + CONDITION_METRICS,
    "CloudyNav": NAV_METRICS + CONDITION_METRICS,
    "DuskQA": QA_METRICS + CONDITION_METRICS,
    "DuskNav": NAV_METRICS + CONDITION_METRICS,
    "NightQA": QA_METRICS + CONDITION_METRICS,
    "NightNav": NAV_METRICS + CONDITION_METRICS,
}

# Historical PedestrianShortNav runs remain readable, but the task was retired from the
# benchmark and must not be placed back into the ladder's generic "Other" section.
BENCHMARK_EXCLUDED_GROUPS = {"PedestrianShortNav"}


def _metrics_for_group(group: str) -> list[str]:
    return TASK_GROUP_METRICS.get(group, NAV_METRICS)


def _task_group_label(task_id: str, task_type_name: str | None) -> str:
    if task_type_name:
        return task_type_name
    match = TASK_ID_PREFIX_RE.match(task_id)
    return match.group(1) if match else "Unknown"


# The metric whose truthiness decides whether a *finished* episode counts as a benchmark
# "success" (the agent actually accomplished the task) versus "failed" (it ran to completion
# without erroring, but did not achieve the goal) -- as opposed to `TaskRunStatus.status`, which
# only reflects whether the episode process itself finished, crashed, or is still running.
# `reached_destination` already folds in closure violations (see tasks/base.py._finalize, which
# forces it to False on a violation), so no extra check is needed here for the closure task types.
_OUTCOME_METRIC_BY_GROUP: dict[str, str] = {
    "LandmarkQA": "answer_correct",
    "OrientationQA": "answer_correct",
    "SpatialQA": "answer_correct",
    "ShortNav": "reached_destination",
    "LongNav": "reached_destination",
    "InstructionNav": "reached_destination",
    "ConstrainedNav": "reached_destination",
    "DynamicClosureNav": "reached_destination",
    "ImplicitIntentNav": "reached_destination",
    "ScheduleWindowNav": "reached_destination",
    "RainExplorationQA": "answer_correct",
    "RainShortNav": "reached_destination",
    "PedestrianShortNav": "reached_destination",
    "PedestrianLongNav": "reached_destination",
    "MultipointNav": "reached_destination",
    "PlaceSearch": "answer_correct",
    "ThunderstormQA": "answer_correct",
    "ThunderstormNav": "reached_destination",
    "OvercastQA": "answer_correct",
    "OvercastNav": "reached_destination",
    "CloudyQA": "answer_correct",
    "CloudyNav": "reached_destination",
    "DuskQA": "answer_correct",
    "DuskNav": "reached_destination",
    "NightQA": "answer_correct",
    "NightNav": "reached_destination",
}


# Benchmark difficulty ladder (see the benchmark figure): every task group belongs to
# exactly one level; the model page renders the levels in this order, and the
# environmental-condition variants (weather / time-of-day) are deliberately shown last,
# below the ladder, since they replay Level-1/2 tasks under harsher conditions rather
# than forming a rung of their own.
LADDER_LEVELS: list[dict[str, Any]] = [
    {
        "key": "level1",
        "title": "Level 1 · Local Environment Understanding",
        "groups": [
            ("LandmarkQA", "Visual Recognition (VR)"),
            ("OrientationQA", "Orientation Understanding (OU)"),
            ("SpatialQA", "Active Exploration Questions (AEQ)"),
        ],
    },
    {
        "key": "level2",
        "title": "Level 2 · Navigation under Explicit Instructions",
        "groups": [
            ("ShortNav", "Short-range Goal Navigation (SGN)"),
            ("LongNav", "Long-range Goal Navigation (LGN)"),
            ("InstructionNav", "Instructional Navigation (IN)"),
            ("ConstrainedNav", "Constrained Navigation (CN)"),
        ],
    },
    {
        "key": "level3",
        "title": "Level 3 · Exploration under Implicit Instructions",
        "groups": [
            ("PlaceSearch", "Place-type Search (PTS)"),
            ("ImplicitIntentNav", "Implicit Intent Inference (III)"),
        ],
    },
    {
        "key": "level4",
        "title": "Level 4 · Multi-Task Planning",
        "groups": [
            ("ScheduleWindowNav", "Time-window Scheduling (TWS)"),
            ("MultipointNav", "Multi-stop Route Planning (MSP)"),
        ],
    },
    {
        "key": "level5",
        "title": "Level 5 · Dynamic Environment Interaction",
        "groups": [
            ("DynamicClosureNav", "Dynamic Road-closure Replanning (DCR)"),
            ("PedestrianLongNav", "Navigation among Pedestrians (NP · long)"),
        ],
    },
]
CONDITIONS_LEVEL: dict[str, Any] = {
    "key": "conditions",
    "title": "Environmental Conditions · weather & time-of-day variants",
    "groups": [
        ("RainExplorationQA", "Rain · Exploration QA"),
        ("RainShortNav", "Rain · Short-range Navigation"),
        ("ThunderstormQA", "Thunderstorm · Exploration QA"),
        ("ThunderstormNav", "Thunderstorm · Short-range Navigation"),
        ("OvercastQA", "Overcast · Exploration QA"),
        ("OvercastNav", "Overcast · Short-range Navigation"),
        ("CloudyQA", "Cloudy · Exploration QA"),
        ("CloudyNav", "Cloudy · Short-range Navigation"),
        ("DuskQA", "Clear Dusk (18:30) · Exploration QA"),
        ("DuskNav", "Clear Dusk (18:30) · Short-range Navigation"),
        ("NightQA", "Clear Night (23:30) · Exploration QA"),
        ("NightNav", "Clear Night (23:30) · Short-range Navigation"),
    ],
}


def _ladder_for_groups(present_groups: list[str]) -> list[dict[str, Any]]:
    """Order the groups that actually have results into the ladder levels.

    Levels with no results are omitted; groups not mapped anywhere are collected into an
    "Other" level placed just above the environmental-conditions section (which is always
    last).
    """
    present = set(present_groups)
    mapped: set[str] = set()
    ladder: list[dict[str, Any]] = []
    for level in LADDER_LEVELS:
        groups = [{"group": name, "label": label}
                  for name, label in level["groups"] if name in present]
        mapped.update(name for name, _ in level["groups"])
        if groups:
            ladder.append({"key": level["key"], "title": level["title"], "groups": groups})
    condition_groups = [{"group": name, "label": label}
                        for name, label in CONDITIONS_LEVEL["groups"] if name in present]
    mapped.update(name for name, _ in CONDITIONS_LEVEL["groups"])
    others = sorted(present - mapped - BENCHMARK_EXCLUDED_GROUPS)
    if others:
        ladder.append({"key": "other", "title": "Other task types",
                       "groups": [{"group": name, "label": None} for name in others]})
    if condition_groups:
        ladder.append({"key": CONDITIONS_LEVEL["key"], "title": CONDITIONS_LEVEL["title"],
                       "groups": condition_groups})
    return ladder


def task_outcome(group: str, metrics: dict[str, Any] | None) -> str | None:
    """Return "success" / "failed" for a *completed* episode, or None if undecidable.

    This is orthogonal to `TaskRunStatus.status`: a task can finish running (status
    "completed") yet still be a benchmark failure because the agent never reached the
    destination / never answered correctly / crossed a road closure.
    """
    if not metrics:
        return None
    key = _OUTCOME_METRIC_BY_GROUP.get(group, "reached_destination")
    value = metrics.get(key)
    if not isinstance(value, bool):
        return None
    return "success" if value else "failed"


def build_model_summary(model: str) -> dict[str, Any]:
    task_dirs = list_task_dirs(model)
    all_tasks: list[dict[str, Any]] = []
    for task_dir in task_dirs:
        run = task_status(task_dir)
        group = _task_group_label(task_dir.name, run.task_type)
        all_tasks.append({
            "task_id": task_dir.name,
            "task_type": run.task_type,
            "task_group": group,
            "status": run.status,
            "outcome": task_outcome(group, run.metrics) if run.status == "completed" else None,
            "metrics": run.metrics,
            "has_video": (task_dir / "episode.mp4").is_file(),
            "frame_count": _count_frames(task_dir),
        })
    all_tasks.sort(key=lambda item: item["task_id"])

    # Retired task groups remain addressable through the task-detail API for historical audits,
    # but they no longer affect benchmark totals, ladder cards, or model overview statistics.
    benchmark_tasks = [
        task for task in all_tasks
        if task["task_group"] not in BENCHMARK_EXCLUDED_GROUPS
    ]
    excluded_tasks = [
        task for task in all_tasks
        if task["task_group"] in BENCHMARK_EXCLUDED_GROUPS
    ]

    # The site only displays finished benchmark episodes (never-run / crashed / still-running
    # tasks carry no meaningful outcome); unfinished runs are still counted in the stat strip.
    tasks = [task for task in benchmark_tasks if task["status"] == "completed"]

    by_group: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        by_group.setdefault(task["task_group"], []).append(task)

    succeeded = [task for task in tasks if task["outcome"] == "success"]
    task_failed = [task for task in tasks if task["outcome"] == "failed"]
    run_failed = [task for task in benchmark_tasks if task["status"] == "failed"]
    running = [task for task in benchmark_tasks if task["status"] == "running"]

    batch_report = _safe_json_load(OUTPUT_ROOT / model / "batch_report.json")

    ordered_groups = sorted(by_group.keys(), key=_task_group_sort_key)
    return {
        "model": model,
        "task_count": len(tasks),
        "completed_count": len(succeeded),
        "failed_count": len(task_failed),
        "run_failed_count": len(run_failed),
        "running_count": len(running),
        "excluded_historical_count": len(excluded_tasks),
        "task_groups": ordered_groups,
        "ladder": _ladder_for_groups(ordered_groups),
        "tasks_by_group": {
            group: sorted(items, key=lambda item: item["task_id"])
            for group, items in by_group.items()
        },
        "group_metrics": {
            group: _group_metric_summary(group, items)
            for group, items in by_group.items()
        },
        "batch_report_summary": _extract_batch_report_summary(batch_report),
    }


def _extract_batch_report_summary(batch_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not batch_report:
        return None
    return {
        "hyperparameters": batch_report.get("hyperparameters"),
        "task_count": batch_report.get("task_count"),
        "completed_count": batch_report.get("completed_count"),
        "failed_count": batch_report.get("failed_count"),
        "elapsed_seconds": batch_report.get("elapsed_seconds"),
        "accuracy": batch_report.get("accuracy"),
        "navigation_arrival_rate": batch_report.get("navigation_arrival_rate"),
        "closure_violation_rate": batch_report.get("closure_violation_rate"),
    }


def _group_metric_summary(group: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build the curated, described metric list for one task-type group's completed tasks.

    Returns one entry per metric in TASK_GROUP_METRICS[group] (skipping ones no completed task
    in this group actually reported), each carrying its display metadata plus the aggregate
    across this group's completed tasks -- this is what the merged "task group + metrics" card
    renders directly, no separate global Metrics section needed.

    Every task passed in is already a finished episode (status == "completed"); callers filter
    out crashed/still-running tasks before this is invoked.

    Boolean metrics (e.g. "reached destination: yes/no") report a single success-rate percentage
    rather than a mean/min/max of true/false, since "the minimum of a set of booleans" isn't a
    meaningful statistic -- the rate of `true` across all completed tasks is what matters.
    """
    entries = []
    for key in _metrics_for_group(group):
        values = [
            task["metrics"][key] for task in tasks
            if isinstance((task.get("metrics") or {}).get(key), (int, float, bool))
        ]
        if not values and not tasks:
            continue
        meta = METRIC_DEFINITIONS.get(key, {"label": key, "format": "text", "description": ""})
        if meta["format"] == "text":
            # Text metrics (e.g. condition_weather) aren't numeric: aggregate them as the
            # most common value across the group's tasks, shown under "Mean".
            text_values = [
                str(task["metrics"][key]) for task in tasks
                if isinstance((task.get("metrics") or {}).get(key), str)
                and task["metrics"][key]
            ]
            modal = max(set(text_values), key=text_values.count) if text_values else None
            entries.append({
                "key": key,
                "label": meta["label"],
                "format": "text",
                "description": meta["description"],
                "count": len(text_values),
                "mean": modal,
                "min": None,
                "max": None,
            })
            continue
        if meta["format"] == "boolean":
            rate = (sum(1 for value in values if value) / len(values)) if values else None
            entries.append({
                "key": key,
                "label": meta["label"],
                "format": "percent",
                "description": meta["description"],
                "count": len(values),
                "mean": round(rate, 6) if rate is not None else None,
                "min": None,
                "max": None,
            })
            continue
        numeric = [float(value) for value in values]
        entries.append({
            "key": key,
            "label": meta["label"],
            "format": meta["format"],
            "description": meta["description"],
            "count": len(values),
            "mean": round(sum(numeric) / len(numeric), 6) if numeric else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        })
    return entries


_FRAME_NAME_RE = re.compile(
    r"^(?P<index>\d+)_(?:step_(?P<step>\d+)_(?P<kind>before|action)(?:_(?P<sub>\d+))?"
    r"|(?P<label>initial|final_answer))\.jpg$"
)


def _count_frames(task_dir: Path) -> int:
    frame_dir = task_dir / "frames"
    if not frame_dir.is_dir():
        return 0
    return sum(1 for _ in frame_dir.glob("*.jpg"))


def list_frames(task_dir: Path) -> list[dict[str, Any]]:
    frame_dir = task_dir / "frames"
    if not frame_dir.is_dir():
        return []
    frames = []
    for path in sorted(frame_dir.glob("*.jpg")):
        match = _FRAME_NAME_RE.match(path.name)
        entry: dict[str, Any] = {"file": path.name}
        if match:
            if match.group("label"):
                entry.update({"kind": match.group("label"), "step": None, "sub_index": None})
            else:
                entry.update({
                    "kind": match.group("kind"),
                    "step": int(match.group("step")),
                    "sub_index": int(match.group("sub")) if match.group("sub") else None,
                })
        else:
            entry.update({"kind": "unknown", "step": None, "sub_index": None})
        frames.append(entry)
    return frames


def build_task_detail(model: str, task_id: str) -> dict[str, Any] | None:
    task_dir = OUTPUT_ROOT / model / task_id
    if not task_dir.is_dir():
        return None
    run = task_status(task_dir)
    report = _safe_json_load(task_dir / "report.json")
    failure = _safe_json_load(task_dir / "run_failure.json")
    frames = list_frames(task_dir)
    group = _task_group_label(task_id, run.task_type)
    metrics = (report or {}).get("metrics") or {}
    metric_entries = [
        {
            "key": key,
            "label": METRIC_DEFINITIONS.get(key, {}).get("label", key),
            "format": METRIC_DEFINITIONS.get(key, {}).get("format", "text"),
            "description": METRIC_DEFINITIONS.get(key, {}).get("description", ""),
            "value": metrics.get(key),
        }
        for key in _metrics_for_group(group)
        if key in metrics
    ]
    return {
        "model": model,
        "task_id": task_id,
        "status": run.status,
        "outcome": task_outcome(group, run.metrics) if run.status == "completed" else None,
        "task_type": run.task_type,
        "task_group": group,
        "report": report,
        "failure": failure,
        "frames": frames,
        "metric_entries": metric_entries,
        "video_available": (task_dir / "episode.mp4").is_file(),
        "video_url": f"/media/{urllib.parse.quote(model)}/{urllib.parse.quote(task_id)}/episode.mp4",
        "frame_base_url": f"/media/{urllib.parse.quote(model)}/{urllib.parse.quote(task_id)}/frames",
    }


class VisualizationSiteHandler(BaseHTTPRequestHandler):
    server_version = "AgentEvalVisualizationSite/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        pass  # keep stdout clean; flip to `super().log_message(...)` for verbose request logs.

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_not_found(self, message: str = "Not found") -> None:
        self._send_json({"error": message}, status=404)

    def _send_file(self, path: Path, send_body: bool = True) -> None:
        if not path.is_file():
            self._send_not_found(f"File not found: {path.name}")
            return
        content_type, _ = mimetypes.guess_type(str(path))
        content_type = content_type or "application/octet-stream"
        file_size = path.stat().st_size

        # Check for Range request header (needed for <video> playback / seeking).
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            self._send_file_range(path, content_type, file_size, range_header, send_body=send_body)
            return

        # Full file response (no Range header).
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Cache-Control", "no-store")
        if content_type.startswith("video/"):
            self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        if send_body:
            self.wfile.write(path.read_bytes())

    def _send_file_range(self, path: Path, content_type: str, file_size: int,
                         range_header: str, send_body: bool = True) -> None:
        """Serve a partial content response (HTTP 206) for one byte range."""
        range_spec = range_header[len("bytes="):]
        # Parse "start-end" or "start-" or "-suffix".
        try:
            if range_spec.startswith("-"):
                suffix = int(range_spec[1:])
                start = max(0, file_size - suffix)
                end = file_size - 1
            elif range_spec.endswith("-"):
                start = int(range_spec[:-1])
                end = file_size - 1
            else:
                parts = range_spec.split("-", 1)
                start = int(parts[0])
                end = int(parts[1]) if parts[1] else file_size - 1
        except (ValueError, IndexError):
            self._send_file(path, send_body=send_body)  # fallback to full response
            return

        # Clamp to file bounds.
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        length = end - start + 1

        self.send_response(206)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if send_body:
            with open(path, "rb") as f:
                f.seek(start)
                chunk = f.read(length)
            self.wfile.write(chunk)

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        self._handle_get_or_head(send_body=True)

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib method name
        # Some browsers/players probe a <video> src with HEAD before issuing the
        # ranged GET requests that actually stream it; without this the request
        # 501s and the player never attempts to load the video at all.
        self._handle_get_or_head(send_body=False)

    def _handle_get_or_head(self, send_body: bool) -> None:
        parsed = urllib.parse.urlparse(self.path)
        parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]

        try:
            if not parts:
                self._send_file(STATIC_DIR / "index.html", send_body=send_body)
                return

            if parts[0] == "api":
                if not send_body:
                    self._send_headers_only(200, "application/json; charset=utf-8")
                    return
                self._route_api(parts[1:])
                return

            if parts[0] == "3d-tiles":
                # Static tileset files, with the same path-traversal guard as STATIC_DIR.
                if TILESET_DIR is None:
                    self._send_not_found()
                    return
                candidate = TILESET_DIR / Path(*parts[1:])
                resolved = candidate.resolve()
                if TILESET_DIR.resolve() in resolved.parents:
                    self._send_file(candidate, send_body=send_body)
                else:
                    self._send_not_found()
                return

            if parts[0] == "media":
                self._route_media(parts[1:], send_body=send_body)
                return

            # Static assets (styles.css, app.js, ...).
            candidate = STATIC_DIR / Path(*parts)
            resolved = candidate.resolve()
            if STATIC_DIR.resolve() in resolved.parents or resolved == STATIC_DIR.resolve():
                self._send_file(candidate, send_body=send_body)
            else:
                self._send_not_found()
        except Exception as exc:  # noqa: BLE001 - convert any handler bug into a JSON 500
            self._send_json({"error": str(exc)}, status=500)

    def _send_headers_only(self, status: int, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _route_api(self, parts: list[str]) -> None:
        if not parts:
            self._send_not_found("Unknown API route")
            return

        if parts == ["models"]:
            models = list_models()
            overview = []
            for model in models:
                summary = build_model_summary(model)
                overview.append({
                    "model": model,
                    "task_count": summary["task_count"],
                    "completed_count": summary["completed_count"],
                    "failed_count": summary["failed_count"],
                    "run_failed_count": summary["run_failed_count"],
                    "running_count": summary["running_count"],
                    "task_groups": summary["task_groups"],
                })
            self._send_json({"models": overview})
            return

        if len(parts) == 2 and parts[0] == "models":
            model = parts[1]
            if model not in list_models():
                self._send_not_found(f"Unknown model: {model}")
                return
            self._send_json(build_model_summary(model))
            return

        if len(parts) == 4 and parts[0] == "models" and parts[2] == "tasks":
            model, task_id = parts[1], parts[3]
            detail = build_task_detail(model, task_id)
            if detail is None:
                self._send_not_found(f"Unknown task: {model}/{task_id}")
                return
            self._send_json(detail)
            return

        self._send_not_found("Unknown API route")

    def _route_media(self, parts: list[str], send_body: bool = True) -> None:
        if len(parts) < 3:
            self._send_not_found()
            return
        model, task_id, *rest = parts
        task_dir = (OUTPUT_ROOT / model / task_id).resolve()
        if OUTPUT_ROOT.resolve() not in task_dir.parents:
            self._send_not_found()
            return
        target = (task_dir / Path(*rest)).resolve()
        if task_dir not in target.parents and target != task_dir:
            self._send_not_found()
            return
        self._send_file(target, send_body=send_body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the AgentEvaluation visualization site")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # ThreadingHTTPServer already mixes in ThreadingMixIn; it lets simultaneous requests (e.g.
    # the front end loading several frame thumbnails at once) be served concurrently.
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((args.host, args.port), VisualizationSiteHandler)
    print(f"AgentEvaluation visualization site serving on http://{args.host}:{args.port}/")
    print(f"Scanning evaluation output under: {OUTPUT_ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
