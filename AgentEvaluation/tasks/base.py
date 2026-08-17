"""Reusable base classes for task-specific embodied-agent evaluations."""

from __future__ import annotations

import json
import logging
import math
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from api import (
    NAV_ACTION_SPACE_PROMPT,
    NAV_REACT_PROTOCOL_PROMPT,
    LLMClient,
    VisualReActAgent,
)
from sandbox import AgentClient

from .geo import ClosureCrossingDetector
from .metrics import compute_common_metrics, compute_navigation_metrics, haversine_meters
from .qa import correct_letter, format_question, parse_answer_letter, score_answer
from .scene_readiness import DEFAULT_EDGE_DENSITY_THRESHOLD, assess_scene_readiness
from .video import EpisodeVideoRecorder

log = logging.getLogger(__name__)

FIRST_PERSON_ACTIONS = {"move", "sprint", "look", "jump", "open_map", "terminate"}
MAP_ACTIONS = {"map_select", "map_pan", "map_zoom", "map_orbit", "close_map", "terminate"}
# Navigation tasks use the same map actions as QA tasks (no route-planning shortcut).
NAV_MAP_ACTIONS = MAP_ACTIONS
DIRECTIONS = {"forward", "backward", "left", "right"}


@dataclass
class TaskEpisodeConfig:
    max_steps: int = 12
    post_teleport_wait_seconds: float = 300.0
    action_timeout: int = 30
    retry_count: int = 2
    save_frames: bool = False
    save_video: bool = True
    video_fps: float = 4.0
    action_sample_interval_seconds: float = 0.3
    action_max_frames: int = 60
    arrival_radius_meters: float = 15.0
    output_dir: Path = Path(__file__).resolve().parent.parent / "output" / "tasks"
    # Adaptive scene-load gating: instead of always sleeping the full
    # `post_teleport_wait_seconds`, poll a screenshot every `scene_poll_interval_seconds` and
    # stop early once `assess_scene_readiness()` reports the tiles/textures have streamed in for
    # `scene_ready_consecutive_checks` polls in a row (debounces one lucky frame). Sets a hard
    # ceiling of `post_teleport_wait_seconds` total so a sandbox that never finishes streaming
    # (or a mis-detected always-featureless task, e.g. a genuinely dark/foggy scene) can't hang
    # the episode forever -- it just falls back to the old fixed-wait behavior in that case. Set
    # `scene_ready_poll_enabled=False` to restore the previous unconditional fixed sleep.
    scene_ready_poll_enabled: bool = True
    scene_poll_interval_seconds: float = 5.0
    scene_ready_consecutive_checks: int = 2
    scene_edge_density_threshold: float = DEFAULT_EDGE_DENSITY_THRESHOLD


# QA task types (LandmarkQA/OrientationQA/SpatialQA) use qaStartPoint + four-choice qaOptions.
# Navigation task types (ShortNav/LongNav/InstructionNav) instead use startPoint/endPoint and
# have no QA fields. InstructionNav additionally requires a non-empty `description` field
# containing the turn-by-turn natural-language instructions the agent must follow.
# ConstrainedNav (11) and DynamicClosureNav (12) are navigation tasks that additionally carry
# `restrictedZones` (one or more road-closure polylines the agent must never cross). Both reuse
# the same CN-* task payload; they differ only in *when* the closure is disclosed to the agent
# (see tasks/constrained_nav and tasks/dynamic_closure_nav). `closureDelayMinutes` is present in
# the payload but intentionally unused by both evaluators (the dynamic-closure delay is fixed at
# 30 seconds per spec, not driven by this field).
# II-* implicit-intent navigation payloads also currently serialize as numeric type 12 because
# the Unity task editor reused that slot. They are distinguished from CN-* payloads by task ID
# prefix (see _task_identity_key below); their actual starting point is `exploreStart`, while
# `startPoint` is a zero-coordinate placeholder on current files.
# SF-* schedule-following payloads (numeric type 5) are time-window schedule tasks: their actual
# starting point is `scheduleStart`, their ordered appointment targets live in `schedule`, and
# both `startPoint`/`endPoint` are zero-coordinate placeholders on current files.
# MP-* multipoint payloads (numeric type 13) are multi-point route-planning tasks: their actual
# starting point is `multiRouteStart`, their unordered visit targets live in `multiRouteTargets`,
# and `startPoint`/`endPoint` are likewise zero-coordinate placeholders on current files.
# PS-* place-search payloads (numeric type 3) search for a requested place type from
# `searchOrigin`; `endPoint` is intentionally a zero placeholder (there is no labeled target --
# arrival is judged by the evaluation LLM, see tasks/place_search).
QA_TASK_TYPES = {7, 8, 9}
NAV_TASK_TYPES = {0, 2, 10, 11, 12}
NAV_TASK_TYPES_REQUIRING_DESCRIPTION = {10}
CLOSURE_NAV_TASK_TYPES = {11, 12}
SCHEDULE_WINDOW_TASK_TYPES = {5}
MULTIPOINT_TASK_TYPES = {13}
PLACE_SEARCH_TASK_TYPES = {3}
REQUIRED_FIELDS_BY_TYPE: dict[int, tuple[str, ...]] = {
    **{task_type: ("id", "type", "description", "qaStartPoint", "qaOptions", "qaAnswerIndex")
       for task_type in QA_TASK_TYPES},
    **{task_type: ("id", "type", "startPoint", "endPoint") for task_type in NAV_TASK_TYPES},
    **{task_type: ("id", "type", "startPoint", "endPoint", "description")
       for task_type in NAV_TASK_TYPES_REQUIRING_DESCRIPTION},
    **{task_type: ("id", "type", "startPoint", "endPoint", "restrictedZones")
       for task_type in CLOSURE_NAV_TASK_TYPES if task_type != 12},
    **{task_type: ("id", "type", "description", "scheduleStart", "schedule")
       for task_type in SCHEDULE_WINDOW_TASK_TYPES},
    **{task_type: ("id", "type", "description", "multiRouteStart", "multiRouteTargets")
       for task_type in MULTIPOINT_TASK_TYPES},
    **{task_type: ("id", "type", "description", "searchOrigin")
       for task_type in PLACE_SEARCH_TASK_TYPES},
}
IMPLICIT_INTENT_REQUIRED_FIELDS = ("id", "type", "description", "exploreStart", "endPoint")
DEFAULT_REQUIRED_FIELDS = ("id", "type", "description")


