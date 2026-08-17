"""Frame collection and MP4 encoding for task evaluation episodes."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image

from sandbox.agent_client import decode_data_url

log = logging.getLogger(__name__)


class EpisodeVideoRecorder:
    """Persist ordered JPEG observations and encode them as one complete episode video."""

    def __init__(self, frame_dir: Path, video_path: Path, fps: float = 4.0,
                 keep_frames: bool = False):
        self.video_path = video_path
        self.fps = fps
        self.keep_frames = keep_frames
        self.frame_paths: list[Path] = []
        self._temporary_dir: tempfile.TemporaryDirectory[str] | None = None
        if keep_frames:
            self.frame_dir = frame_dir
            self.frame_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._temporary_dir = tempfile.TemporaryDirectory(prefix="agent-evaluation-frames-")
            self.frame_dir = Path(self._temporary_dir.name)

    def add_jpeg(self, image: bytes, label: str) -> Path:
        safe_label = "".join(character if character.isalnum() or character in "-_" else "_"
                             for character in label)
        path = self.frame_dir / f"{len(self.frame_paths):05d}_{safe_label}.jpg"
        path.write_bytes(image)
        self.frame_paths.append(path)
        return path

    def add_data_urls(self, images: list[str], label: str) -> None:
        for index, data_url in enumerate(images):
            self.add_jpeg(decode_data_url(data_url), f"{label}_{index:03d}")

    def encode(self) -> Path | None:
        if not self.frame_paths:
            self.cleanup()
            return None
        try:
            with Image.open(self.frame_paths[0]) as first:
                width, height = first.size
            self.video_path.parent.mkdir(parents=True, exist_ok=True)
            # imageio-ffmpeg provides its own bundled ffmpeg binary and encodes H.264 by
            # default, so the resulting .mp4 plays correctly in web browsers (unlike
            # OpenCV's `mp4v` MPEG-4 Part 2 output, which browsers cannot decode).
            writer = imageio.get_writer(
                str(self.video_path),
                fps=self.fps,
                codec="libx264",
                # yuv420p is required for broad browser compatibility; yuv444p and other
                # chroma subsampling variants will render as 0:00 / unplayable in <video>.
                pixelformat="yuv420p",
            )
            try:
                for path in self.frame_paths:
                    try:
                        with Image.open(path) as frame_image:
                            if frame_image.size != (width, height):
                                frame_image = frame_image.resize((width, height))
                            writer.append_data(np.asarray(frame_image.convert("RGB")))
                    except Exception as exc:  # noqa: BLE001 - skip corrupt frame, keep the rest
                        log.warning("Skipping unreadable frame: %s (%s)", path, exc)
                        continue
            finally:
                writer.close()
            if not self.video_path.exists() or self.video_path.stat().st_size == 0:
                raise RuntimeError(f"Video encoding produced no output: {self.video_path}")
            log.info("Encoded %d frames to %s", len(self.frame_paths), self.video_path)
            return self.video_path
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Delete temporary source frames while preserving explicitly requested frames."""
        if self._temporary_dir is not None:
            self._temporary_dir.cleanup()
            self._temporary_dir = None
