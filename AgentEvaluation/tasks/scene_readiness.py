"""Heuristic detection of "scene/map tiles not finished streaming in yet" screenshots.

The sandbox streams 3D-tile geometry and imagery asynchronously after a teleport (and after
opening the map). Before those tiles arrive, the screenshot the agent would see is dominated by
one of two near-featureless states:
  - First-person: large flat-shaded/untextured polygon fills (foreground terrain rendered with
    its collision mesh but no imagery draped on it yet), or in the worst case a plain sky-only
    frame with the ground plane rendered as one flat color.
  - Map mode: the map canvas is a single flat background color with no tile imagery at all.

Both cases share one measurable trait relative to a normally-loaded frame: almost no edge/texture
detail anywhere in the image. A fully streamed-in frame -- even one that is mostly sky -- always
has photographic imagery on any building/terrain/road surface, which Canny edge detection picks
up as a non-trivial density of edges. `run_task.py`/`tasks/base.py` previously just slept a fixed
`--exe-boot-wait` / `--post-teleport-wait` duration and hoped that was long enough; this module
lets that wait be adaptive instead: poll screenshots and stop as soon as the scene looks loaded
(or give up at a hard cap so a persistently broken sandbox can't hang forever).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

log = logging.getLogger(__name__)

# Below this fraction of Canny-edge pixels, a frame is considered "featureless" -- i.e. still
# showing placeholder flat-shaded geometry / a blank map canvas rather than streamed-in imagery.
# Calibrated against the existing evaluation corpus (AgentEvaluation/output/tasks/**/frames/*.jpg):
# confirmed-broken frames (blank map canvas, all-black ground plane, untextured foreground rock)
# measured 0.0000-0.0090; normally-loaded frames (including mostly-sky shots) measured >=0.013,
# with the bulk of the distribution above 0.02.
DEFAULT_EDGE_DENSITY_THRESHOLD = 0.010


@dataclass(frozen=True)
class SceneReadiness:
    """Result of analyzing one screenshot for tile/texture load completeness."""

    is_loaded: bool
    edge_density: float
    threshold: float

    def __str__(self) -> str:
        state = "loaded" if self.is_loaded else "NOT loaded"
        return f"scene {state} (edge_density={self.edge_density:.4f}, threshold={self.threshold:.4f})"


def _decode_gray(jpeg_bytes: bytes) -> np.ndarray | None:
    array = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)
    return image


def assess_scene_readiness(jpeg_bytes: bytes,
                            threshold: float = DEFAULT_EDGE_DENSITY_THRESHOLD) -> SceneReadiness:
    """Score one JPEG screenshot for whether tiles/textures have finished streaming in.

    Uses Canny edge density as a proxy for "how much real imagery detail is on screen" --
    untextured flat-shaded placeholder geometry and blank map canvases both produce almost no
    edges, while any normally-loaded frame (first-person or map) has abundant edge detail from
    building facades, road markings, or map tile imagery.
    """
    gray = _decode_gray(jpeg_bytes)
    if gray is None:
        # Can't decode -> treat as not-ready rather than silently proceeding.
        return SceneReadiness(is_loaded=False, edge_density=0.0, threshold=threshold)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(edges.mean()) / 255.0
    return SceneReadiness(is_loaded=edge_density >= threshold, edge_density=edge_density,
                           threshold=threshold)
