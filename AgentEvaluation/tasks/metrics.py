"""Metrics shared by all sandbox task evaluators."""

from __future__ import annotations

import math
from typing import Any


def haversine_meters(first: dict[str, Any], second: dict[str, Any]) -> float:
    """Return horizontal great-circle distance between two state/point dictionaries."""
    lat1, lon1 = math.radians(float(first["lat"])), math.radians(float(first["lon"]))
    lat2, lon2 = math.radians(float(second["lat"])), math.radians(float(second["lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000.0 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def compute_common_metrics(records: list[dict[str, Any]], initial_state: dict[str, Any],
                           final_state: dict[str, Any], destination: dict[str, Any] | None = None,
                           arrival_radius_m: float = 15.0) -> dict[str, Any]:
    """Compute reusable trajectory, sidewalk, mode, and destination metrics."""
    states = [initial_state] + [record.get("state_after", {}) for record in records]
    valid_states = [state for state in states if "lat" in state and "lon" in state]
    path_length = sum(haversine_meters(a, b) for a, b in zip(valid_states, valid_states[1:]))
    durations = [max(0.0, float(record.get("duration_seconds", 0.0))) for record in records]
    total_time = sum(durations)
    sidewalk_time = sum(
        duration for record, duration in zip(records, durations)
        if bool(record.get("state_after", {}).get("on_sidewalk"))
    )
    map_steps = sum(record.get("state_after", {}).get("mode") == "map" for record in records)
    termination = next((record for record in records if record.get("terminated")), None)
    metrics: dict[str, Any] = {
        "elapsed_action_seconds": round(total_time, 3),
        "sidewalk_seconds": round(sidewalk_time, 3),
        "sidewalk_time_ratio": round(sidewalk_time / total_time, 4) if total_time else 0.0,
        "sidewalk_state_ratio": round(
            sum(bool(state.get("on_sidewalk")) for state in valid_states) / len(valid_states), 4
        ) if valid_states else 0.0,
        "path_length_meters": round(path_length, 3),
        "displacement_meters": round(haversine_meters(initial_state, final_state), 3),
        "map_step_count": map_steps,
        "first_person_step_count": len(records) - map_steps,
        "agent_terminated": termination is not None,
        "agent_termination_step": termination.get("step") if termination is not None else None,
    }
    if destination and destination.get("lat") and destination.get("lon"):
        distance = haversine_meters(final_state, destination)
        metrics.update({
            "distance_to_destination_meters": round(distance, 3),
            "reached_destination": distance <= arrival_radius_m,
            "arrival_radius_meters": arrival_radius_m,
        })
    else:
        metrics.update({"distance_to_destination_meters": None, "reached_destination": None})
    return metrics


def mst_route_length_meters(origin: dict[str, Any],
                            points: list[dict[str, Any]]) -> float:
    """Minimum spanning tree length over {origin} ∪ points, using haversine edges.

    The MST length is a cheap lower bound on the optimal multi-stop route (any route
    visiting all points contains a spanning tree, so optimal >= MST). MultipointNav
    reports it as the reference distance a perfectly-planned route would need at minimum,
    and compares the agent's actual path length against it.
    """
    nodes = [origin, *points]
    if len(nodes) <= 1:
        return 0.0
    in_tree = {0}
    total = 0.0
    while len(in_tree) < len(nodes):  # Prim's algorithm; n <= 5 here, keep it simple
        best_distance, best_node = None, None
        for i in in_tree:
            for j in range(len(nodes)):
                if j in in_tree:
                    continue
                distance = haversine_meters(nodes[i], nodes[j])
                if best_distance is None or distance < best_distance:
                    best_distance, best_node = distance, j
        total += best_distance
        in_tree.add(best_node)
    return total


def compute_navigation_metrics(final_state: dict[str, Any], origin: dict[str, Any],
                               destination: dict[str, Any],
                               arrival_radius_m: float = 15.0) -> dict[str, Any]:
    """Compute navigation-specific success metrics for ShortNav/LongNav episodes.

    - `original_distance_meters`: straight-line distance from the task's labeled start point
      to its destination (the denominator used to normalize remaining progress).
    - `remaining_distance_meters`: straight-line distance from the final agent position to
      the destination.
    - `remaining_distance_ratio`: remaining distance divided by the original distance, i.e.
      the fraction of the original trip that is still left to travel. 0 means the agent
      ended exactly at the destination; 1 means it made no net progress (or moved away by
      an amount matching the original distance); values above 1 indicate the agent ended up
      farther from the destination than its starting point.
    - `reached_destination`: whether the final position is within `arrival_radius_m` of the
      destination.
    """
    original_distance = haversine_meters(origin, destination)
    remaining_distance = haversine_meters(final_state, destination)
    if original_distance > 0:
        remaining_ratio = remaining_distance / original_distance
    else:
        # Degenerate task where start and destination coincide: any remaining distance
        # represents complete failure to stay at the destination.
        remaining_ratio = 0.0 if remaining_distance <= arrival_radius_m else 1.0
    return {
        "original_distance_meters": round(original_distance, 3),
        "remaining_distance_meters": round(remaining_distance, 3),
        "remaining_distance_ratio": round(remaining_ratio, 6),
        "reached_destination": remaining_distance <= arrival_radius_m,
        "arrival_radius_meters": arrival_radius_m,
    }
