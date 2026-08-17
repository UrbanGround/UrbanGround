"""Compare every evaluated model's score across all task types.

Failed runs (missing report, crashed episode, invalid report.json, ...) count as unsuccessful
in score and completion-rate denominators. For every ratio, both the numerator and denominator
are printed alongside the percentage, e.g. "74/80 (92.5%)".

Usage:
    python3 AgentEvaluation/compare_models.py
    python3 AgentEvaluation/compare_models.py --models gpt-5.4 aws.claude-opus-4.6
    python3 AgentEvaluation/compare_models.py --output-root AgentEvaluation/output/tasks
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark_scoring import result_score_kind, summarize_score_outcomes
from score_model import (
    DEFAULT_OUTPUT_ROOT,
    STATUS_COMPLETED,
    STATUS_FAILED,
    build_statistics,
    safe_model_directory_name,
)

DEFAULT_JSON_PATH = Path(__file__).resolve().parent / "output" / "all_models_comparison.json"
DEFAULT_CSV_PATH = Path(__file__).resolve().parent / "output" / "all_models_comparison.csv"


def discover_models(output_root: Path) -> list[str]:
    """Return every model directory name found under output_root, sorted alphabetically."""
    if not output_root.is_dir():
        raise FileNotFoundError(f"Output root not found: {output_root}")
    return sorted(path.name for path in output_root.iterdir() if path.is_dir())


def fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "ratio": round(numerator / denominator, 6) if denominator else None,
    }


def format_fraction(data: dict[str, Any] | None, as_percent: bool = True) -> str:
    if not data or not data["denominator"]:
        return "-"
    if data["ratio"] is None:
        return f"{data['numerator']}/{data['denominator']}"
    if as_percent:
        return f"{data['numerator']}/{data['denominator']} ({data['ratio'] * 100:.1f}%)"
    return f"{data['numerator']}/{data['denominator']} ({data['ratio']:.4f})"


def summarize_for_comparison(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build fractions with every attempted run in the denominator.

    A completed task contributes its boolean outcome. Incomplete and failed runs contribute
    zero, so infrastructure/model protocol errors cannot inflate model scores by disappearing.
    """
    completed = [result for result in results if result["status"] == STATUS_COMPLETED]
    failed_count = sum(result["status"] == STATUS_FAILED for result in results)

    score_outcomes = summarize_score_outcomes(results)
    score_kinds = {
        kind for result in results if (kind := result_score_kind(result)) is not None
    }
    score = fraction(score_outcomes["success_count"], len(results))
    if score_kinds == {"accuracy"}:
        score_kind = "accuracy"
    elif score_kinds == {"arrival_rate"}:
        score_kind = "arrival_rate"
    elif score_kinds:
        score_kind = "success_rate"
    else:
        score_kind = None

    return {
        "task_count": len(results),
        "failed_count": failed_count,
        "valid_count": len(results),
        "completion": fraction(len(completed), len(results)),
        "score": score,
        "score_kind": score_kind,
    }


def build_comparison(models: list[str], output_root: Path) -> dict[str, Any]:
    per_model: dict[str, dict[str, Any]] = {}
    task_types: set[str] = set()
    for model in models:
        model_dir = output_root / safe_model_directory_name(model)
        data = build_statistics(model, model_dir)
        per_model[model] = data
        task_types.update(data["by_task_type"].keys())

    overall: dict[str, Any] = {}
    by_task_type: dict[str, dict[str, Any]] = {name: {} for name in sorted(task_types)}
    for model, data in per_model.items():
        overall[model] = summarize_for_comparison(data["tasks"])
        for task_type in by_task_type:
            group_results = [task for task in data["tasks"] if task.get("task_type") == task_type]
            by_task_type[task_type][model] = summarize_for_comparison(group_results) if group_results else None

    return {
        "models": models,
        "task_types": sorted(task_types),
        "overall": overall,
        "by_task_type": by_task_type,
    }


def write_csv(comparison: dict[str, Any], path: Path) -> None:
    models = comparison["models"]
    lines = ["task_type," + ",".join(models)]

    def row(label: str, values: dict[str, dict[str, Any] | None], key: str) -> str:
        cells = []
        for model in models:
            entry = values.get(model)
            cells.append(format_fraction(entry[key]) if entry else "-")
        return label + "," + ",".join(cells)

    lines.append(row("Overall (completion)", comparison["overall"], "completion"))
    lines.append(row("Overall (score)", comparison["overall"], "score"))
    for task_type in comparison["task_types"]:
        lines.append(row(task_type, comparison["by_task_type"][task_type], "score"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_comparison(comparison: dict[str, Any]) -> None:
    models = comparison["models"]
    header = f"{'Task Type':<16}" + "".join(f"{model:>28}" for model in models)
    print(header)
    print("-" * len(header))

    def print_row(label: str, values: dict[str, dict[str, Any] | None], key: str) -> None:
        cells = []
        for model in models:
            entry = values.get(model)
            cells.append(format_fraction(entry[key]) if entry else "-")
        print(f"{label:<16}" + "".join(f"{cell:>28}" for cell in cells))

    print_row("Completion", comparison["overall"], "completion")
    print_row("Score", comparison["overall"], "score")
    print("-" * len(header))
    for task_type in comparison["task_types"]:
        print_row(task_type, comparison["by_task_type"][task_type], "score")
    print()
    for model in models:
        failed = comparison["overall"][model]["failed_count"]
        total = comparison["overall"][model]["task_count"]
        print(f"{model}: {failed}/{total} run(s) failed and counted as unsuccessful above")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare score/completion across all evaluated models")
    parser.add_argument("--models", nargs="+",
                        help="Model names to compare (default: every directory under --output-root)")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT,
                        help="Root containing model-specific task output directories")
    parser.add_argument("--result-json", type=Path, default=DEFAULT_JSON_PATH)
    parser.add_argument("--result-csv", type=Path, default=DEFAULT_CSV_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = args.output_root.resolve()
    models = args.models or discover_models(output_root)
    if not models:
        raise ValueError(f"No model directories found under {output_root}")

    comparison = build_comparison(models, output_root)
    print_comparison(comparison)

    json_path = args.result_json.resolve()
    csv_path = args.result_csv.resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(comparison, csv_path)
    print(f"\nJSON: {json_path}")
    print(f"CSV:  {csv_path}")


if __name__ == "__main__":
    main()
