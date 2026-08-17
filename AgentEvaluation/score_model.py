"""Summarize every task and metric for one evaluated model."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from benchmark_scoring import (
    QA_REPORT_TASK_TYPES,
    normalize_task_type,
    summarize_score_outcomes,
)

DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output" / "tasks"
STATUS_COMPLETED = "completed"
STATUS_INCOMPLETE = "incomplete"
STATUS_FAILED = "failed"
# QA task reports (LandmarkQA/OrientationQA/SpatialQA) only count as completed once a final
# multiple-choice answer has been recorded. Navigation task reports (ShortNav/LongNav) have no
# such answer field, so completion instead relies solely on the presence of final metrics.
# PlaceSearch is included because its report carries a final judge verdict in the
# "answer" field (found / not_found) just like the four-choice QA reports carry theirs.


def safe_model_directory_name(model: str) -> str:
    safe = "".join(character if character.isalnum() or character in "-_." else "_"
                   for character in model.strip()).strip("._")
    if not safe:
        raise ValueError("--model must contain at least one filesystem-safe character")
    return safe


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def is_metric_value(value: Any) -> bool:
    return isinstance(value, (bool, int, float)) and not (
        isinstance(value, float) and not math.isfinite(value)
    )


def load_task_result(task_dir: Path, expected_model: str) -> dict[str, Any] | None:
    report_path = task_dir / "report.json"
    failure_path = task_dir / "run_failure.json"
    report: dict[str, Any] | None = None
    report_error: str | None = None
    if report_path.is_file():
        try:
            report = read_json(report_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            report_error = f"Invalid report.json: {exc}"

    if report is not None:
        model = str(report.get("model", ""))
        if model and model != expected_model:
            return {
                "task_id": task_dir.name,
                "task_type": normalize_task_type(report.get("task_type"), task_dir.name),
                "status": STATUS_FAILED,
                "model": model,
                "error": f"Report model {model!r} does not match requested model {expected_model!r}",
                "metrics": {},
            }
        metrics = report.get("metrics")
        task_type = normalize_task_type(report.get("task_type"), task_dir.name)
        if task_type in QA_REPORT_TASK_TYPES:
            completed = isinstance(metrics, dict) and report.get("answer") is not None
        else:
            completed = isinstance(metrics, dict) and len(metrics) > 0
        result = {
            "task_id": str(report.get("task_id", task_dir.name)),
            "task_type": task_type,
            "status": STATUS_COMPLETED if completed else STATUS_INCOMPLETE,
            "model": model or expected_model,
            "question": report.get("question") or report.get("instructions"),
            "task_completed": report.get("task_completed"),
            "steps_completed": report.get("steps_completed", 0),
            "completion_step": report.get("completion_step"),
            "completion_elapsed_seconds": report.get("completion_elapsed_seconds"),
            "completion_event": report.get("completion_event"),
            "agent_terminated": report.get("agent_terminated"),
            "agent_termination_step": report.get("agent_termination_step"),
            "agent_termination_elapsed_seconds": report.get(
                "agent_termination_elapsed_seconds"
            ),
            "steps_completed_at_termination": report.get(
                "steps_completed_at_termination"
            ),
            "configured_max_steps": (report.get("hyperparameters") or {}).get("max_steps"),
            "answer": (report.get("answer") or {}).get("answer"),
            "metrics": metrics if isinstance(metrics, dict) else {},
            "report_path": str(report_path),
            "video_path": report.get("video_path"),
            "video_exists": bool(report.get("video_path") and Path(report["video_path"]).is_file()),
        }
        if not completed:
            result["error"] = "Task report is partial: final answer or metrics are missing"
        return result

    if failure_path.is_file():
        try:
            failure = read_json(failure_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failure = {"error": f"Invalid run_failure.json: {exc}"}
        return {
            "task_id": str(failure.get("task_id", task_dir.name)),
            "task_type": normalize_task_type(failure.get("task_type"), task_dir.name),
            "status": STATUS_FAILED,
            "model": str(failure.get("model", expected_model)),
            "task_completed": failure.get("task_completed"),
            "steps_completed": failure.get("steps_completed"),
            "completion_step": failure.get("completion_step"),
            "completion_elapsed_seconds": failure.get("completion_elapsed_seconds"),
            "completion_event": failure.get("completion_event"),
            "agent_terminated": failure.get("agent_terminated"),
            "agent_termination_step": failure.get("agent_termination_step"),
            "agent_termination_elapsed_seconds": failure.get(
                "agent_termination_elapsed_seconds"
            ),
            "steps_completed_at_termination": failure.get(
                "steps_completed_at_termination"
            ),
            "error": failure.get("error", report_error or "Task failed"),
            "elapsed_seconds": failure.get("elapsed_seconds"),
            "metrics": {},
            "failure_path": str(failure_path),
        }

    if report_error:
        return {
            "task_id": task_dir.name,
            "task_type": "Unknown",
            "status": STATUS_FAILED,
            "model": expected_model,
            "error": report_error,
            "metrics": {},
        }
    return None


def summarize_metric(values: list[bool | int | float]) -> dict[str, Any]:
    numeric = [float(value) for value in values]
    return {
        "count": len(values),
        "mean": round(statistics.fmean(numeric), 6),
        "median": round(statistics.median(numeric), 6),
        "min": min(values),
        "max": max(values),
        "sum": round(sum(numeric), 6),
    }


def summarize_group(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [result for result in results if result["status"] == STATUS_COMPLETED]
    metric_values: dict[str, list[bool | int | float]] = defaultdict(list)
    for result in completed:
        for name, value in result["metrics"].items():
            if is_metric_value(value):
                metric_values[name].append(value)
    score_outcomes = summarize_score_outcomes(results)
    remaining_ratios = [result["metrics"]["remaining_distance_ratio"] for result in completed
                        if is_metric_value(result["metrics"].get("remaining_distance_ratio"))]
    return {
        "task_count": len(results),
        "completed_count": len(completed),
        "incomplete_count": sum(result["status"] == STATUS_INCOMPLETE for result in results),
        "failed_count": sum(result["status"] == STATUS_FAILED for result in results),
        "completion_rate": round(len(completed) / len(results), 6) if results else None,
        **score_outcomes,
        # Compatibility alias: "all tasks" now means all tasks in the QA score family.
        "accuracy_all_tasks": score_outcomes["accuracy"],
        # Compatibility alias: denominator is every navigation-family attempt, including Error.
        "navigation_arrival_rate_all_tasks": score_outcomes["navigation_arrival_rate"],
        "navigation_mean_remaining_distance_ratio": round(statistics.fmean(remaining_ratios), 6)
        if remaining_ratios else None,
        "metrics": {name: summarize_metric(values) for name, values in sorted(metric_values.items())},
    }


def build_statistics(model: str, model_dir: Path) -> dict[str, Any]:
    results = []
    for task_dir in sorted(path for path in model_dir.iterdir() if path.is_dir()):
        result = load_task_result(task_dir, model)
        if result is not None:
            results.append(result)
    if not results:
        raise ValueError(f"No task reports or failures found in {model_dir}")
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_type[str(result.get("task_type", "Unknown"))].append(result)
    return {
        "model": model,
        "model_output_dir": str(model_dir),
        "overall": summarize_group(results),
        "by_task_type": {name: summarize_group(items) for name, items in sorted(by_type.items())},
        "tasks": results,
    }


def write_task_csv(statistics_data: dict[str, Any], path: Path) -> None:
    tasks = statistics_data["tasks"]
    metric_names = sorted({name for task in tasks for name in task.get("metrics", {})})
    columns = [
        "task_id", "task_type", "status", "model", "task_completed", "steps_completed",
        "completion_step", "completion_elapsed_seconds", "completion_event",
        "agent_terminated", "agent_termination_step", "agent_termination_elapsed_seconds",
        "steps_completed_at_termination", "configured_max_steps", "answer", "error",
        "report_path", "video_path", "video_exists",
    ] + metric_names
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for task in tasks:
            row = {column: task.get(column) for column in columns}
            row.update(task.get("metrics", {}))
            writer.writerow(row)


def print_summary(data: dict[str, Any], json_path: Path, csv_path: Path) -> None:
    overall = data["overall"]
    print(f"Model: {data['model']}")
    print(f"Tasks: {overall['task_count']} total, {overall['completed_count']} completed, "
          f"{overall['incomplete_count']} incomplete, {overall['failed_count']} failed")
    print(f"Completion rate: {overall['completion_rate']}")
    print(f"Success rate (Error/incomplete count as unsuccessful): "
          f"{overall['success_count']}/{overall['task_count']} = {overall['success_rate']}")
    print(f"QA accuracy (Error/incomplete count as incorrect): "
          f"{overall['accuracy_correct_count']}/{overall['accuracy_denominator']} = "
          f"{overall['accuracy']}")
    print(f"Navigation arrival rate (Error/incomplete count as not arrived): "
          f"{overall['navigation_arrival_count']}/{overall['navigation_denominator']} = "
          f"{overall['navigation_arrival_rate']}")
    print(f"QA accuracy (completed/observed only; diagnostic): "
          f"{overall['accuracy_completed_only']}")
    print(f"Navigation arrival rate (completed/observed only; diagnostic): "
          f"{overall['navigation_arrival_rate_completed_only']}")
    print(f"Navigation mean remaining-distance ratio: {overall['navigation_mean_remaining_distance_ratio']}")
    for task_type, summary in data["by_task_type"].items():
        if summary["accuracy"] is not None:
            print(f"  {task_type}: {summary['completed_count']}/{summary['task_count']} completed, "
                  f"accuracy={summary['accuracy_correct_count']}/"
                  f"{summary['accuracy_denominator']} = {summary['accuracy']}")
        elif summary["navigation_arrival_rate"] is not None:
            print(f"  {task_type}: {summary['completed_count']}/{summary['task_count']} completed, "
                  f"arrival_rate={summary['navigation_arrival_count']}/"
                  f"{summary['navigation_denominator']} = "
                  f"{summary['navigation_arrival_rate']}, "
                  f"mean_remaining_distance_ratio={summary['navigation_mean_remaining_distance_ratio']}")
        else:
            print(f"  {task_type}: {summary['completed_count']}/{summary['task_count']} completed, "
                  f"success_rate={summary['success_rate']}")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score all recorded metrics for one model")
    parser.add_argument("--model", required=True, help="Exact model name used by run_task.py")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT,
                        help="Root containing model-specific task output directories")
    parser.add_argument("--result-json", type=Path,
                        help="Optional statistics JSON path (default: MODEL_DIR/model_scores.json)")
    parser.add_argument("--result-csv", type=Path,
                        help="Optional per-task CSV path (default: MODEL_DIR/task_scores.csv)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = args.output_root.resolve() / safe_model_directory_name(args.model)
    if not model_dir.is_dir():
        raise FileNotFoundError(f"Model output directory not found: {model_dir}")
    data = build_statistics(args.model, model_dir)
    json_path = args.result_json.resolve() if args.result_json else model_dir / "model_scores.json"
    csv_path = args.result_csv.resolve() if args.result_csv else model_dir / "task_scores.csv"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_task_csv(data, csv_path)
    print_summary(data, json_path, csv_path)


if __name__ == "__main__":
    main()
