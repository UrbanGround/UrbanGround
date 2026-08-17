"""Shared pedestrian-simulation episode support for pedestrian-enabled task evaluators.

The sandbox simulates pedestrians on demand: the `enable_pedestrians` action spawns them
on the pedestrian network, and every /state payload carries the telemetry
(`pedestrians_active`, `pedestrian_count`, `pedestrian_collisions`). Pedestrian-enabled
navigation evaluators (PS-*/PL-* task IDs) mix this class in ahead of their concrete base
so that:

- `initialize()` enables pedestrians right after the teleport + scene-load wait (so
  pedestrians never spawn into an unfinished scene) and baselines the cumulative
  `pedestrian_collisions` counter;
- `_exit_task()` disables pedestrians again so a reused/attached sandbox never leaks
  them into the next episode;
- `_pedestrian_metrics()` reports the episode's collision count (sandbox counter delta)
  plus per-step pedestrian-presence context (mean/peak visible crowd size).

Per the task spec, the prompts and task payloads are identical to the plain ShortNav /
LongNav tasks -- pedestrians are purely an environmental condition added on top.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class PedestrianEpisodeMixin:
    """Pedestrian setup/teardown/metrics; list before the concrete evaluator for MRO."""

    def _setup_pedestrians(self) -> None:
        """Enable pedestrian simulation (best effort) and baseline the collision counter."""
        self._pedestrians_active = False
        self._pedestrian_baseline_collisions: int = 0
        try:
            self.sandbox.enable_pedestrians()
            state = self.sandbox.get_state()
            # Trust the action even if this build's /state predates the telemetry fields.
            self._pedestrians_active = bool(state.get("pedestrians_active", True))
            self._pedestrian_baseline_collisions = int(state.get("pedestrian_collisions") or 0)
            log.info("[%s] Pedestrians active: pedestrians_active=%s count=%s",
                     self.task["id"], state.get("pedestrians_active"),
                     state.get("pedestrian_count"))
        except Exception as exc:  # noqa: BLE001 - an older build without the action must not abort
            log.warning("[%s] enable_pedestrians failed (%s); pedestrian metrics will "
                        "report inactive", self.task["id"], exc)

    def initialize(self) -> dict[str, Any]:
        state = super().initialize()
        self._setup_pedestrians()
        return state

    def _exit_task(self) -> None:
        """Disable pedestrians (best effort) before unloading the task."""
        try:
            if getattr(self, "_pedestrians_active", False):
                self.sandbox.disable_pedestrians()
        except Exception as exc:  # noqa: BLE001 - cleanup must not hide the task result
            log.warning("[%s] disabling pedestrians failed (ignored): %s", self.task["id"], exc)
        super()._exit_task()

    def _pedestrian_metrics(self) -> dict[str, Any]:
        states = [record.get("state_after", {}) for record in self.records]
        counts = [int(state["pedestrian_count"]) for state in states
                  if state.get("pedestrian_count") is not None]
        # Episode collision count: sandbox counter delta between the post-enable baseline
        # and the last recorded state; falls back to the raw last reading when the
        # baseline was never captured.
        collisions = None
        last = next((state.get("pedestrian_collisions") for state in reversed(states)
                     if state.get("pedestrian_collisions") is not None), None)
        if last is not None:
            collisions = int(last) - getattr(self, "_pedestrian_baseline_collisions", 0)
        # Steps during which the cumulative counter increased (it stays non-zero forever
        # after the first collision, so a plain truthiness check would overcount).
        readings = [int(state["pedestrian_collisions"]) for state in states
                    if state.get("pedestrian_collisions") is not None]
        baseline = getattr(self, "_pedestrian_baseline_collisions", 0)
        collision_steps = sum(
            1 for previous, current in zip([baseline] + readings, readings)
            if current > previous
        )
        return {
            "pedestrians_active": getattr(self, "_pedestrians_active", False),
            "pedestrian_collision_count": collisions,
            "pedestrian_collided": bool(collisions),
            "pedestrian_collision_step_count": collision_steps,
            "pedestrian_count_mean": (
                round(sum(counts) / len(counts), 2) if counts else None),
            "pedestrian_count_max": max(counts) if counts else None,
        }
