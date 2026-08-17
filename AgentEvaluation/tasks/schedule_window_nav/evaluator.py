"""Evaluator for TaskType.ScheduleWindowNav (SF task IDs, numeric type 5).

SF tasks are time-window schedule-following tasks:

- `description` narrates the agent's day as an ordered list of appointments, each with a
  scheduled time ("At 10 a.m., you've got a court hearing at the Court of Final Appeal.
  You're meeting your husband at Samsung at 12 noon. ..."). A variant states only a current
  time plus one overall deadline ("It is now 9:00 AM; run these errands within 2 hours").
- `scheduleStart` is the editor-selected starting position.
- `schedule` is the editor-labeled ground truth: the ordered appointment targets, aligned
  positionally with the appointments in the description.
- `startPoint`/`endPoint` are zero-coordinate placeholders on all current SF payloads and
  must not be used for teleport or metrics.

The sandbox clock (state["time"]) advances in real time and can be set via the `set_time`
action, which makes the time windows genuinely enforceable: at episode start the clock is
set to the narrative "now" (the stated current time, or a fixed lead before the first
appointment), and from then on every minute the agent spends planning or walking consumes
real schedule time. Scoring therefore covers three dimensions:

1. Order: stops must be reached in the scheduled sequence; arriving at a later stop's
   radius before completing earlier ones is an order violation.
2. Arrival: fraction of stops reached within `arrival_radius_meters`, in order.
3. Punctuality: per-stop on-time verdicts against the LLM-parsed deadlines, plus the
   optional overall deadline for errand-chain tasks. If the description cannot be parsed
   into times, the episode degrades to order+arrival scoring only.
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from ..metrics import compute_common_metrics, compute_navigation_metrics, haversine_meters
from .prompt import SYSTEM_PROMPT
from .schedule import (
    ParsedSchedule,
    format_clock,
    parse_schedule,
    parse_state_clock,
)

log = logging.getLogger(__name__)

# When the description states no "current time", the sandbox clock is set this many
# minutes before the first appointment so the agent has a realistic but bounded head start.
DEFAULT_LEAD_MINUTES = 45
# A deadline of "10:00" is treated as the whole minute: arriving before 10:01:00 still
# counts as on time (the parsed deadlines carry minute resolution only).
ON_TIME_GRACE_SECONDS = 60.0


class ScheduleWindowNavEvaluator(BaseNavEvaluator):
    """Evaluate following an ordered, time-windowed appointment schedule."""

    task_type = 5
    task_name = "ScheduleWindowNav"
    task_id_prefix = "SF-"

    def __init__(self, task, sandbox, llm, config):
        # Parse the narrative schedule up front: _build_agent() (invoked by super().__init__)
        # already needs the parsed appointments to render task_instructions().
        self._schedule: ParsedSchedule = parse_schedule(
            llm, str(task.get("description", "")), expected_stops=len(task.get("schedule") or []),
            retry_count=config.retry_count,
        )
        self._targets: list[dict[str, Any]] = [
            dict(stop.get("target") or {}) for stop in (task.get("schedule") or [])
        ]
        self._next_stop_index = 0
        self._order_violations: list[dict[str, Any]] = []
        self._order_violation_stops: set[int] = set()
        self._stop_results: list[dict[str, Any] | None] = [None] * len(self._targets)
        # Clock state: reference minute the sandbox clock is set to at episode start, and
        # the latest clock reading seen in any state payload (minutes, may exceed 1440).
        self._clock_active = False
        self._clock_start_minutes: float | None = None
        self._last_sim_minutes: float | None = None
        self._reference_minutes: float | None = self._plan_reference_minutes()
        super().__init__(task, sandbox, llm, config)

    # ── schedule / clock helpers ─────────────────────────────────────────

    def _plan_reference_minutes(self) -> float | None:
        """The narrative 'now' the sandbox clock should show at episode start."""
        if self._schedule.current_time_minutes is not None:
            return float(self._schedule.current_time_minutes)
        first = self._schedule.first_deadline_minutes()
        if first is not None:
            return float(first - DEFAULT_LEAD_MINUTES)
        return None

    def _stop_deadline(self, index: int) -> float | None:
        """Stop deadline in the same unwrapped-minute frame as the sandbox clock."""
        deadline = self._schedule.stops[index].deadline_minutes
        if deadline is None or self._reference_minutes is None:
            return None
        value = float(deadline)
        while value < self._reference_minutes:
            value += 1440.0  # appointment falls after midnight relative to the start
        return value

    def _total_deadline(self) -> float | None:
        deadline = self._schedule.total_deadline_minutes
        if deadline is None or self._reference_minutes is None:
            return None
        value = float(deadline)
        while value < self._reference_minutes:
            value += 1440.0
        return value

    def _unwrap_clock(self, minutes: float) -> float:
        """Map a raw HH:MM clock reading onto the monotonic episode timeline."""
        if self._clock_start_minutes is not None:
            while minutes < self._clock_start_minutes - 12 * 60:
                minutes += 1440.0
        return minutes

    def _update_clock_from_state(self, state: dict[str, Any]) -> None:
        """Advance the latest clock reading from one state payload (monotonic).

        Older states (for example the pre-set_time initial state) must never move the
        reading backwards: `_update_arrivals` is also called with `initial_state`, which
        was captured before the sandbox clock was set to the narrative start time.
        """
        minutes = parse_state_clock(state)
        if minutes is None:
            return
        minutes = self._unwrap_clock(minutes)
        if self._last_sim_minutes is None or minutes > self._last_sim_minutes:
            self._last_sim_minutes = minutes

    def _setup_clock(self, initial_state: dict[str, Any]) -> None:
        """Set the sandbox clock to the narrative start time (best effort)."""
        self._update_clock_from_state(initial_state)
        if self._reference_minutes is None:
            log.info("[%s] No usable schedule times; running order-only scoring", self.task["id"])
            return
        hour = int(self._reference_minutes // 60) % 24
        minute = int(self._reference_minutes % 60)
        try:
            self.sandbox.set_time(hour, minute)
            state = self.sandbox.get_state()
            self._update_clock_from_state(state)
        except Exception as exc:  # noqa: BLE001 - an older build without set_time must not abort
            log.warning("[%s] set_time failed (%s); falling back to the sandbox's own clock",
                        self.task["id"], exc)
        if self._last_sim_minutes is not None:
            self._clock_active = True
            self._clock_start_minutes = self._last_sim_minutes
            log.info("[%s] Schedule clock active: start=%s", self.task["id"],
                     format_clock(int(self._clock_start_minutes)))
        else:
            log.warning("[%s] Sandbox state carries no clock; time-window metrics disabled",
                        self.task["id"])

    # ── evaluator interface ──────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def _start_point(self) -> dict[str, Any]:
        return self.task["scheduleStart"]

    def destination(self) -> dict[str, Any] | None:
        """The current appointment target; the final stop once the schedule is complete."""
        if not self._targets:
            return None
        return self._targets[min(self._next_stop_index, len(self._targets) - 1)]

    def task_instructions(self) -> str:
        lines = [
            "[Time-Window Schedule Task]",
            f"Current location: {format_geo_point(self._start_point())}",
            "",
        ]
        if self._reference_minutes is not None:
            lines.append(f"It is currently {format_clock(int(self._reference_minutes))}.")
        lines.append("Your appointments today, in the order you must visit them:")
        for stop in self._schedule.stops:
            entry = f"{stop.index + 1}. {stop.place}"
            if stop.activity:
                entry += f" — {stop.activity}"
            deadline = self._stop_deadline(stop.index)
            if deadline is not None:
                entry += f" — due by {format_clock(int(deadline))}"
            lines.append(entry)
        total = self._total_deadline()
        if total is not None:
            lines.append(f"Everything must be finished by {format_clock(int(total))}.")
        if self._schedule.dwell_minutes:
            lines.append(f"Plan to spend about {self._schedule.dwell_minutes:g} minutes at each place.")
        lines.append(
            "\nVisit the appointments in this exact order and arrive before each scheduled "
            "time. The clock keeps running while you act."
        )
        return "\n".join(lines)

    def _progress_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        destination = self.destination()
        base = {
            "distance_to_destination_meters": None,
            "reached_destination": None,
            "task_completed": self._next_stop_index >= len(self._targets),
        }
        if not destination or "lat" not in state or "lon" not in state:
            return base
        distance = haversine_meters(state, destination)
        base["distance_to_destination_meters"] = round(distance, 3)
        base["reached_destination"] = distance <= self.config.arrival_radius_meters
        base["current_stop_index"] = min(self._next_stop_index, len(self._targets) - 1)
        return base

    def _pending_extra_context(self, elapsed_seconds: float) -> str | None:
        """Give the agent a watch readout and schedule status on every turn."""
        total = len(self._targets)
        done = min(self._next_stop_index, total)
        lines = [f"Schedule status: {done}/{total} appointments completed."]
        if self._last_sim_minutes is not None:
            lines[0] = (f"Current time: {format_clock(int(self._last_sim_minutes))}. " + lines[0])
        if done < total:
            stop = self._schedule.stops[done]
            nxt = f"Next appointment: {stop.place}"
            if stop.activity:
                nxt += f" ({stop.activity})"
            deadline = self._stop_deadline(done)
            if deadline is not None and self._last_sim_minutes is not None:
                remaining = (deadline - self._last_sim_minutes) * 60.0
                nxt += f", due {format_clock(int(deadline))}"
                if remaining >= 0:
                    nxt += f" — {remaining / 60.0:.0f} minutes left."
                else:
                    nxt += f" — OVERDUE by {-remaining / 60.0:.0f} minutes."
            lines.append(nxt)
        else:
            lines.append("All appointments completed.")
        return "\n".join(lines)

    # ── arrival / order tracking ─────────────────────────────────────────

    def _update_arrivals(self, state: dict[str, Any], step: int) -> None:
        """Record in-order arrivals and out-of-order stop violations for one state."""
        if "lat" not in state or "lon" not in state:
            return
        self._update_clock_from_state(state)
        # Out-of-order detection: entering a *future* stop's radius before finishing the
        # current one. Recorded once per stop; it does not count as reaching that stop.
        for index in range(self._next_stop_index + 1, len(self._targets)):
            if index in self._order_violation_stops:
                continue
            distance = haversine_meters(state, self._targets[index])
            if distance <= self.config.arrival_radius_meters:
                self._order_violation_stops.add(index)
                self._order_violations.append({
                    "stop_index": index, "step": step,
                    "distance_meters": round(distance, 3),
                    "expected_stop_index": self._next_stop_index,
                })
                log.info("[%s] step %d order violation: entered stop %d radius before stop %d",
                         self.task["id"], step, index, self._next_stop_index)
        # In-order arrivals; loop in case several remaining targets share one radius.
        while self._next_stop_index < len(self._targets):
            index = self._next_stop_index
            distance = haversine_meters(state, self._targets[index])
            if distance > self.config.arrival_radius_meters:
                break
            arrival_minutes = self._last_sim_minutes
            deadline = self._stop_deadline(index)
            lateness_seconds = None
            on_time = None
            if deadline is not None and arrival_minutes is not None:
                lateness_seconds = max(0.0, (arrival_minutes - deadline) * 60.0)
                on_time = lateness_seconds <= ON_TIME_GRACE_SECONDS
                if on_time:
                    lateness_seconds = 0.0
            stop = self._schedule.stops[index]
            self._stop_results[index] = {
                "stop_index": index,
                "place": stop.place,
                "activity": stop.activity,
                "deadline": format_clock(int(deadline)) if deadline is not None else None,
                "arrival_time": (format_clock(int(arrival_minutes))
                                 if arrival_minutes is not None else None),
                "reached": True,
                "reached_at_step": step,
                "on_time": on_time,
                "lateness_seconds": (round(lateness_seconds, 1)
                                     if lateness_seconds is not None else None),
                "arrival_distance_meters": round(distance, 3),
            }
            self._next_stop_index += 1
            log.info("[%s] step %d reached stop %d/%d (%s) at %s (deadline %s, on_time=%s)",
                     self.task["id"], step, index + 1, len(self._targets), stop.place,
                     self._stop_results[index]["arrival_time"],
                     self._stop_results[index]["deadline"], on_time)

    # ── episode loop ─────────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        self.task_output_dir.mkdir(parents=True, exist_ok=True)
        initial_state = self.initialize()
        self._setup_clock(initial_state)
        self._update_arrivals(initial_state, step=0)
        self._record_frame(self.sandbox.screenshot(), "initial")
        report: dict[str, Any] | None = None
        try:
            final_state = initial_state
            for step in range(self.config.max_steps):
                if self._next_stop_index >= len(self._targets):
                    break
                record = self._run_one_step(step)
                self._write_partial(initial_state)
                final_state = record.get("state_after", final_state)
                self._update_arrivals(final_state, step=record["step"])
                if record.get("terminated"):
                    log.info("Task %s terminated at schedule stop %d/%d after %d total steps; "
                             "scoring current state", self.task["id"], self._next_stop_index,
                             len(self._targets), len(self.records))
                    break
                if self._next_stop_index >= len(self._targets):
                    log.info("Task %s reached all %d schedule stops at step %d",
                             self.task["id"], len(self._targets), step + 1)
                    break
            else:
                final_state = self.sandbox.get_state()
                self._update_arrivals(final_state, step=self.config.max_steps)
                log.info("[%s] step %d/%d frame=final (max_steps reached) stops_reached=%d/%d",
                         self.task["id"], self.config.max_steps, self.config.max_steps,
                         self._next_stop_index, len(self._targets))
            metrics = self._compute_metrics(initial_state, final_state)
            if metrics.get("reached_destination"):
                completion_step = max(
                    int(result["reached_at_step"])
                    for result in self._stop_results if result and result.get("reached")
                )
                self._mark_task_completed(completion_step, "schedule_completed")
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
        last_stop = self._targets[-1] if self._targets else None
        metrics = compute_common_metrics(self.records, initial_state, final_state, last_stop,
                                         self.config.arrival_radius_meters)
        if last_stop:
            metrics.update(compute_navigation_metrics(final_state, self._start_point(),
                                                      last_stop,
                                                      self.config.arrival_radius_meters))
        reached = [result for result in self._stop_results if result and result["reached"]]
        # Punctuality is judged over EVERY stop that carries a deadline, reached or not:
        # never arriving at a timed appointment must score worse than arriving late, so an
        # unreached timed stop counts as not on time rather than being dropped from the ratio.
        timed_total = sum(
            1 for index in range(len(self._targets)) if self._stop_deadline(index) is not None
        )
        timed_reached = [result for result in self._stop_results
                         if result and result["reached"] and result["deadline"] is not None]
        on_time = [result for result in timed_reached if result["on_time"]]
        lateness = [result["lateness_seconds"] for result in timed_reached
                    if result["lateness_seconds"]]
        completed = self._next_stop_index >= len(self._targets)
        completed_in_order = completed and not self._order_violations
        total_deadline = self._total_deadline()
        finished_within_total = None
        if total_deadline is not None:
            finished_within_total = bool(
                completed and self._last_sim_minutes is not None
                and self._last_sim_minutes <= total_deadline + ON_TIME_GRACE_SECONDS / 60.0
            )
        metrics.update({
            "schedule_stop_count": len(self._targets),
            "schedule_stops_reached": len(reached),
            "schedule_stop_arrival_ratio": (
                round(len(reached) / len(self._targets), 4) if self._targets else 0.0),
            "schedule_completed": completed,
            "schedule_completed_in_order": completed_in_order,
            "schedule_order_violation_count": len(self._order_violations),
            "schedule_order_violated": bool(self._order_violations),
            "schedule_time_windows_parsed": self._schedule.has_time_windows,
            "schedule_clock_active": self._clock_active,
            "schedule_timed_stop_count": timed_total,
            "schedule_on_time_stop_count": len(on_time),
            "schedule_on_time_ratio": (
                round(len(on_time) / timed_total, 4) if timed_total else None),
            "schedule_late_stop_count": len(timed_reached) - len(on_time),
            "schedule_total_lateness_seconds": round(sum(lateness), 1),
            "schedule_max_lateness_seconds": round(max(lateness), 1) if lateness else 0.0,
            "schedule_all_on_time": bool(timed_total) and len(on_time) == timed_total,
            "schedule_total_deadline": (format_clock(int(total_deadline))
                                        if total_deadline is not None else None),
            "schedule_finished_within_total_deadline": finished_within_total,
            # Headline success metric, reusing the navigation aggregation channel:
            # the whole schedule, in order (closure-style hard failures don't exist here).
            "reached_destination": completed_in_order,
        })
        return metrics

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                metrics: dict[str, Any] | None) -> dict[str, Any]:
        report = super()._report(initial_state, final_state, metrics)
        report["start_point"] = self._start_point()
        report["end_point"] = self._targets[-1] if self._targets else None
        report["serialized_start_point_placeholder"] = self.task.get("startPoint")
        report["schedule"] = {
            "parse_status": self._schedule.parse_status,
            "parse_error": self._schedule.parse_error,
            "current_time": (format_clock(self._schedule.current_time_minutes)
                             if self._schedule.current_time_minutes is not None else None),
            "reference_start_time": (format_clock(int(self._reference_minutes))
                                     if self._reference_minutes is not None else None),
            "lead_minutes_when_unstated": (
                DEFAULT_LEAD_MINUTES if self._schedule.current_time_minutes is None
                and self._reference_minutes is not None else None),
            "dwell_minutes": self._schedule.dwell_minutes,
            "stops": [
                result if result is not None else {
                    "stop_index": index,
                    "place": self._schedule.stops[index].place,
                    "activity": self._schedule.stops[index].activity,
                    "deadline": (format_clock(int(d)) if (d := self._stop_deadline(index))
                                 is not None else None),
                    "reached": False,
                    "reached_at_step": None,
                    "on_time": None,
                    "lateness_seconds": None,
                    "arrival_time": None,
                    "arrival_distance_meters": None,
                }
                for index, result in enumerate(self._stop_results)
            ],
            "order_violations": self._order_violations,
        }
        return report
