"""Run one or more UrbanBench tasks against a packaged UrbanGround build."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import statistics
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api import LLMClient, LLMConfig
from benchmark_scoring import summarize_score_outcomes
from sandbox import (
    AgentClient,
    SandboxSession,
    default_build_folder,
    launch_build,
    task_directory_for_build,
)
from task_variants import TaskRunSpec, expand_all_task_runs, task_run_from_path
from tasks import TaskEpisodeConfig, create_evaluator, load_task_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "tasks"
EXE_BOOT_WAIT_S = 600
DEFAULT_MAX_WORKERS = 1
DEFAULT_SERVER_URL = "http://127.0.0.1:8081"
# 7/8/9 = LandmarkQA/OrientationQA/SpatialQA (four-choice QA);
# 0/2/10 = ShortNav/LongNav/InstructionNav (navigation);
# 3 = PlaceSearch (PS task IDs, find and reach a requested place type);
# 5 = ScheduleWindowNav (SF task IDs, ordered appointments with time windows);
# 11 = ConstrainedNav (CN task IDs, road closures disclosed up front);
# 12 is shared by DynamicClosureNav (CN task IDs, dynamically disclosed closures) and
# ImplicitIntentNav (II task IDs, infer a destination POI from an everyday-life goal);
# 13 = MultipointNav (MP task IDs, visit several unordered targets on a self-planned route).
SUPPORTED_TYPES = {0, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13}
LIFECYCLE_RESULT_FIELDS = (
    "task_completed",
    "steps_completed",
    "completion_step",
    "completion_elapsed_seconds",
    "completion_event",
    "agent_terminated",
    "agent_termination_step",
    "agent_termination_elapsed_seconds",
    "steps_completed_at_termination",
)

log = logging.getLogger("run_task")
_write_lock = threading.Lock()


@dataclass(frozen=True)
class RunOptions:
    model: str
    max_steps: int
    build_folder: Path
    exe_path: str | None
    server_url: str
    exe_boot_wait: float
    post_teleport_wait: float
    output_dir: Path
    attach: bool
    save_frames: bool
    save_video: bool
    video_fps: float
    action_sample_interval: float
    scene_ready_poll: bool = True
    scene_poll_interval: float = 5.0
    scene_ready_consecutive_checks: int = 2
    scene_edge_density_threshold: float = 0.010


def safe_model_directory_name(model: str) -> str:
    """Convert an API model identifier to a stable single directory name."""
    safe = "".join(character if character.isalnum() or character in "-_." else "_"
                   for character in model.strip())
    safe = safe.strip("._")
    if not safe:
        raise ValueError("--model must contain at least one filesystem-safe character")
    return safe


def resolve_task_path(value: str, task_dir: Path) -> Path:
    value_path = Path(value)
    if value_path.is_absolute() or value_path.parent != Path("."):
        raise ValueError(
            "Tasks must be selected by ID or filename from the task directory bundled "
            "with --build-folder"
        )
    candidate = task_dir / (value if value.endswith(".json") else f"{value}.json")
    if candidate.is_file():
        return candidate.resolve()
    raise FileNotFoundError(f"Task file not found: {value}")


def resolve_task_paths(values: list[str], task_glob: str | None, task_dir: Path,
                       run_all: bool = False) -> list[Path]:
    selection_count = int(bool(values)) + int(bool(task_glob)) + int(run_all)
    if selection_count > 1:
        raise ValueError(
            "Use only one task selection mode: task IDs/filenames, --task-glob, or --all"
        )

    paths: list[Path] = []
    if run_all:
        for path in sorted(task_dir.glob("*.json")):
            try:
                task = load_task_file(path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                log.warning("Skipping invalid task file %s: %s", path, exc)
                continue
            if int(task.get("type", -1)) in SUPPORTED_TYPES:
                paths.append(path)
    elif task_glob:
        paths.extend(sorted(task_dir.glob(task_glob)))
    paths.extend(resolve_task_path(value, task_dir) for value in values)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    if not unique:
        raise ValueError("Provide at least one task, --task-glob, or --all")
    return unique


def resolve_task_runs(values: list[str], task_glob: str | None, task_dir: Path,
                      run_all: bool = False) -> list[TaskRunSpec]:
    """Resolve CLI selection and fully expand reusable variants for ``--all`` only."""
    paths = resolve_task_paths(values, task_glob, task_dir, run_all)
    if run_all:
        return expand_all_task_runs(paths, load_task_file, SUPPORTED_TYPES)
    return [task_run_from_path(path, load_task_file) for path in paths]


def is_task_already_completed(task_id: str, output_dir: Path) -> bool:
    """True iff a previous run of `task_id` in `output_dir` finished successfully.

    "Successfully" means report.json exists with a non-null "metrics" object -- the same
    condition the visualization site uses to color a task green. A stray run_failure.json (a
    retry that failed *after* an earlier success had already been written) still counts the
    task as completed, since report.json reflects the most recent full run_one_task() attempt
    and is only ever written on success; failed attempts never touch report.json.
    """
    report_path = output_dir / task_id / "report.json"
    if not report_path.is_file():
        return False
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return report.get("metrics") is not None


def lifecycle_result_fields(report: dict[str, Any]) -> dict[str, Any]:
    """Copy standardized episode lifecycle fields into each batch-report result."""
    return {field: report.get(field) for field in LIFECYCLE_RESULT_FIELDS}


def load_completed_result(task_run: TaskRunSpec, model: str, max_steps: int,
                          output_dir: Path) -> dict[str, Any]:
    """Rebuild a run_one_task()-shaped "completed" result straight from a prior report.json.

    Lets the default skip-already-completed behavior fold previously-finished tasks back into
    aggregate_results()/the batch report without re-running them, so batch_report.json still
    reflects every task in the requested selection rather than only the ones actually
    (re-)executed this invocation.
    """
    task_id = task_run.task_id
    task_dir = output_dir / task_id
    report = json.loads((task_dir / "report.json").read_text(encoding="utf-8"))
    answer = report.get("answer")
    return {
        "status": "completed",
        "task_id": task_id,
        "task_type": report["task_type"],
        "model": model,
        "max_steps": max_steps,
        "task_path": str(task_run.task_path),
        "source_task_id": task_run.source_task_id,
        "generated_variant": task_run.generated_variant,
        "worker_thread": None,
        "sandbox_session_id": None,
        "elapsed_seconds": 0.0,
        "answer": answer["answer"] if isinstance(answer, dict) and "answer" in answer else None,
        **lifecycle_result_fields(report),
        "metrics": report["metrics"],
        "report_path": str(task_dir / "report.json"),
        "video_path": report.get("video_path"),
        "video_frame_count": report.get("video_frame_count", 0),
        "skipped": True,
    }


def run_one_task(task_run: TaskRunSpec | Path, options: RunOptions) -> dict[str, Any]:
    started = time.monotonic()
    if isinstance(task_run, Path):
        task_run = task_run_from_path(task_run, load_task_file)
    task_path = task_run.task_path
    task = task_run.task
    task_id = str(task["id"])
    if int(task["type"]) not in SUPPORTED_TYPES:
        raise ValueError(f"Task {task_id} has unsupported type {task['type']}")
    config = TaskEpisodeConfig(
        max_steps=options.max_steps,
        post_teleport_wait_seconds=options.post_teleport_wait,
        save_frames=options.save_frames,
        save_video=options.save_video,
        video_fps=options.video_fps,
        action_sample_interval_seconds=options.action_sample_interval,
        output_dir=options.output_dir,
        scene_ready_poll_enabled=options.scene_ready_poll,
        scene_poll_interval_seconds=options.scene_poll_interval,
        scene_ready_consecutive_checks=options.scene_ready_consecutive_checks,
        scene_edge_density_threshold=options.scene_edge_density_threshold,
    )
    evaluator = None
    session_id = None
    worker_thread = threading.current_thread().name
    log.info("[%s] Worker %s is starting an evaluation episode", task_id, worker_thread)
    try:
        llm = LLMClient(LLMConfig.from_env(model=options.model))
        with SandboxSession(attach=options.attach) as session:
            session_id = str(session.session_id)
            if not options.attach:
                launch_build(session, options.build_folder, options.exe_path)
            client = AgentClient(options.server_url)
            client.wait_until_ready(options.exe_boot_wait)
            evaluator = create_evaluator(task, client, llm, config)
            report = evaluator.run()
        answer = report.get("answer")
        return {
            "status": "completed",
            "task_id": task_id,
            "task_type": report["task_type"],
            "model": options.model,
            "max_steps": options.max_steps,
            "task_path": str(task_path),
            "source_task_id": task_run.source_task_id,
            "generated_variant": task_run.generated_variant,
            "worker_thread": worker_thread,
            "sandbox_session_id": session_id,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "answer": answer["answer"] if isinstance(answer, dict) and "answer" in answer else None,
            **lifecycle_result_fields(report),
            "metrics": report["metrics"],
            "report_path": str(evaluator.report_path),
            "video_path": report.get("video_path"),
            "video_frame_count": report.get("video_frame_count", 0),
        }
    except Exception as exc:
        lifecycle = (
            evaluator.episode_summary() if evaluator is not None
            else {field: None for field in LIFECYCLE_RESULT_FIELDS}
        )
        failure = {
            "status": "failed",
            "task_id": task_id,
            "task_type": task.get("type"),
            "model": options.model,
            "max_steps": options.max_steps,
            "task_path": str(task_path),
            "source_task_id": task_run.source_task_id,
            "generated_variant": task_run.generated_variant,
            "worker_thread": worker_thread,
            "sandbox_session_id": session_id,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            **lifecycle,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        failure_dir = options.output_dir / task_id
        failure_dir.mkdir(parents=True, exist_ok=True)
        (failure_dir / "run_failure.json").write_text(
            json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log.exception("[%s] Task failed", task_id)
        return failure


def aggregate_results(results: list[dict[str, Any]], model: str, max_steps: int,
                      max_workers: int, elapsed_seconds: float) -> dict[str, Any]:
    completed = [result for result in results if result["status"] == "completed"]
    failed = [result for result in results if result["status"] == "failed"]
    metric_names = sorted({
        name for result in completed for name, value in result.get("metrics", {}).items()
        if isinstance(value, (int, float, bool)) and value is not None
    })
    metric_summary: dict[str, Any] = {}
    for name in metric_names:
        values = [result["metrics"][name] for result in completed
                  if isinstance(result["metrics"].get(name), (int, float, bool))]
        numeric = [float(value) for value in values]
        metric_summary[name] = {
            "count": len(values),
            "mean": round(statistics.fmean(numeric), 6) if numeric else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "sum": round(sum(numeric), 6) if numeric else None,
        }
    # Every requested task in the relevant family is a denominator observation. Completed
    # tasks contribute their boolean metric; Error/partial tasks contribute zero.
    score_outcomes = summarize_score_outcomes(results)
    # Only ConstrainedNav/DynamicClosureNav (CN task IDs) report `closure_violated`; II reports
    # use the generic navigation arrival metrics instead. An Error does not imply a closure
    # violation, so this diagnostic keeps its observed-metric denominator.
    closure_violations = [bool(result["metrics"]["closure_violated"]) for result in completed
                          if "closure_violated" in result.get("metrics", {})]
    return {
        "model": model,
        "hyperparameters": {
            "model": model,
            "max_steps": max_steps,
            "max_workers": max_workers,
        },
        "task_count": len(results),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "max_workers": max_workers,
        "elapsed_seconds": round(elapsed_seconds, 3),
        **score_outcomes,
        "closure_violation_rate": (
            round(sum(closure_violations) / len(closure_violations), 6) if closure_violations else None
        ),
        "metric_summary": metric_summary,
        "results": results,
    }


def write_batch_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "batch_report.json"
    with _write_lock:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def execute_task_runs(
    task_runs: list[TaskRunSpec],
    prior_results: list[dict[str, Any]],
    total_task_count: int,
    options: RunOptions,
    max_workers: int,
) -> tuple[dict[str, Any], Path, int]:
    """Execute a task selection while one UrbanGround application remains available."""
    results = list(prior_results)
    started = time.monotonic()
    worker_count = min(max_workers, len(task_runs)) if task_runs else max_workers
    if task_runs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(run_one_task, task_run, options): task_run
                for task_run in task_runs
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                report = aggregate_results(
                    results, options.model, options.max_steps, worker_count,
                    time.monotonic() - started,
                )
                write_batch_report(report, options.output_dir)
                log.info(
                    "Batch progress: %d/%d complete (%s)",
                    len(results), total_task_count, result["task_id"],
                )
    results.sort(key=lambda item: item["task_id"])
    report = aggregate_results(
        results, options.model, options.max_steps, worker_count, time.monotonic() - started
    )
    report_path = write_batch_report(report, options.output_dir)
    return report, report_path, worker_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate UrbanBench tasks in UrbanGround")
    parser.add_argument(
        "tasks", nargs="*",
        help="Task IDs or filenames from the task directory bundled with the selected build",
    )
    parser.add_argument(
        "--task-glob", help="Glob within the packaged task directory, for example 'OQ-*.json'"
    )
    parser.add_argument("--all", action="store_true",
                        help="Run every supported base task and fully expand the current "
                             "dynamic-closure, pedestrian-long-nav, weather, and time-of-day "
                             "reuse variants")
    parser.add_argument("--model", default=None,
                        help="Model API identifier (default: AGENT_MODEL or gpt-4.1)")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS,
                        help="Local application workers; currently fixed at 1")
    parser.add_argument("--max-steps", type=int, default=12,
                        help="Maximum embodied exploration steps per task (default: 12)")
    parser.add_argument(
        "--build-folder", type=Path,
        help="Packaged build directory (default: Builds/macOS or Builds/Windows for this host)",
    )
    parser.add_argument(
        "--exe-path",
        help="Executable or .app path relative to --build-folder (default: inferred)",
    )
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--exe-boot-wait", type=float, default=EXE_BOOT_WAIT_S)
    parser.add_argument("--post-teleport-wait", type=float, default=EXE_BOOT_WAIT_S)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--attach", action="store_true",
                        help="Connect to an already running UrbanGround application")
    parser.add_argument("--force-rerun", action="store_true",
                        help="By default, tasks that already have a successful report.json "
                             "(non-null metrics) in --output-dir/<model>/<task_id>/ are skipped "
                             "and only previously-failed or never-evaluated tasks are (re-)run. "
                             "Pass --force-rerun to re-run every selected task regardless.")
    parser.add_argument("--save-frames", action="store_true",
                        help="Keep source JPEG frames after encoding (default: video only)")
    parser.add_argument("--no-save-video", action="store_true")
    parser.add_argument("--video-fps", type=float, default=4.0)
    parser.add_argument("--action-sample-interval", type=float, default=0.3)
    parser.add_argument("--no-scene-ready-poll", action="store_true",
                        help="Disable adaptive scene-load polling; always sleep the full "
                             "--post-teleport-wait like before (fixed wait).")
    parser.add_argument("--scene-poll-interval", type=float, default=5.0,
                        help="Seconds between screenshot polls while waiting for map/terrain "
                             "tiles to finish streaming in after a teleport (default: 5.0)")
    parser.add_argument("--scene-ready-consecutive-checks", type=int, default=2,
                        help="Number of consecutive 'loaded' polls required before proceeding, "
                             "to debounce one lucky frame (default: 2)")
    parser.add_argument("--scene-edge-density-threshold", type=float, default=0.010,
                        help="Canny edge-density threshold above which a screenshot is "
                             "considered fully loaded (default: 0.010; see tasks/scene_readiness.py)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    build_folder = (
        args.build_folder.resolve()
        if args.build_folder is not None
        else default_build_folder(PROJECT_ROOT).resolve()
    )
    task_dir = task_directory_for_build(build_folder)
    task_runs = resolve_task_runs(args.tasks, args.task_glob, task_dir, args.all)
    if args.all:
        generated_count = sum(task_run.generated_variant for task_run in task_runs)
        log.info("--all selected %d tasks: %d base tasks + %d generated reuse variants",
                 len(task_runs), len(task_runs) - generated_count, generated_count)
    if args.max_steps < 1:
        raise ValueError("--max-steps must be at least 1")
    if not 1 <= args.max_workers <= DEFAULT_MAX_WORKERS:
        raise ValueError(f"--max-workers must be between 1 and {DEFAULT_MAX_WORKERS}")
    if args.video_fps <= 0 or args.action_sample_interval <= 0:
        raise ValueError("Video FPS and action sample interval must be positive")
    model = args.model or LLMConfig.from_env().model
    model_output_dir = args.output_dir.resolve() / safe_model_directory_name(model)

    results: list[dict[str, Any]] = []
    total_task_count = len(task_runs)
    if not args.force_rerun:
        remaining_runs = []
        for task_run in task_runs:
            task_id = task_run.task_id
            if is_task_already_completed(task_id, model_output_dir):
                results.append(load_completed_result(
                    task_run, model, args.max_steps, model_output_dir
                ))
            else:
                remaining_runs.append(task_run)
        skipped_count = total_task_count - len(remaining_runs)
        if skipped_count:
            log.info("Skipping %d/%d tasks that already have a successful report; "
                      "%d remaining (failed or never evaluated). Pass --force-rerun to re-run "
                      "everything.", skipped_count, total_task_count, len(remaining_runs))
        task_runs = remaining_runs

    application_session: SandboxSession | None = None
    try:
        # One packaged application serves the whole sequential batch. Each task evaluator still
        # enters and exits its own task, so map markers and dynamic state do not leak between
        # episodes.
        if task_runs and not args.attach:
            application_session = SandboxSession()
            application_session.__enter__()
            launch_build(application_session, build_folder, args.exe_path)
            AgentClient(args.server_url).wait_until_ready(args.exe_boot_wait)

        options = RunOptions(
            model=model,
            max_steps=args.max_steps,
            build_folder=build_folder,
            exe_path=args.exe_path,
            server_url=args.server_url,
            exe_boot_wait=args.exe_boot_wait,
            post_teleport_wait=args.post_teleport_wait,
            output_dir=model_output_dir,
            attach=True,
            save_frames=args.save_frames,
            save_video=not args.no_save_video,
            video_fps=args.video_fps,
            action_sample_interval=args.action_sample_interval,
            scene_ready_poll=not args.no_scene_ready_poll,
            scene_poll_interval=args.scene_poll_interval,
            scene_ready_consecutive_checks=args.scene_ready_consecutive_checks,
            scene_edge_density_threshold=args.scene_edge_density_threshold,
        )
        report, report_path, worker_count = execute_task_runs(
            task_runs, results, total_task_count, options, args.max_workers
        )
    finally:
        if application_session is not None:
            application_session.__exit__(None, None, None)
    print(json.dumps({
        "model": report["model"],
        "max_steps": options.max_steps,
        "max_workers": worker_count,
        "output_dir": str(options.output_dir),
        "task_count": report["task_count"],
        "completed_count": report["completed_count"],
        "failed_count": report["failed_count"],
        "success_rate": report["success_rate"],
        "accuracy": report["accuracy"],
        "navigation_arrival_rate": report["navigation_arrival_rate"],
        "closure_violation_rate": report["closure_violation_rate"],
        "batch_report": str(report_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
