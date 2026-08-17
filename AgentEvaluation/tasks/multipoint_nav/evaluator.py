"""Evaluator for TaskType.MultipointNav (MP task IDs, numeric type 13).

MP tasks are multi-point route-planning tasks:

- `description` asks the agent to visit several places in one outing and explicitly asks
  for an optimal route ("I will visit Aberdeen Sports Ground, Wong Chuk Hang Sports
  Centre and Ocean Square today... help me plan the optimal route"). Unlike the SF
  schedule tasks there is NO required visiting order and NO time window -- choosing the
  order *is* the task.
- `multiRouteStart` is the editor-selected starting position.
- `multiRouteTargets` is the ground truth: 3-4 targets, each
  {"kind", "point": GeoPoint, "poiCategory", "note"}; `note` optionally carries a POI
  name. Targets may be visited in any order; entering a target's arrival radius marks it
  visited.
- `startPoint`/`endPoint` are zero-coordinate placeholders on all current MP payloads and
  must not be used for teleport or metrics.

Scoring centers on completion (the user-facing question "did it manage to visit them
all?") plus route efficiency (it was asked for an *optimal* route):

- `multipoint_completion_ratio`: fraction of targets visited -- the overall completion
  rate; aggregated across tasks by the batch tooling into the mean completion rate.
- `multipoint_targets_visited`: how many targets were visited -- aggregated into the mean
  number of completed targets per task.
- `multipoint_all_completed` / `reached_destination`: every target visited.
- `multipoint_route_efficiency`: the MST lower-bound route length divided by the agent's
  actual path length (<= 1; higher means less wasted travel). The MST over
  {start} ∪ {targets} lower-bounds any route that visits all targets.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from ..metrics import compute_common_metrics, haversine_meters, mst_route_length_meters
from .prompt import SYSTEM_PROMPT

log = logging.getLogger(__name__)


class MultipointNavEvaluator(BaseNavEvaluator):
    """Evaluate visiting multiple unordered targets with a self-planned route."""

    task_type = 13
    task_name = "MultipointNav"
    task_id_prefix = "MP-"

    def __init__(self, task, sandbox, llm, config):
        self._targets: list[dict[str, Any]] = [
            dict(entry.get("point") or {}) for entry in (task.get("multiRouteTargets") or [])
        ]
        self._target_notes: list[str] = [
            str(entry.get("note") or "").strip()
            for entry in (task.get("multiRouteTargets") or [])
        ]
        self._visited: list[dict[str, Any] | None] = [None] * len(self._targets)
        self._visit_order: list[int] = []
        super().__init__(task, sandbox, llm, config)

    # ── evaluator interface ──────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def _start_point(self) -> dict[str, Any]:
        return self.task["multiRouteStart"]

    def _target_label(self, index: int) -> str:
        return self._target_notes[index] or f"Target {index + 1}"

    def _unvisited_indices(self) -> list[int]:
        return [index for index in range(len(self._targets)) if self._visited[index] is None]

    def destination(self) -> dict[str, Any] | None:
        """The nearest unvisited target (for per-frame progress logging only)."""
        unvisited = self._unvisited_indices()
        if not unvisited:
            return self._targets[-1] if self._targets else None
        # No current-position context here; report the first unvisited target. The
        # distance readout in the per-step log is informational only for MP tasks.
        return self._targets[unvisited[0]]

    def task_instructions(self) -> str:
        lines = [
            "[Multi-Point Route Planning Task]",
            f"Current location: {format_geo_point(self._start_point())}",
            "",
            str(self.task.get("description", "")).strip(),
            "",
            f"There are {len(self._targets)} destinations to visit. There is no required "
            "order: plan the most efficient route yourself, then visit all of them.",
        ]
        return "\n".join(lines)

    def _progress_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        """Distance to the NEAREST unvisited target; completed when all are visited."""
        base = {
            "distance_to_destination_meters": None,
            "reached_destination": None,
            "task_completed": not self._unvisited_indices(),
        }
        if "lat" not in state or "lon" not in state:
            return base
        unvisited = self._unvisited_indices()
        if not unvisited:
            return base
        nearest = min(haversine_meters(state, self._targets[index]) for index in unvisited)
        base["distance_to_destination_meters"] = round(nearest, 3)
        base["reached_destination"] = nearest <= self.config.arrival_radius_meters
        base["unvisited_target_count"] = len(unvisited)
        return base

    def _pending_extra_context(self, elapsed_seconds: float) -> str | None:
        """Keep the agent aware of its visiting progress on every turn."""
        total = len(self._targets)
        visited_count = total - len(self._unvisited_indices())
        remaining = ", ".join(
            self._target_label(index) for index in self._unvisited_indices()
        ) or "none"
        return (f"Route progress: {visited_count}/{total} destinations visited. "
                f"Remaining: {remaining}.")

    # ── visit tracking ───────────────────────────────────────────────────

    def _update_visits(self, state: dict[str, Any], step: int) -> None:
        """Mark every unvisited target whose arrival radius contains the agent."""
        if "lat" not in state or "lon" not in state:
            return
        for index in self._unvisited_indices():
            distance = haversine_meters(state, self._targets[index])
            if distance <= self.config.arrival_radius_meters:
                self._visited[index] = {
                    "target_index": index,
                    "target": self._target_label(index),
                    "visited": True,
                    "visited_at_step": step,
                    "visit_order": len(self._visit_order) + 1,
                    "arrival_distance_meters": round(distance, 3),
                }
                self._visit_order.append(index)
                log.info("[%s] step %d visited target %d/%d (%s), visit order %d",
                         self.task["id"], step, index + 1, len(self._targets),
                         self._target_label(index), len(self._visit_order))

    # ── episode loop ─────────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        self.task_output_dir.mkdir(parents=True, exist_ok=True)
        initial_state = self.initialize()
        self._update_visits(initial_state, step=0)
        self._record_frame(self.sandbox.screenshot(), "initial")
        report: dict[str, Any] | None = None
        try:
            final_state = initial_state
            for step in range(self.config.max_steps):
                if not self._unvisited_indices():
                    break
                record = self._run_one_step(step)
                self._write_partial(initial_state)
                final_state = record.get("state_after", final_state)
                self._update_visits(final_state, step=record["step"])
                if record.get("terminated"):
                    log.info("Task %s terminated after %d total steps and visiting %d/%d targets; "
                             "scoring current state", self.task["id"], len(self.records),
                             len(self._visit_order), len(self._targets))
                    break
                if not self._unvisited_indices():
                    log.info("Task %s visited all %d targets at step %d",
                             self.task["id"], len(self._targets), step + 1)
                    break
            else:
                final_state = self.sandbox.get_state()
                self._update_visits(final_state, step=self.config.max_steps)
                log.info("[%s] step %d/%d frame=final (max_steps reached) targets_visited=%d/%d",
                         self.task["id"], self.config.max_steps, self.config.max_steps,
                         len(self._visit_order), len(self._targets))
            metrics = self._compute_metrics(initial_state, final_state)
            if metrics.get("reached_destination"):
                completion_step = max(
                    int(result["visited_at_step"])
                    for result in self._visited if result and result.get("visited")
                )
                self._mark_task_completed(completion_step, "all_targets_visited")
            self._finalize_outcome_metrics(metrics)
            report = self._report(initial_state, final_state, metrics)
            self._write(report)
            return report
        finally:
            self._exit_task()
            self._finalize_video(report)

    # ── metrics / report ─────────────────────────────────────────────────

    def _compute_metrics(self, initial_state: dict[str, Any],
                         final_state: dict[str, Any]) -> dict[str, Any]:
        # Common trajectory metrics are computed against the nearest unvisited target
        # (or the last target once all are visited) just for the distance readout.
        reference = self.destination()
        metrics = compute_common_metrics(self.records, initial_state, final_state, reference,
                                         self.config.arrival_radius_meters)
        visited_count = len(self._visit_order)
        total = len(self._targets)
        all_done = not self._unvisited_indices()
        mst = mst_route_length_meters(self._start_point(), self._targets)
        path = float(metrics.get("path_length_meters") or 0.0)
        # Route efficiency: the MST lower bound of the VISITED subset (the useful travel the
        # agent actually accomplished) divided by its actual path length. Zero visited
        # targets means zero useful travel -- the efficiency is 0, not vacuously 1.
        useful = mst_route_length_meters(self._start_point(),
                                         [self._targets[i] for i in self._visit_order])
        metrics.update({
            "multipoint_target_count": total,
            "multipoint_targets_visited": visited_count,
            "multipoint_completion_ratio": round(visited_count / total, 4) if total else 0.0,
            "multipoint_all_completed": all_done,
            "multipoint_visit_order": list(self._visit_order),
            "multipoint_optimal_lower_bound_meters": round(mst, 3),
            "multipoint_route_efficiency": (
                round(min(1.0, useful / path), 4) if path > 0 else None),
            # Aggregation channel: `original_distance_meters` carries the MST lower bound
            # (the distance a perfect route must travel at minimum) so the batch arrival
            # rate reflects full multi-target completion.
            "original_distance_meters": round(mst, 3),
            "remaining_distance_meters": metrics.get("distance_to_destination_meters"),
            "reached_destination": all_done,
        })
        return metrics

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                metrics: dict[str, Any] | None) -> dict[str, Any]:
        report = super()._report(initial_state, final_state, metrics)
        report["start_point"] = self._start_point()
        report["end_point"] = None
        report["serialized_start_point_placeholder"] = self.task.get("startPoint")
        report["multipoint"] = {
            "targets": [
                self._visited[index] if self._visited[index] is not None else {
                    "target_index": index,
                    "target": self._target_label(index),
                    "visited": False,
                    "visited_at_step": None,
                    "visit_order": None,
                    "arrival_distance_meters": None,
                }
                for index in range(len(self._targets))
            ],
            "visit_order": list(self._visit_order),
        }
        return report
