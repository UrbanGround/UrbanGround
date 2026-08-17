"""Environmental-condition episode support for weather / time-of-day variant tasks.

Per the task spec these variants reuse the plain Level-1 QA (types 7/8/9) / ShortNav (type 0)
payloads with UNCHANGED prompts: the only difference from the base tasks is the
environmental condition the episode runs under. Unlike the rainy-day variants (RQ-/RN-),
no exposure metric is measured -- the condition is purely an environmental difficulty
modifier, recorded in the metrics for traceability.

Conditions (weather values verified against the deployed build; see
AgentEvaluation/verify_rain_values.py -- set_weather accepts sunny/rainy/thunderstorm/
overcast/cloudy and silently falls back to sunny for anything else):

- TSQ/TSN: thunderstorm
- OCQ/OCN: overcast
- CLQ/CLN: cloudy
- EVQ/EVN: clear dusk  (sunny weather, clock set to 18:30)
- NTQ/NTN: clear night (sunny weather, clock set to 23:30)

The Q-suffixed prefixes are exploration-QA variants, the N-suffixed
ones short-navigation variants (ShortNav payload). The mix-in applies the condition right
after the teleport + scene-load wait and restores the pre-episode weather/clock on exit,
so a reused/attached sandbox never leaks a condition into the next episode.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

# prefix -> (condition key, report task_type name, set_weather value, clock hour or None)
CONDITIONS: dict[str, tuple[str, str, str, int | None]] = {
    "TSQ": ("thunderstorm", "ThunderstormQA", "thunderstorm", None),
    "TSN": ("thunderstorm", "ThunderstormNav", "thunderstorm", None),
    "OCQ": ("overcast", "OvercastQA", "overcast", None),
    "OCN": ("overcast", "OvercastNav", "overcast", None),
    "CLQ": ("cloudy", "CloudyQA", "cloudy", None),
    "CLN": ("cloudy", "CloudyNav", "cloudy", None),
    "EVQ": ("dusk", "DuskQA", "sunny", 18),
    "EVN": ("dusk", "DuskNav", "sunny", 18),
    "NTQ": ("night", "NightQA", "sunny", 23),
    "NTN": ("night", "NightNav", "sunny", 23),
}
# Clock minutes are fixed at :30 for both time-of-day conditions.
CONDITION_CLOCK_MINUTE = 30

CONDITION_QA_PREFIXES = frozenset(prefix for prefix in CONDITIONS if prefix.endswith("Q"))
CONDITION_NAV_PREFIXES = frozenset(prefix for prefix in CONDITIONS if prefix.endswith("N"))


def condition_for_task(task: dict[str, Any], expected_suffix: str) -> tuple[str, str, str, int | None]:
    """Resolve a task payload's ID prefix to its condition entry, with validation."""
    prefix = str(task.get("id", "")).split("-", 1)[0].upper()
    entry = CONDITIONS.get(prefix)
    if entry is None or not prefix.endswith(expected_suffix):
        raise ValueError(
            f"Task {task.get('id')!r} has no registered environmental condition "
            f"for a {'QA' if expected_suffix == 'Q' else 'navigation'} variant"
        )
    return entry


class ConditionEpisodeMixin:
    """Apply/restore an environmental condition; list before the concrete base for MRO."""

    def _setup_condition(self) -> None:
        """Apply the condition (weather and/or clock) and snapshot what actually took."""
        key, name, weather, hour = self._condition
        self._condition_applied = False
        self._condition_baseline: dict[str, Any] = {}
        try:
            before = self.sandbox.get_state()
            self._condition_baseline = {
                "weather": before.get("weather"),
                "time": before.get("time"),
            }
            self.sandbox.set_weather(weather)
            if hour is not None:
                self.sandbox.set_time(hour, CONDITION_CLOCK_MINUTE)
            after = self.sandbox.get_state()
            self._condition_state_weather = after.get("weather")
            self._condition_state_time = after.get("time")
            self._condition_applied = self._condition_state_weather == weather and (
                hour is None or bool(self._condition_state_time)
            )
            log.info("[%s] Condition %s applied: weather=%s time=%s",
                     self.task["id"], key, self._condition_state_weather,
                     self._condition_state_time)
        except Exception as exc:  # noqa: BLE001 - an older build must not abort the episode
            log.warning("[%s] applying condition %s failed (%s); metrics will report "
                        "not-applied", self.task["id"], key, exc)

    def initialize(self) -> dict[str, Any]:
        state = super().initialize()
        self._setup_condition()
        return state

    def _exit_task(self) -> None:
        """Restore the pre-episode weather (best effort) before unloading the task."""
        try:
            baseline = getattr(self, "_condition_baseline", None)
            if getattr(self, "_condition_applied", False) and baseline:
                if baseline.get("weather"):
                    self.sandbox.set_weather(str(baseline["weather"]))
                clock = baseline.get("time")
                if isinstance(clock, str) and clock.count(":") == 2:
                    self.sandbox.set_time(int(clock[:2]), int(clock[3:5]))
        except Exception as exc:  # noqa: BLE001 - cleanup must not hide the task result
            log.warning("[%s] restoring baseline condition failed (ignored): %s",
                        self.task["id"], exc)
        super()._exit_task()

    def _condition_metrics(self) -> dict[str, Any]:
        key, _name, weather, hour = self._condition
        return {
            "condition": key,
            "condition_weather": weather,
            "condition_clock": (f"{hour:02d}:{CONDITION_CLOCK_MINUTE:02d}"
                                if hour is not None else None),
            "condition_applied": getattr(self, "_condition_applied", False),
            "condition_state_weather": getattr(self, "_condition_state_weather", None),
            "condition_state_time": getattr(self, "_condition_state_time", None),
        }