def _task_identity_key(task: dict[str, Any]) -> tuple[int, str]:
    """Return (numeric type, normalized ID prefix) for payloads that reuse a numeric type."""
    task_id = str(task.get("id", ""))
    prefix = task_id.split("-", 1)[0].upper() if "-" in task_id else ""
    return int(task.get("type", -1)), prefix


def _is_implicit_intent_task(task: dict[str, Any]) -> bool:
    task_type, prefix = _task_identity_key(task)
    return task_type == 12 and prefix == "II"


def _is_schedule_window_task(task: dict[str, Any]) -> bool:
    task_type, _prefix = _task_identity_key(task)
    return task_type in SCHEDULE_WINDOW_TASK_TYPES


def _is_multipoint_task(task: dict[str, Any]) -> bool:
    task_type, _prefix = _task_identity_key(task)
    return task_type in MULTIPOINT_TASK_TYPES


def _is_place_search_task(task: dict[str, Any]) -> bool:
    task_type, _prefix = _task_identity_key(task)
    return task_type in PLACE_SEARCH_TASK_TYPES


def _is_zero_geo_point(point: Any) -> bool:
    """Whether a serialized GeoPoint is the editor's 0,0 placeholder (or missing)."""
    if not isinstance(point, dict):
        return True
    return float(point.get("lat", 0.0)) == 0.0 and float(point.get("lon", 0.0)) == 0.0


def load_task_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    task = payload.get("task", payload)
    if not isinstance(task, dict):
        raise ValueError(f"Invalid task payload in {path}")
    if _is_implicit_intent_task(task):
        required = IMPLICIT_INTENT_REQUIRED_FIELDS
    else:
        required = REQUIRED_FIELDS_BY_TYPE.get(int(task.get("type", -1)), DEFAULT_REQUIRED_FIELDS)
    missing = [field for field in required if field not in task]
    if missing:
        raise ValueError(f"Task {path} is missing fields: {', '.join(missing)}")
    if _is_implicit_intent_task(task):
        start = task.get("exploreStart", {})
        if not all(float(start.get(field, 0.0)) != 0.0 for field in ("lat", "lon")):
            raise ValueError(f"Task {path} has a zero-coordinate exploreStart")
    if _is_schedule_window_task(task):
        if _is_zero_geo_point(task.get("scheduleStart")):
            raise ValueError(f"Task {path} has a zero-coordinate scheduleStart")
        schedule = task.get("schedule")
        if not isinstance(schedule, list) or not schedule:
            raise ValueError(f"Task {path} has an empty schedule")
        for index, stop in enumerate(schedule):
            if not isinstance(stop, dict) or _is_zero_geo_point(stop.get("target")):
                raise ValueError(f"Task {path} schedule stop {index} has a zero-coordinate target")
    if _is_multipoint_task(task):
        if _is_zero_geo_point(task.get("multiRouteStart")):
            raise ValueError(f"Task {path} has a zero-coordinate multiRouteStart")
        targets = task.get("multiRouteTargets")
        if not isinstance(targets, list) or not targets:
            raise ValueError(f"Task {path} has no multiRouteTargets")
        for index, entry in enumerate(targets):
            if not isinstance(entry, dict) or _is_zero_geo_point(entry.get("point")):
                raise ValueError(
                    f"Task {path} multiRouteTargets[{index}] has a zero-coordinate point")
    if _is_place_search_task(task) and _is_zero_geo_point(task.get("searchOrigin")):
        raise ValueError(f"Task {path} has a zero-coordinate searchOrigin")
    return task


def format_geo_point(point: dict[str, Any]) -> str:
    """Render a start/end point the same way the Unity task editor prints GeoPoint.ToString()."""
    lat, lon = float(point.get("lat", 0.0)), float(point.get("lon", 0.0))
    height, yaw = float(point.get("height", 0.0)), float(point.get("yaw", 0.0))
    position = f"{lat:.6f},{lon:.6f},{height:.1f}m, yaw {yaw:.0f}\u00b0"
    label = str(point.get("label") or "").strip()
    # Translate any Chinese labels from the Unity task editor into English.
    _LABEL_ZH_EN = {"当前位置": "Current position"}
    label = _LABEL_ZH_EN.get(label, label)
    return f"{label} ({position})" if label else position


