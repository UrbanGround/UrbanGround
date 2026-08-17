"""Geometry helpers for road-closure polyline crossing detection.

`restrictedZones` in a CN-* (constrained navigation / dynamic road closure) task describes
one or more road-closure polylines ("closure segments"): an ordered list of WGS84 vertices whose
consecutive pairs form the individual closure segments. These are *not* closed polygons
(the last vertex does not repeat the first), so "crossing the closure" means the agent's
movement crossed any single edge of any polyline, not that it entered an enclosed area.

All crossing math is done in a local metric (east/north, in meters) tangent-plane
projection centered on the task's start point, which is accurate enough for the
few-hundred-meter scale of one episode and avoids the branch-cut/pole issues of doing
segment intersection directly in lat/lon space.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

_EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class LocalProjector:
    """Equirectangular local tangent-plane projection anchored at one lat/lon origin."""

    origin_lat: float
    origin_lon: float

    def to_local(self, lat: float, lon: float) -> tuple[float, float]:
        """Return (east_meters, north_meters) relative to the origin."""
        lat_rad = math.radians(self.origin_lat)
        east = math.radians(lon - self.origin_lon) * _EARTH_RADIUS_M * math.cos(lat_rad)
        north = math.radians(lat - self.origin_lat) * _EARTH_RADIUS_M
        return east, north


def _point_local(projector: LocalProjector, point: dict[str, Any]) -> tuple[float, float] | None:
    if point is None or "lat" not in point or "lon" not in point:
        return None
    try:
        lat, lon = float(point["lat"]), float(point["lon"])
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lon)):
        return None
    return projector.to_local(lat, lon)


def _segments_intersect(p1: tuple[float, float], p2: tuple[float, float],
                        p3: tuple[float, float], p4: tuple[float, float]) -> bool:
    """Return True iff closed segments p1-p2 and p3-p4 intersect (including touching)."""

    def cross(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def on_segment(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> bool:
        return (min(a[0], b[0]) - 1e-9 <= p[0] <= max(a[0], b[0]) + 1e-9
                and min(a[1], b[1]) - 1e-9 <= p[1] <= max(a[1], b[1]) + 1e-9)

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    if abs(d1) < 1e-9 and on_segment(p1, p3, p4):
        return True
    if abs(d2) < 1e-9 and on_segment(p2, p3, p4):
        return True
    if abs(d3) < 1e-9 and on_segment(p3, p1, p2):
        return True
    if abs(d4) < 1e-9 and on_segment(p4, p1, p2):
        return True
    return False


def describe_closures(restricted_zones: list[dict[str, Any]] | None) -> str:
    """Render `restrictedZones` as a human-readable, LLM-facing description.

    Each polyline is summarized by its label and its ordered vertex coordinates, so the agent
    (and the map it can open in-sim) can be cross-referenced against this text without needing
    the raw geo JSON.
    """
    zones = restricted_zones or []
    if not zones:
        return "No road closures are currently in effect."
    lines = []
    for index, zone in enumerate(zones, start=1):
        label = str(zone.get("label") or f"closure_{index}")
        vertices = zone.get("vertices") or []
        points = "; ".join(
            f"({float(vertex.get('lat', 0.0)):.6f}, {float(vertex.get('lon', 0.0)):.6f})"
            for vertex in vertices
        )
        lines.append(f"- {label}: closure line through waypoints [{points}]")
    return "\n".join(lines)


def closure_edges(restricted_zones: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Flatten every polyline's consecutive vertex pairs into individually labeled edges."""
    edges: list[dict[str, Any]] = []
    for zone in restricted_zones or []:
        label = str(zone.get("label") or "restricted_zone")
        vertices = zone.get("vertices") or []
        for index in range(len(vertices) - 1):
            edges.append({
                "label": label,
                "edge_index": index,
                "start": vertices[index],
                "end": vertices[index + 1],
            })
    return edges


class ClosureCrossingDetector:
    """Detects whether an agent's movement segment crosses any road-closure edge."""

    def __init__(self, restricted_zones: list[dict[str, Any]] | None, origin: dict[str, Any]):
        self.edges = closure_edges(restricted_zones)
        origin_lat = float(origin.get("lat", 0.0)) if origin else 0.0
        origin_lon = float(origin.get("lon", 0.0)) if origin else 0.0
        self.projector = LocalProjector(origin_lat, origin_lon)
        self._edges_local: list[tuple[str, int, tuple[float, float], tuple[float, float]]] = []
        for edge in self.edges:
            start = _point_local(self.projector, edge["start"])
            end = _point_local(self.projector, edge["end"])
            if start is not None and end is not None:
                self._edges_local.append((edge["label"], edge["edge_index"], start, end))

    @property
    def has_edges(self) -> bool:
        return bool(self._edges_local)

    def crossed_edges(self, previous_state: dict[str, Any] | None,
                      current_state: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Return every closure edge crossed by the movement from previous to current state."""
        if not self._edges_local or previous_state is None or current_state is None:
            return []
        prev_point = _point_local(self.projector, previous_state)
        curr_point = _point_local(self.projector, current_state)
        if prev_point is None or curr_point is None or prev_point == curr_point:
            return []
        crossed: list[dict[str, Any]] = []
        for label, edge_index, edge_start, edge_end in self._edges_local:
            if _segments_intersect(prev_point, curr_point, edge_start, edge_end):
                crossed.append({"label": label, "edge_index": edge_index})
        return crossed
