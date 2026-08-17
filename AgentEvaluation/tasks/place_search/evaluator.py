"""Evaluator for TaskType.PoiSearch (PS task IDs, numeric type 3) -- 地点类型搜寻.

PS tasks ask the agent to find and travel to a nearby place of a requested type or name
("Take me to City Hall.", "Go to the nearby park.", "Find the nearest public toilet."):

- `searchOrigin` is the editor-selected starting position (the search starts here);
- `poiCategory` is the LandsD POI category of the requested place type, kept as metadata;
- there is intentionally NO labeled target: `endPoint` is a zero placeholder on every
  current PS payload, and /task/enter returns no end_points for type 3.

Verified against the deployed build (see AgentEvaluation/verify_place_search.py): the
sandbox's `identify_location` action depends on an external geocoding API that is
unreachable from inside the VM ("timeout waiting for API"), while `where_am_i` only
returns the current street/surface name. There is therefore no privileged ground-truth
channel to score against, so completion is judged by the evaluation LLM from the agent's
final view plus its final surface, i.e. whether the agent stopped at the entrance of /
inside / immediately in front of a facility matching the requested place.

Metrics center on the judgement (`answer_correct` mirrors `placesearch_found` so the
QA-style accuracy aggregation picks it up) plus search-behavior indicators (map usage,
inspection turns, and steps whose observation mentions the requested place).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from ..metrics import compute_common_metrics
from .prompt import JUDGE_PROMPT, SYSTEM_PROMPT

log = logging.getLogger(__name__)

_STOP_WORDS = {
    "take", "go", "the", "a", "an", "to", "me", "please", "find", "nearest", "nearby",
    "near", "is", "there", "where", "one", "i", "want", "need", "can", "you", "thanks",
    "thank", "lead", "way", "look", "for", "out", "visit", "hang", "time", "it's",
    "its", "and", "take me", "go to",
}


class PlaceSearchEvaluator(BaseNavEvaluator):
    """Evaluate finding and reaching a requested place type, judged by the LLM."""

    task_type = 3
    task_name = "PlaceSearch"
    task_id_prefix = "PS-"

    # ── evaluator interface ──────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def _start_point(self) -> dict[str, Any]:
        return self.task["searchOrigin"]

    def destination(self) -> dict[str, Any] | None:
        """PS tasks have no labeled target; distance readouts stay None."""
        return None

    def task_instructions(self) -> str:
        return (
            "[Place-Type Search Task]\n"
            f"Current location: {format_geo_point(self._start_point())}\n\n"
            f"Request: {str(self.task.get('description', '')).strip()}\n\n"
            "Locate a suitable nearby place that satisfies the request, navigate to it, "
            "and stop at its entrance or in front of its signage. You may use the map, "
            "visual inspection, and first-person movement in any combination."
        )

    def _pending_extra_context(self, elapsed_seconds: float) -> str | None:
        return (
            "Reminder: your goal is to reach the requested place "
            f"({str(self.task.get('description', '')).strip()}). If you believe you have "
            "arrived, stop there and make sure the place or its signage is clearly visible."
        )

    # ── final judgement ──────────────────────────────────────────────────

    def _final_surface(self, final_state: dict[str, Any]) -> str:
        """Best-effort current street name: where_am_i first, /state surface as fallback."""
        try:
            reply = self.sandbox.where_am_i()
            text = str(reply.get("action") or "").strip()
            if text:
                return text
        except Exception as exc:  # noqa: BLE001 - surface fallback below
            log.warning("[%s] where_am_i failed (using state surface): %s", self.task["id"], exc)
        return str(final_state.get("surface") or "unknown")

    def _judge(self, final_state: dict[str, Any]) -> dict[str, Any]:
        """Ask the evaluation LLM whether the agent's final view shows arrival."""
        screenshot = self.sandbox.screenshot()
        self._record_frame(screenshot, "final_judge")
        surface = self._final_surface(final_state)
        prompt = JUDGE_PROMPT.format(
            description=str(self.task.get("description", "")).strip(), surface=surface,
        )
        last_error = ""
        for _attempt in range(self.config.retry_count + 1):
            try:
                raw = self.llm.complete_with_image(prompt, screenshot)
                payload = self.llm.parse_json_object(raw)
                found = bool(payload.get("found"))
                confidence = str(payload.get("confidence", "")).strip().lower() or "unknown"
                reason = str(payload.get("reason", "")).strip()[:1000]
                if not reason:
                    raise ValueError("judge reason must be non-empty")
                log.info("[%s] judge: found=%s confidence=%s reason=%s",
                         self.task["id"], found, confidence, reason)
                return {"found": found, "confidence": confidence, "reason": reason,
                        "surface": surface, "judge_error": None}
            except Exception as exc:  # noqa: BLE001 - retry, then degrade gracefully
                last_error = str(exc)
                log.warning("[%s] judge attempt failed: %s", self.task["id"], exc)
        return {"found": False, "confidence": "judge_error", "reason": "",
                "surface": surface, "judge_error": last_error}

    # ── episode loop ─────────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        self.task_output_dir.mkdir(parents=True, exist_ok=True)
        initial_state = self.initialize()
        self._record_frame(self.sandbox.screenshot(), "initial")
        report: dict[str, Any] | None = None
        try:
            final_state = initial_state
            for step in range(self.config.max_steps):
                record = self._run_one_step(step)
                self._write_partial(initial_state)
                final_state = record.get("state_after", final_state)
                if record.get("terminated"):
                    log.info("Task %s terminated place search at step %d after %d total steps; "
                             "running final judge", self.task["id"], step + 1,
                             len(self.records))
                    break
            judgement = self._judge(final_state)
            if judgement.get("found"):
                self._mark_task_completed(
                    len(self.records), "place_judged_found", self._elapsed_episode_seconds()
                )
            metrics = {
                **compute_common_metrics(self.records, initial_state, final_state, None,
                                         self.config.arrival_radius_meters),
                **self._search_metrics(judgement),
            }
            self._finalize_outcome_metrics(metrics)
            report = self._report(initial_state, final_state, judgement, metrics)
            self._write(report)
            return report
        finally:
            self._exit_task()
            self._finalize_video(report)

    # ── metrics / report ─────────────────────────────────────────────────

    def _target_terms(self) -> list[str]:
        """Significant words from the request, used for observation-mention stats."""
        words = re.findall(r"[a-zA-Z']+", str(self.task.get("description", "")).lower())
        return sorted({word for word in words if len(word) >= 4 and word not in _STOP_WORDS})

    def _search_metrics(self, judgement: dict[str, Any]) -> dict[str, Any]:
        total = len(self.records)
        map_steps = sum(
            record["action"].get("action") in {
                "open_map", "map_select", "map_pan", "map_zoom", "map_orbit", "close_map",
            }
            for record in self.records
        )
        inspection_steps = sum(
            record["action"].get("action") in {"look", "map_orbit"}
            for record in self.records
        )
        terms = self._target_terms()
        mention_steps = sum(
            any(term in record["observation"].lower() for term in terms)
            for record in self.records
        ) if terms else 0
        found = bool(judgement["found"])
        return {
            # QA-style aggregation channel: the batch accuracy for PlaceSearch tasks is
            # the fraction judged to have arrived at the requested place.
            "answer_correct": found,
            "placesearch_found": found,
            "placesearch_confidence": judgement["confidence"],
            "placesearch_judge_reason": judgement["reason"],
            "placesearch_judge_error": judgement["judge_error"],
            "placesearch_final_surface": judgement["surface"],
            "placesearch_poi_category": self.task.get("poiCategory"),
            "placesearch_map_step_count": map_steps,
            "placesearch_inspection_step_count": inspection_steps,
            "placesearch_target_mention_step_count": mention_steps,
            "placesearch_target_mention_step_ratio": (
                round(mention_steps / total, 4) if total else 0.0),
        }

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                judgement: dict[str, Any] | None,
                metrics: dict[str, Any] | None) -> dict[str, Any]:
        report = super()._report(initial_state, final_state, metrics)
        report["start_point"] = self._start_point()
        report["end_point"] = None
        report["serialized_end_point_placeholder"] = self.task.get("endPoint")
        if judgement is not None:
            report["answer"] = {
                "answer": "found" if judgement["found"] else "not_found",
                "reason": judgement["reason"],
                "confidence": judgement["confidence"],
            }
        return report

    def _write_partial(self, initial_state: dict[str, Any]) -> None:
        self._write(self._report(initial_state, self.records[-1]["state_after"], None, None))