def _finite_float(value: Any, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def normalize_action(candidate: Any) -> dict[str, Any]:
    """Normalize common LLM action encodings into the sandbox's flat JSON schema."""
    if not isinstance(candidate, dict):
        raise ValueError("action must be an object")
    if isinstance(candidate.get("action"), str):
        return dict(candidate)
    if isinstance(candidate.get("type"), str):
        return {"action": candidate["type"], **{
            key: value for key, value in candidate.items() if key != "type"
        }}
    if len(candidate) == 1:
        name, parameters = next(iter(candidate.items()))
        if isinstance(name, str) and isinstance(parameters, dict):
            return {"action": name, **parameters}
        if isinstance(name, str) and parameters is None:
            return {"action": name}
    raise ValueError(
        "action must use the flat sandbox schema, for example "
        '{"action":"look","yaw":-20,"pitch":0}'
    )


def validate_action(candidate: Any, mode: str, map_actions: set[str] = MAP_ACTIONS) -> dict[str, Any]:
    """Normalize and validate the intentionally limited exploration action space."""
    normalized = normalize_action(candidate)
    name = normalized.get("action")
    allowed = map_actions if mode == "map" else FIRST_PERSON_ACTIONS
    if name not in allowed:
        raise ValueError(f"Action {name!r} is unavailable in {mode} mode")
    result: dict[str, Any] = {"action": name}
    if name in {"move", "sprint"}:
        if normalized.get("dir") not in DIRECTIONS:
            raise ValueError("Movement dir must be forward, backward, left, or right")
        result["dir"] = normalized["dir"]
        result["seconds"] = min(2.0, max(0.05, _finite_float(normalized.get("seconds", 0.5), "seconds")))
        for field in ("yaw_rate", "pitch_rate"):
            if field in normalized:
                result[field] = min(180.0, max(-180.0, _finite_float(normalized[field], field)))
        if "jump" in normalized:
            result["jump"] = bool(normalized["jump"])
        if "jump_at" in normalized:
            result["jump_at"] = min(result["seconds"], max(0.0, _finite_float(normalized["jump_at"], "jump_at")))
    elif name in {"look", "map_orbit"}:
        result["yaw"] = min(180.0, max(-180.0, _finite_float(normalized.get("yaw", 0), "yaw")))
        result["pitch"] = min(90.0, max(-90.0, _finite_float(normalized.get("pitch", 0), "pitch")))
    elif name == "map_select":
        result["x"] = min(1.0, max(0.0, _finite_float(normalized.get("x", 0.5), "x")))
        result["y"] = min(1.0, max(0.0, _finite_float(normalized.get("y", 0.5), "y")))
    elif name == "map_pan":
        result["east"] = min(2000.0, max(-2000.0, _finite_float(normalized.get("east", 0), "east")))
        result["north"] = min(2000.0, max(-2000.0, _finite_float(normalized.get("north", 0), "north")))
    elif name == "map_zoom":
        result["factor"] = min(4.0, max(0.25, _finite_float(normalized.get("factor", 1), "factor")))
    return result


class _EpisodeEvaluatorBase(ABC):
    """Shared teleport/step/record/persist machinery for one embodied-agent episode."""

    task_type: int
    task_name: str

    def __init__(self, task: dict[str, Any], sandbox: AgentClient, llm: LLMClient,
                 config: TaskEpisodeConfig):
        expected_prefix = getattr(self, "task_id_prefix", None)
        if int(task["type"]) != self.task_type or (
            expected_prefix and not str(task.get("id", "")).startswith(expected_prefix)
        ):
            expected = f"type {self.task_type}"
            if expected_prefix:
                expected += f" with {expected_prefix} task IDs"
            raise ValueError(f"{self.__class__.__name__} cannot evaluate {task['id']} ({expected})")
        self.task = task
        self.sandbox = sandbox
        self.llm = llm
        self.config = config
        self.records: list[dict[str, Any]] = []
        self.agent = self._build_agent()
        # Wall-clock anchor for the *navigation* portion of the episode (set once step 0 is
        # about to run, i.e. after teleport + scene-load wait). Used only by evaluators that
        # gate behavior on elapsed navigation time, such as DynamicClosureNavEvaluator's
        # 30-second closure disclosure delay.
        self._episode_started_at: float | None = None
        # Unified lifecycle metadata. Task-specific loops call _mark_task_completed exactly
        # when their own success condition becomes true; termination is derived from records.
        self._completion_step: int | None = None
        self._completion_elapsed_seconds: float | None = None
        self._completion_event: str | None = None
        self.task_output_dir = config.output_dir / str(task["id"])
        self.frame_dir = self.task_output_dir / "frames"
        self.video_path = self.task_output_dir / "episode.mp4"
        self.report_path = self.task_output_dir / "report.json"
        self.recorder = EpisodeVideoRecorder(
            self.frame_dir, self.video_path, config.video_fps, keep_frames=config.save_frames
        )

    @property
    def _is_navigation_episode(self) -> bool:
        """Whether frame-level arrival means task completion for this evaluator."""
        return self.task_type in NAV_TASK_TYPES

    @property
    def system_prompt(self) -> str:
        return self.build_system_prompt()

    @abstractmethod
    def build_system_prompt(self) -> str:
        """Return the task-specific prompt."""

    @abstractmethod
    def _build_agent(self) -> VisualReActAgent:
        """Construct the VisualReActAgent with the appropriate action space/protocol."""

    @abstractmethod
    def _start_point(self) -> dict[str, Any]:
        """Return the geo point (lat/lon/height/yaw) the episode teleports to."""

    def _allowed_map_actions(self) -> set[str]:
        return MAP_ACTIONS

    def destination(self) -> dict[str, Any] | None:
        """Return the geo point (lat/lon) this episode is judged against, if any.

        Navigation evaluators always have one (task["endPoint"]); QA evaluators may
        optionally define one via task["endPoint"] and otherwise have none.
        """
        return None

    def _progress_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        """Compute this frame's distance-to-destination / completion status, if known.

        `task_completed` is the frame-level completion signal used for logging and
        per-step reporting:
          - Navigation tasks: identical to `reached_destination` (arriving is success).
          - QA tasks: completion is only known once the model commits a final answer,
            so intermediate frames report `task_completed=None` even when a distance
            can still be computed (QA tasks may optionally reference an endPoint).
        """
        destination = self.destination()
        if not destination or "lat" not in state or "lon" not in state:
            return {"distance_to_destination_meters": None, "reached_destination": None,
                    "task_completed": None}
        distance = haversine_meters(state, destination)
        reached = distance <= self.config.arrival_radius_meters
        return {
            "distance_to_destination_meters": round(distance, 3),
            "reached_destination": reached,
            "task_completed": reached if self._is_navigation_episode else None,
        }

    def _record_frame(self, screenshot: bytes, label: str) -> None:
        if self.config.save_frames or self.config.save_video:
            self.recorder.add_jpeg(screenshot, label)

    def _wait_for_scene_ready(self) -> None:
        """Wait for map/terrain tiles to finish streaming in after a teleport.

        Polls a screenshot every `scene_poll_interval_seconds` and stops as soon as
        `assess_scene_readiness()` reports the scene loaded for
        `scene_ready_consecutive_checks` polls in a row, instead of always sleeping the full
        `post_teleport_wait_seconds` -- which was previously wasted time on fast-loading tasks
        and, worse, still not always enough on slow-loading ones (the agent would then start
        exploring a screenshot that is mostly untextured placeholder geometry or a blank map).
        Never waits longer than `post_teleport_wait_seconds` total.
        """
        cap = self.config.post_teleport_wait_seconds
        if not self.config.scene_ready_poll_enabled or cap <= 0:
            log.info("Waiting %.1f seconds after teleport for scene loading", cap)
            time.sleep(cap)
            return

        interval = max(0.5, self.config.scene_poll_interval_seconds)
        needed = max(1, self.config.scene_ready_consecutive_checks)
        threshold = self.config.scene_edge_density_threshold
        deadline = time.monotonic() + cap
        consecutive_ready = 0
        last_assessment = None
        while True:
            try:
                screenshot = self.sandbox.screenshot()
                last_assessment = assess_scene_readiness(screenshot, threshold=threshold)
            except Exception as exc:  # noqa: BLE001 - a failed poll shouldn't abort the episode
                log.warning("[%s] Scene-readiness screenshot poll failed: %s", self.task["id"], exc)
                last_assessment = None
            if last_assessment is not None:
                if last_assessment.is_loaded:
                    consecutive_ready += 1
                else:
                    consecutive_ready = 0
                log.info("[%s] Scene-readiness poll: %s (%d/%d consecutive ready)",
                          self.task["id"], last_assessment, consecutive_ready, needed)
                if consecutive_ready >= needed:
                    return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                log.warning(
                    "[%s] Scene did not report ready within %.1fs post-teleport wait "
                    "(last check: %s); proceeding anyway",
                    self.task["id"], cap, last_assessment,
                )
                return
            time.sleep(min(interval, remaining))

    def _enter_task(self) -> None:
        """Load this task into the sandbox so its map markers are visible to the agent.

        The sandbox only draws a task's destination pin / road-closure polylines on the map
        once the task has been loaded via POST /task/enter; without it the agent explores a
        markerless map and cannot know where the goal is. Must run before the teleport so the
        markers are already in place by the time the scene finishes streaming in.
        """
        sandbox_task_id = str(self.task.get("sourceTaskId") or self.task["id"])
        log.info("[%s] Loading sandbox task %s via POST /task/enter",
                 self.task["id"], sandbox_task_id)
        self.sandbox.task_enter(sandbox_task_id)

    def _exit_task(self) -> None:
        """Unload this task from the sandbox once the episode is over.

        Cleanup must never mask the episode's own outcome (the sandbox may already be gone
        when this runs, e.g. after a session-level failure), so every error is logged and
        swallowed here.
        """
        try:
            self.sandbox.task_exit()
        except Exception as exc:  # noqa: BLE001 - cleanup must not hide the task result
            log.warning("[%s] task/exit failed (ignored): %s", self.task["id"], exc)

    def initialize(self) -> dict[str, Any]:
        self._enter_task()
        point = self._start_point()
        log.info("Teleporting task %s to lat=%s lon=%s height=%s", self.task["id"],
                 point["lat"], point["lon"], point["height"])
        reply = self.sandbox.teleport(float(point["lat"]), float(point["lon"]), float(point["height"]))
        target_yaw = float(point.get("yaw", 0.0)) % 360.0
        state = reply.get("state", {})
        current_yaw = float(state.get("yaw", 0.0)) % 360.0
        yaw_delta = (target_yaw - current_yaw + 180.0) % 360.0 - 180.0
        if abs(yaw_delta) > 0.05:
            self.sandbox.look(yaw=yaw_delta)
        self._wait_for_scene_ready()
        state = self.sandbox.get_state()
        progress = self._progress_snapshot(state)
        log.info(
            "[%s] step 0/%d frame=initial completed=%s distance_to_destination_m=%s",
            self.task["id"], self.config.max_steps,
            progress["task_completed"], progress["distance_to_destination_meters"],
        )
        self._episode_started_at = time.monotonic()
        return state

    def _elapsed_episode_seconds(self) -> float:
        """Seconds since step 0 began (post teleport/scene-load wait). 0.0 before that."""
        if self._episode_started_at is None:
            return 0.0
        return time.monotonic() - self._episode_started_at

    def _elapsed_at_step(self, step: int) -> float:
        """Return the recorded episode time at ``step`` (step 0 is the initial state)."""
        if step <= 0:
            return 0.0
        record = next((item for item in self.records if item.get("step") == step), None)
        if record is not None and record.get("elapsed_episode_seconds") is not None:
            return float(record["elapsed_episode_seconds"])
        return self._elapsed_episode_seconds()

    def _mark_task_completed(self, step: int, event: str,
                             elapsed_seconds: float | None = None) -> None:
        """Record the first step/time at which this evaluator's success condition became true."""
        if self._completion_step is not None:
            return
        step = int(step)
        if step < 0 or step > len(self.records):
            raise ValueError(
                f"completion step {step} is outside recorded range 0..{len(self.records)}"
            )
        self._completion_step = step
        self._completion_elapsed_seconds = round(
            self._elapsed_at_step(step) if elapsed_seconds is None else float(elapsed_seconds), 3
        )
        self._completion_event = str(event)

    def _episode_summary(self) -> dict[str, Any]:
        """Lifecycle fields shared by every report, metric set, and batch result."""
        termination = next((record for record in self.records if record.get("terminated")), None)
        termination_step = int(termination["step"]) if termination is not None else None
        termination_elapsed = (
            round(float(termination.get("elapsed_episode_seconds", 0.0)), 3)
            if termination is not None else None
        )
        return {
            "task_completed": self._completion_step is not None,
            "steps_completed": len(self.records),
            "completion_step": self._completion_step,
            "completion_elapsed_seconds": self._completion_elapsed_seconds,
            "completion_event": self._completion_event,
            "agent_terminated": termination is not None,
            "agent_termination_step": termination_step,
            "agent_termination_elapsed_seconds": termination_elapsed,
            # The terminate decision itself is a recorded step, so this is the total number
            # of ReAct decisions made when the agent stopped the episode.
            "steps_completed_at_termination": termination_step,
        }

    def episode_summary(self) -> dict[str, Any]:
        """Public copy of current lifecycle state for batch/failure logging."""
        return dict(self._episode_summary())

    def _finalize_outcome_metrics(self, metrics: dict[str, Any]) -> None:
        """Attach lifecycle metrics and emit one uniform machine-searchable outcome log line."""
        summary = self._episode_summary()
        metrics.update(summary)
        log.info(
            "[%s] episode_outcome task_completed=%s completion_step=%s "
            "completion_elapsed_seconds=%s completion_event=%s steps_completed=%d "
            "agent_terminated=%s agent_termination_step=%s "
            "agent_termination_elapsed_seconds=%s steps_completed_at_termination=%s",
            self.task["id"], summary["task_completed"], summary["completion_step"],
            summary["completion_elapsed_seconds"], summary["completion_event"],
            summary["steps_completed"], summary["agent_terminated"],
            summary["agent_termination_step"], summary["agent_termination_elapsed_seconds"],
            summary["steps_completed_at_termination"],
        )

    def _plan(self, state: dict[str, Any], screenshot: bytes, step: int,
             extra_context: str | None = None) -> dict[str, Any]:
        # State remains evaluator-private: the closure uses only mode to reject impossible
        # actions, while VisualReActAgent receives only the screenshot and its own memory.
        try:
            decision = self.agent.plan(
                screenshot,
                lambda candidate: validate_action(
                    candidate, str(state.get("mode", "first_person")), self._allowed_map_actions()
                ),
                extra_context=extra_context,
            )
        except ValueError as exc:
            failure_path = self.task_output_dir / f"failed_step_{step + 1:04d}.json"
            failure_path.write_text(json.dumps({"task_id": self.task["id"], "step": step + 1,
                                                "state": state, "error": str(exc)},
                                               ensure_ascii=False, indent=2), encoding="utf-8")
            raise ValueError(f"{exc}; details={failure_path}") from exc
        return {
            "observation": decision.observation,
            "reason": decision.reason,
            "action": decision.action,
            "raw_response": decision.raw_response,
            "raw_responses": decision.raw_responses,
            "model_attempts": decision.model_attempts,
        }

    def _pending_extra_context(self, elapsed_seconds: float) -> str | None:
        """Override to inject a one-off notice into this turn's exploration prompt.

        Used by DynamicClosureNavEvaluator to disclose a newly-appeared road closure once
        `elapsed_seconds` crosses the disclosure delay, without altering the original task
        description. No-op (returns None) for every other evaluator.
        """
        return None

    def _closure_check_active(self, elapsed_seconds: float) -> bool:
        """Override to gate closure-crossing detection on elapsed navigation time.

        ConstrainedNavEvaluator returns True from the first step (the closure is disclosed
        up front, so it is off-limits immediately). DynamicClosureNavEvaluator returns True
        only once the closure has been disclosed. Every other evaluator leaves this False,
        so `_check_closure_crossing` below is a no-op for them.
        """
        return False

    def _check_closure_crossing(self, state_before: dict[str, Any], state_after: dict[str, Any],
                                elapsed_seconds: float) -> dict[str, Any]:
        """Return this step's closure-crossing verdict; a no-op stub for non-closure tasks."""
        return {"closure_check_active": False, "closure_crossed": False, "closure_crossed_edges": []}

    def _run_one_step(self, step: int) -> dict[str, Any]:
        state_before = self.sandbox.get_state()
        screenshot = self.sandbox.screenshot()
        self._record_frame(screenshot, f"step_{step + 1:04d}_before")
        progress_before = self._progress_snapshot(state_before)
        elapsed_before = self._elapsed_episode_seconds()
        extra_context = self._pending_extra_context(elapsed_before)
        decision = self._plan(state_before, screenshot, step, extra_context=extra_context)
        terminated = decision["action"].get("action") == "terminate"
        if terminated:
            # `terminate` is evaluator-owned control flow, not a Unity action.  Keeping the
            # state unchanged avoids an unsupported /action request and scores the exact view
            # from which the agent chose to stop.
            duration = 0.0
            sampled_images: list[str] = []
            state_after = state_before
            action_result: Any = {"action": "terminate", "terminated": True}
        else:
            started = time.monotonic()
            reply = self.sandbox.act(
                decision["action"],
                timeout=self.config.action_timeout,
                interval=(self.config.action_sample_interval_seconds
                          if self.config.save_video else 0.0),
                max_frames=self.config.action_max_frames,
            )
            duration = time.monotonic() - started
            sampled_images = reply.get("images", [])
            state_after = reply.get("state", {})
            action_result = reply.get("action")
        if self.config.save_video:
            self.recorder.add_data_urls(sampled_images, f"step_{step + 1:04d}_action")
        progress_after = self._progress_snapshot(state_after)
        elapsed_after = self._elapsed_episode_seconds()
        closure = self._check_closure_crossing(state_before, state_after, elapsed_after)
        # Frame-level progress log: every recorded frame (the "before" observation frame
        # that drives the model's decision, and the "after" frame once the action lands)
        # gets its own distance-to-destination / task-completion readout so the run log can
        # be scanned frame-by-frame without opening report.json. `closure_crossed` is always
        # logged (True/False/inactive) for closure-constrained navigation tasks so the run log
        # can be scanned frame-by-frame for restriction violations without opening report.json.
        log.info(
            "[%s] step %d/%d frame=before completed=%s distance_to_destination_m=%s",
            self.task["id"], step + 1, self.config.max_steps,
            progress_before["task_completed"], progress_before["distance_to_destination_meters"],
        )
        if extra_context:
            log.info("[%s] step %d/%d extra context injected: %s",
                     self.task["id"], step + 1, self.config.max_steps, extra_context)
        log.info(
            "[%s] step %d/%d frame=after  completed=%s distance_to_destination_m=%s "
            "closure_check_active=%s closure_crossed=%s terminated=%s",
            self.task["id"], step + 1, self.config.max_steps,
            progress_after["task_completed"], progress_after["distance_to_destination_meters"],
            closure["closure_check_active"], closure["closure_crossed"], terminated,
        )
        record = {"step": step + 1, "state_before": state_before,
                  "observation": decision["observation"], "reason": decision["reason"],
                  "action": decision["action"], "result": action_result,
                  "state_after": state_after,
                  "terminated": terminated,
                  "duration_seconds": round(duration, 3),
                  "sampled_video_frames": len(sampled_images),
                  "model_attempts": decision["model_attempts"],
                  "raw_response": decision["raw_response"],
                  "raw_responses": decision["raw_responses"],
                  "progress_before": progress_before,
                  "progress_after": progress_after,
                  "elapsed_episode_seconds": round(elapsed_after, 3),
                  "closure_notice_injected": extra_context,
                  "closure_check_active": closure["closure_check_active"],
                  "closure_crossed": closure["closure_crossed"],
                  "closure_crossed_edges": closure["closure_crossed_edges"]}
        self.records.append(record)
        return record

    @abstractmethod
    def run(self) -> dict[str, Any]:
        """Run the full episode and return the final report."""

    def _write(self, report: dict[str, Any]) -> None:
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def _finalize_video(self, report: dict[str, Any] | None) -> None:
        if self.config.save_video:
            encoded = self.recorder.encode()
            if report is not None and encoded is not None:
                report["video_path"] = str(encoded)
                report["video_frame_count"] = len(self.recorder.frame_paths)
                self._write(report)


class BaseTaskEvaluator(_EpisodeEvaluatorBase):
    """Template method for teleport, explore, answer, score, and persist (four-choice QA tasks)."""

    def _build_agent(self) -> VisualReActAgent:
        return VisualReActAgent(
            llm=self.llm,
            task_prompt=self.system_prompt,
            task_description=format_question(self.task),
            retry_count=self.config.retry_count,
        )

    def _start_point(self) -> dict[str, Any]:
        return self.task["qaStartPoint"]

    def task_specific_metrics(self, answer: str | None) -> dict[str, Any]:
        """Override when a task type needs extra metrics beyond QA accuracy."""
        return {}

    def destination(self) -> dict[str, Any] | None:
        point = self.task.get("endPoint")
        return point if isinstance(point, dict) else None

    def ask_final_answer(self) -> dict[str, Any]:
        screenshot = self.sandbox.screenshot()
        self._record_frame(screenshot, "final_answer")
        state = self.sandbox.get_state()
        progress = self._progress_snapshot(state)
        answer = self.agent.answer(screenshot, parse_answer_letter)
        expected = correct_letter(self.task)
        task_completed = answer.answer == expected
        if task_completed:
            self._mark_task_completed(
                len(self.records), "final_answer", self._elapsed_episode_seconds()
            )
        log.info(
            "[%s] step final frame=final_answer completed=%s distance_to_destination_m=%s "
            "answer=%s correct_answer=%s completion_step=%s completion_elapsed_seconds=%s",
            self.task["id"], task_completed, progress["distance_to_destination_meters"],
            answer.answer, expected, self._completion_step, self._completion_elapsed_seconds,
        )
        return {"answer": answer.answer, "reason": answer.reason,
                "raw_response": answer.raw_response,
                "distance_to_destination_meters": progress["distance_to_destination_meters"],
                "task_completed": task_completed}

    def run(self) -> dict[str, Any]:
        self.task_output_dir.mkdir(parents=True, exist_ok=True)
        initial_state = self.initialize()
        self._record_frame(self.sandbox.screenshot(), "initial")
        report: dict[str, Any] | None = None
        try:
            for step in range(self.config.max_steps):
                record = self._run_one_step(step)
                self._write_partial(initial_state)
                if record.get("terminated"):
                    log.info("Task %s terminated exploration at step %d after %d total steps; "
                             "requesting final answer", self.task["id"], step + 1,
                             len(self.records))
                    break
            final_state = self.sandbox.get_state()
            answer = self.ask_final_answer()
            common = compute_common_metrics(self.records, initial_state, final_state, self.destination(),
                                            self.config.arrival_radius_meters)
            metrics = {**common, **score_answer(self.task, answer["answer"]),
                       **self.task_specific_metrics(answer["answer"])}
            self._finalize_outcome_metrics(metrics)
            report = self._report(initial_state, final_state, answer, metrics)
            self._write(report)
            return report
        finally:
            self._exit_task()
            self._finalize_video(report)

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                answer: dict[str, Any] | None, metrics: dict[str, Any] | None) -> dict[str, Any]:
        return {"task_id": self.task["id"], "task_type": self.task_name,
                "source_task_id": self.task.get("sourceTaskId") or None,
                "generated_variant": bool(self.task.get("_generatedVariant", False)),
                **self._episode_summary(),
                "question": self.task["description"], "options": self.task["qaOptions"],
                "model": self.llm.config.model,
                "hyperparameters": {
                    "model": self.llm.config.model,
                    "max_steps": self.config.max_steps,
                    "action_timeout": self.config.action_timeout,
                    "retry_count": self.config.retry_count,
                    "video_fps": self.config.video_fps,
                    "action_sample_interval_seconds": self.config.action_sample_interval_seconds,
                },
                "initial_state": initial_state,
                "final_state": final_state,
                "answer": answer, "metrics": metrics,
                "video_path": str(self.video_path) if self.config.save_video else None,
                "video_frame_count": len(self.recorder.frame_paths), "steps": self.records}

    def _write_partial(self, initial_state: dict[str, Any]) -> None:
        self._write(self._report(initial_state, self.records[-1]["state_after"], None, None))


