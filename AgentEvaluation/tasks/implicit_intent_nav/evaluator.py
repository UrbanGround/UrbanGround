"""Evaluator for TaskType.ImplicitIntentNav (II task IDs).

II tasks currently serialize as numeric type 12 because the Unity task editor historically
used that slot before DynamicClosureNav occupied it. The numeric field therefore cannot be
used alone: registry.create_evaluator routes II-* IDs here while CN-* IDs with the same
numeric type continue to use DynamicClosureNav. The task's meaningful fields are:

- `description`: an everyday-life goal that only implies the destination category;
- `exploreStart`: the editor-selected actual starting position;
- `endPoint`: the hidden editor-labeled target POI used only for scoring;
- `exploreDurationMinutes`: the intended exploration budget, reported as metadata;
- `poiCategory`: editor metadata retained for analysis, not disclosed to the model.

`startPoint` is a serialized placeholder of zero coordinates on all current II payloads and
must not be used for teleport or navigation metrics.
"""

from __future__ import annotations

from typing import Any

from ..base import BaseNavEvaluator, format_geo_point
from .prompt import SYSTEM_PROMPT


class ImplicitIntentNavEvaluator(BaseNavEvaluator):
    """Evaluate inferring a POI category from an implicit goal and navigating to it."""

    task_type = 12
    task_name = "ImplicitIntentNav"
    task_id_prefix = "II-"

    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @staticmethod
    def _nonzero_geo_point(point: Any) -> bool:
        """Whether a serialized GeoPoint is usable (the editor writes 0,0 placeholders)."""
        return (
            isinstance(point, dict)
            and abs(float(point.get("lat", 0.0))) > 1e-12
            and abs(float(point.get("lon", 0.0))) > 1e-12
        )

    def _start_point(self) -> dict[str, Any]:
        # Current II payloads leave `startPoint` as a zero-coordinate placeholder and put the
        # real starting position in `exploreStart`. Fall back to `startPoint` only for future
        # tasks where the editor starts filling it in.
        if self._nonzero_geo_point(self.task.get("exploreStart")):
            return self.task["exploreStart"]
        if self._nonzero_geo_point(self.task.get("startPoint")):
            return self.task["startPoint"]
        raise ValueError(
            f"Implicit-intent task {self.task['id']} has no usable exploreStart/startPoint"
        )

    def task_instructions(self) -> str:
        intent = str(self.task.get("description", "")).strip()
        return (
            "[Implicit Intent Navigation Task]\n"
            f"Current location: {format_geo_point(self._start_point())}\n\n"
            f"Everyday goal: {intent}\n\n"
            "Infer the type of place that would satisfy this goal, find a suitable nearby "
            "POI from visible signs and map evidence, and navigate to it. The destination "
            "category is intentionally not stated directly. You may use the map, visual "
            "inspection, and first-person movement in any combination."
        )

    def task_specific_metrics(self) -> dict[str, Any]:
        navigate_calls = sum(record["action"].get("action") == "navigate" for record in self.records)
        map_steps = sum(
            record["action"].get("action") in {
                "open_map", "map_select", "map_pan", "map_zoom", "map_orbit",
                "navigate", "clear_route", "close_map",
            }
            for record in self.records
        )
        inspection_steps = sum(
            record["action"].get("action") in {"look", "map_orbit"}
            for record in self.records
        )
        poi_terms = (
            "bank", "atm", "optician", "eye", "pharmacy", "clinic", "store", "shop",
            "supermarket", "restaurant", "cafe", "market", "station", "mall", "name",
            "sign", "logo", "entrance",
        )
        evidence_steps = sum(
            any(term in record["observation"].lower() for term in poi_terms)
            for record in self.records
        )
        total = len(self.records)
        return {
            "implicit_intent_text": str(self.task.get("description", "")).strip(),
            "implicit_intent_poi_category": self.task.get("poiCategory"),
            "implicit_intent_explore_duration_minutes": self.task.get("exploreDurationMinutes"),
            "navigate_call_count": navigate_calls,
            "used_navigation_api": navigate_calls > 0,
            "map_usage_step_count": map_steps,
            "used_map": map_steps > 0,
            "poi_inspection_step_count": inspection_steps,
            "poi_evidence_step_count": evidence_steps,
            "poi_evidence_step_ratio": round(evidence_steps / total, 4) if total else 0.0,
        }

    def _report(self, initial_state: dict[str, Any], final_state: dict[str, Any],
                metrics: dict[str, Any] | None) -> dict[str, Any]:
        report = super()._report(initial_state, final_state, metrics)
        # `start_point` in the base report should mean the point actually used for teleport,
        # not the all-zero serialized placeholder retained only for schema compatibility.
        report["start_point"] = self._start_point()
        report["serialized_start_point_placeholder"] = self.task.get("startPoint")
        report["serialized_type_conflict"] = (
            "II task payloads currently use numeric type 12, which is also used by "
            "DynamicClosureNav; evaluator selection used the II- task ID prefix."
        )
        return report
