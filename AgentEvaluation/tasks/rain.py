"""Shared rain-weather episode support for rainy-day task evaluators.

The sandbox tracks rain exposure natively in every /state payload (`is_raining`,
`being_rained_on`, `has_overhead_shelter`, `rain_exposure_seconds`, ...) and the weather
can be switched via the `set_weather` action. Rainy-day evaluators (RQ-*/RN-* task IDs)
mix this class in ahead of their concrete base so that:

- `initialize()` switches the weather to rain right after the teleport + scene-load wait
  (so the fixed scene-streaming time is never counted as rain exposure), and records the
  sandbox's cumulative `rain_exposure_seconds` counter as the episode baseline;
- `_exit_task()` restores clear weather so a reused/attached sandbox never leaks rain
  into the next episode;
- `_rain_metrics()` reports the share of action time the agent spent being rained on,
  both as a per-step ratio (state_after.being_rained_on weighted by action duration) and
  as the sandbox-native counter delta.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

# Verified against the deployed build (AgentEvaluation/verify_rain_values.py): the
# set_weather action accepts sunny/rainy/thunderstorm/overcast/cloudy; anything else
# ("rain", "drizzle", Chinese names, ...) silently falls back to sunny. "rainy" turns
# on is_raining with intensity ~0.55; "thunderstorm" is the heavy variant (~0.95).
RAIN_WEATHER = "rainy"
CLEAR_WEATHER = "sunny"


class RainEpisodeMixin:
    """Rain setup/teardown/metrics; list before the concrete evaluator for MRO."""

    def _setup_rain(self) -> None:
        """Switch the sandbox to rainy weather (best effort) and baseline the counter."""
        self._rain_active = False
        self._rain_baseline_exposure: float | None = None
        try:
            self.sandbox.set_weather(RAIN_WEATHER)
            state = self.sandbox.get_state()
            # Trust the action even if this build's /state predates the is_raining field.
            self._rain_active = bool(state.get("is_raining", True))
            self._rain_baseline_exposure = float(state.get("rain_exposure_seconds") or 0.0)
            log.info("[%s] Rain weather active: is_raining=%s intensity=%s",
                     self.task["id"], state.get("is_raining"), state.get("rain_intensity"))
        except Exception as exc:  # noqa: BLE001 - an older build without set_weather must not abort
            log.warning("[%s] set_weather(%s) failed (%s); rain metrics will report inactive",
                        self.task["id"], RAIN_WEATHER, exc)

    def initialize(self) -> dict[str, Any]:
        state = super().initialize()
        self._setup_rain()
        return state

    def _exit_task(self) -> None:
        """Restore clear weather (best effort) before unloading the task."""
        try:
            if getattr(self, "_rain_active", False):
                self.sandbox.set_weather(CLEAR_WEATHER)
        except Exception as exc:  # noqa: BLE001 - cleanup must not hide the task result
            log.warning("[%s] restoring clear weather failed (ignored): %s", self.task["id"], exc)
        super()._exit_task()

    def _rain_metrics(self) -> dict[str, Any]:
        durations = [max(0.0, float(record.get("duration_seconds", 0.0)))
                     for record in self.records]
        total_time = sum(durations)
        rain_time = sum(
            duration for record, duration in zip(self.records, durations)
            if bool(record.get("state_after", {}).get("being_rained_on"))
        )
        sheltered_time = sum(
            duration for record, duration in zip(self.records, durations)
            if bool(record.get("state_after", {}).get("has_overhead_shelter"))
        )
        exposed_steps = sum(
            bool(record.get("state_after", {}).get("being_rained_on"))
            for record in self.records
        )
        # Sandbox-native cumulative counter delta: baseline (post set_weather) -> last
        # recorded state. Authoritative cross-check for the per-step ratio above.
        counter_delta = None
        baseline = getattr(self, "_rain_baseline_exposure", None)
        if baseline is not None and self.records:
            final_exposure = self.records[-1].get("state_after", {}).get("rain_exposure_seconds")
            if final_exposure is not None:
                counter_delta = round(float(final_exposure) - baseline, 3)
        return {
            "rain_weather_active": getattr(self, "_rain_active", False),
            "rain_exposure_seconds": round(rain_time, 3),
            "rain_exposure_time_ratio": round(rain_time / total_time, 4) if total_time else 0.0,
            "rain_exposed_step_count": exposed_steps,
            "rain_exposed_step_ratio": (
                round(exposed_steps / len(self.records), 4) if self.records else 0.0),
            "rain_exposure_counter_seconds": counter_delta,
            "sheltered_seconds": round(sheltered_time, 3),
            "sheltered_time_ratio": (
                round(sheltered_time / total_time, 4) if total_time else 0.0),
        }