class BaseNavEvaluator(_EpisodeEvaluatorBase):
    """Template method for goal-directed navigation tasks (ShortNav / LongNav).

    Unlike the QA evaluators, navigation tasks have no multiple-choice answer: success is
    measured purely by how close the agent ends up to the labeled destination relative to
    the original start-to-destination distance. The episode stops early once the agent's
    reported position is within `arrival_radius_meters` of the destination.
    """

    def _build_agent(self) -> VisualReActAgent:
        return VisualReActAgent(
            llm=self.llm,
            task_prompt=self.system_prompt,
            task_description=self.task_instructions(),
            retry_count=self.config.retry_count,
            action_space_prompt=NAV_ACTION_SPACE_PROMPT,
            react_protocol_prompt=NAV_REACT_PROTOCOL_PROMPT,
        )

    def _allowed_map_actions(self) -> set[str]:
        return NAV_MAP_ACTIONS

    def _start_point(self) -> dict[str, Any]:
        return self.task["startPoint"]

    def destination(self) -> dict[str, Any]:
        return self.task["endPoint"]

    @abstractmethod
    def task_instructions(self) -> str:
        """Return the task-specific instruction text describing start/goal."""

    def task_specific_metrics(self) -> dict[str, Any]:
        """Override when a navigation task type needs extra metrics beyond arrival/progress."""
        return {}

    def _reached_destination(self, state: dict[str, Any]) -> bool:
        return bool(self._progress_snapshot(state)["reached_destination"])

    # ── road-closure crossing detection, shared by ConstrainedNav / DynamicClosureNav ──
    #
    # `restrictedZones` (present only on CN-* task payloads) describes one or more open
    # polylines ("closure segments"); "crossing the closure" means the agent's movement segment
    # (state_before position -> state_after position, both this step) intersected any single
    # edge of any polyline. Both closure-constrained evaluators share this detector; they
    # differ only in when `_closure_check_active` starts returning True (see each evaluator).

    @property
    def _closure_detector(self) -> ClosureCrossingDetector:
        detector = getattr(self, "_closure_detector_instance", None)
        if detector is None:
            detector = ClosureCrossingDetector(
                self.task.get("restrictedZones"), origin=self._start_point()
            )
            self._closure_detector_instance = detector
        return detector

    def _check_closure_crossing(self, state_before: dict[str, Any], state_after: dict[str, Any],
                                elapsed_seconds: float) -> dict[str, Any]:
        active = self._closure_check_active(elapsed_seconds)
        if not active or not self._closure_detector.has_edges:
            return {"closure_check_active": active, "closure_crossed": False,
                    "closure_crossed_edges": []}
        crossed_edges = self._closure_detector.crossed_edges(state_before, state_after)
        return {"closure_check_active": True, "closure_crossed": bool(crossed_edges),
                "closure_crossed_edges": crossed_edges}

    def run(self) -> dict[str, Any]:
        self.task_output_dir.mkdir(parents=True, exist_ok=True)
        initial_state = self.initialize()
        self._record_frame(self.sandbox.screenshot(), "initial")
        report: dict[str, Any] | None = None
        closure_violation: dict[str, Any] | None = None
        try:
            final_state = initial_state
            for step in range(self.config.max_steps):
                record = self._run_one_step(step)
                self._write_partial(initial_state)
                final_state = record.get("state_after", final_state)
                if record.get("terminated"):
                    if self._reached_destination(final_state):
                        self._mark_task_completed(
                            record["step"], "agent_terminated_at_destination"
                        )
                    log.info("Task %s terminated navigation at step %d after %d total steps; "
                             "scoring current state", self.task["id"], step + 1,
                             len(self.records))
                    break
                if record.get("closure_crossed"):
                    # Crossing a disclosed closure is an immediate, unconditional failure for
                    # ConstrainedNav/DynamicClosureNav: stop the episode right away instead of
                    # letting the agent continue toward the destination on the wrong side.
                    closure_violation = {
                        "step": record["step"],
                        "elapsed_episode_seconds": record["elapsed_episode_seconds"],
                        "crossed_edges": record["closure_crossed_edges"],
                    }
                    log.info(
                        "[%s] step %d/%d closure violation: agent crossed restricted edges %s "
                        "-- ending episode as failed",
                        self.task["id"], record["step"], self.config.max_steps,
                        record["closure_crossed_edges"],
                    )
                    break
                if self._reached_destination(final_state):
                    self._mark_task_completed(record["step"], "destination_reached")
                    log.info("Task %s reached destination at step %d (elapsed %.3fs)",
                             self.task["id"], step + 1,
                             self._completion_elapsed_seconds or 0.0)
                    break
            else:
                final_state = self.sandbox.get_state()
                final_progress = self._progress_snapshot(final_state)
                log.info(
                    "[%s] step %d/%d frame=final (max_steps reached) completed=%s "
                    "distance_to_destination_m=%s",
                    self.task["id"], self.config.max_steps, self.config.max_steps,
                    final_progress["task_completed"], final_progress["distance_to_destination_meters"],
                )
                if final_progress["reached_destination"]:
                    self._mark_task_completed(
                        len(self.records), "destination_reached_at_final_state"
                    )
            metrics = {
                **compute_common_metrics(self.records, initial_state, final_state, self.destination(),
                                         self.config.arrival_radius_meters),
                **compute_navigation_metrics(final_state, self._start_point(), self.destination(),
                                             self.config.arrival_radius_meters),
                **self.task_specific_metrics(),
                **self._closure_metrics(closure_violation),
            }
            if closure_violation is not None:
                # A closure violation overrides arrival: reaching the destination after
                # crossing a restricted edge still counts as task failure.
                metrics["reached_destination"] = False
            elif metrics.get("reached_destination") and self._completion_step is None:
                self._mark_task_completed(
                    len(self.records), "destination_reached_at_final_state"
                )
            self._finalize_outcome_metrics(metrics)
            report = self._report(initial_state, final_state, metrics)
            self._write(report)
            return report
        finally:
            self._exit_task()
            self._finalize_video(report)

    def _closure_metrics(self, closure_violation: dict[str, Any] | None) -> dict[str, Any]:
        """Override-free helper so both closure-constrained evaluators report the same shape."""
        checked_steps = sum(1 for record in self.records if record.get("closure_check_active"))
        return {
            "closure_violated": closure_violation is not None,
            "closure_violation": closure_violation,
            "closure_checked_step_count": checked_steps,
            "closure_edge_count": len(self._closure_detector.edges),
        }

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                metrics: dict[str, Any] | None) -> dict[str, Any]:
        return {"task_id": self.task["id"], "task_type": self.task_name,
                "source_task_id": self.task.get("sourceTaskId") or None,
                "generated_variant": bool(self.task.get("_generatedVariant", False)),
                **self._episode_summary(),
                "instructions": self.task_instructions(),
                "start_point": self.task["startPoint"], "end_point": self.task["endPoint"],
                "restricted_zones": self.task.get("restrictedZones"),
                "model": self.llm.config.model,
                "hyperparameters": {
                    "model": self.llm.config.model,
                    "max_steps": self.config.max_steps,
                    "action_timeout": self.config.action_timeout,
                    "retry_count": self.config.retry_count,
                    "video_fps": self.config.video_fps,
                    "action_sample_interval_seconds": self.config.action_sample_interval_seconds,
                    "arrival_radius_meters": self.config.arrival_radius_meters,
                },
                "initial_state": initial_state,
                "final_state": final_state,
                "metrics": metrics,
                "video_path": str(self.video_path) if self.config.save_video else None,
                "video_frame_count": len(self.recorder.frame_paths), "steps": self.records}

    def _write_partial(self, initial_state: dict[str, Any]) -> None:
        self._write(self._report(initial_state, self.records[-1]["state_after"], None))
