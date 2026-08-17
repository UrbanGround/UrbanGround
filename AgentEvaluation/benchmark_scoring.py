"""Dependency-free benchmark outcome classification and score denominators."""

from __future__ import annotations

from typing import Any, Sequence


TASK_TYPE_NAMES = {
    0: "ShortNav", 2: "LongNav", 3: "PlaceSearch", 5: "ScheduleWindowNav",
    7: "LandmarkQA", 8: "OrientationQA", 9: "SpatialQA", 10: "InstructionNav",
    11: "ConstrainedNav", 12: "DynamicClosureNav", 13: "MultipointNav",
}
CONDITION_TASK_TYPE_NAMES = {
    "TSQ": "ThunderstormQA", "TSN": "ThunderstormNav",
    "OCQ": "OvercastQA", "OCN": "OvercastNav",
    "CLQ": "CloudyQA", "CLN": "CloudyNav",
    "EVQ": "DuskQA", "EVN": "DuskNav",
    "NTQ": "NightQA", "NTN": "NightNav",
}
PREFIX_TASK_TYPE_NAMES = {
    **CONDITION_TASK_TYPE_NAMES,
    "RQ": "RainExplorationQA",
    "RN": "RainShortNav",
    "PD": "PedestrianShortNav",
    "PL": "PedestrianLongNav",
    "DCR": "DynamicClosureNav",
    "II": "ImplicitIntentNav",
}
QA_REPORT_TASK_TYPES = {
    "LandmarkQA", "OrientationQA", "SpatialQA", "PlaceSearch", "RainExplorationQA",
    *(name for prefix, name in CONDITION_TASK_TYPE_NAMES.items() if prefix.endswith("Q")),
}
NAVIGATION_REPORT_TASK_TYPES = {
    "ShortNav", "LongNav", "ScheduleWindowNav", "InstructionNav", "ConstrainedNav",
    "DynamicClosureNav", "ImplicitIntentNav", "MultipointNav", "RainShortNav",
    "PedestrianShortNav", "PedestrianLongNav",
    *(name for prefix, name in CONDITION_TASK_TYPE_NAMES.items() if prefix.endswith("N")),
}
QA_TASK_ID_PREFIXES = {
    "LQ", "OQ", "SQ", "PS", "RQ",
    *(prefix for prefix in CONDITION_TASK_TYPE_NAMES if prefix.endswith("Q")),
}
NAVIGATION_TASK_ID_PREFIXES = {
    "SN", "LN", "SF", "IN", "CN", "DCR", "II", "MP", "RN", "PD", "PL",
    *(prefix for prefix in CONDITION_TASK_TYPE_NAMES if prefix.endswith("N")),
}


def normalize_task_type(value: Any, task_id: Any = None) -> str:
    """Normalize report/failure task types, using ID prefixes for reused numeric types."""
    task_id = str(task_id or "")
    prefix = task_id.split("-", 1)[0].upper()
    if prefix in PREFIX_TASK_TYPE_NAMES:
        return PREFIX_TASK_TYPE_NAMES[prefix]
    if isinstance(value, str) and value and not value.isdigit():
        return value
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return str(value) if value not in (None, "") else "Unknown"
    return TASK_TYPE_NAMES.get(numeric, f"TaskType-{numeric}")


def result_score_kind(result: dict[str, Any]) -> str | None:
    """Return the score family even when an Error result has no metrics/report."""
    metrics = result.get("metrics")
    if isinstance(metrics, dict):
        if "answer_correct" in metrics:
            return "accuracy"
        if "reached_destination" in metrics:
            return "arrival_rate"

    task_id = str(result.get("task_id") or "")
    prefix = task_id.split("-", 1)[0].upper()
    task_type = normalize_task_type(result.get("task_type"), task_id)
    if task_type in QA_REPORT_TASK_TYPES or prefix in QA_TASK_ID_PREFIXES:
        return "accuracy"
    if task_type in NAVIGATION_REPORT_TASK_TYPES or prefix in NAVIGATION_TASK_ID_PREFIXES:
        return "arrival_rate"
    return None


def summarize_score_outcomes(
    results: Sequence[dict[str, Any]], completed_status: str = "completed"
) -> dict[str, Any]:
    """Compute canonical scores with Error/incomplete attempts contributing zero."""
    completed = [
        result for result in results
        if str(result.get("status", "")).lower() == completed_status
    ]
    accuracy_results = [result for result in results if result_score_kind(result) == "accuracy"]
    navigation_results = [
        result for result in results if result_score_kind(result) == "arrival_rate"
    ]
    answer_values = [
        bool(result["metrics"]["answer_correct"])
        for result in completed
        if result_score_kind(result) == "accuracy"
        and isinstance(result.get("metrics"), dict)
        and "answer_correct" in result["metrics"]
    ]
    arrival_values = [
        bool(result["metrics"]["reached_destination"])
        for result in completed
        if result_score_kind(result) == "arrival_rate"
        and isinstance(result.get("metrics"), dict)
        and "reached_destination" in result["metrics"]
    ]
    accuracy_correct_count = int(sum(answer_values))
    navigation_arrival_count = int(sum(arrival_values))
    success_count = accuracy_correct_count + navigation_arrival_count
    return {
        "success_count": success_count,
        "success_rate": round(success_count / len(results), 6) if results else None,
        "accuracy": (
            round(accuracy_correct_count / len(accuracy_results), 6)
            if accuracy_results else None
        ),
        "accuracy_correct_count": accuracy_correct_count,
        "accuracy_denominator": len(accuracy_results),
        "accuracy_completed_only": (
            round(accuracy_correct_count / len(answer_values), 6) if answer_values else None
        ),
        "accuracy_observed_count": len(answer_values),
        "navigation_arrival_rate": (
            round(navigation_arrival_count / len(navigation_results), 6)
            if navigation_results else None
        ),
        "navigation_arrival_count": navigation_arrival_count,
        "navigation_denominator": len(navigation_results),
        "navigation_arrival_rate_completed_only": (
            round(navigation_arrival_count / len(arrival_values), 6)
            if arrival_values else None
        ),
        "navigation_observed_count": len(arrival_values),
        "unclassified_score_count": (
            len(results) - len(accuracy_results) - len(navigation_results)
        ),
    }
