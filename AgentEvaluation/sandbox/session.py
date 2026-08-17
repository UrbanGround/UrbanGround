"""Lifecycle management for a local UrbanGround application process."""

from __future__ import annotations

import logging
import subprocess
import uuid
from pathlib import Path

log = logging.getLogger(__name__)


class SandboxSession:
    """Own one locally launched UrbanGround process.

    When ``attach`` is true, the caller is responsible for starting the application and
    the context manager only provides a stable run identifier.
    """

    def __init__(self, *, attach: bool = False):
        self.attach = attach
        self._process: subprocess.Popen[bytes] | None = None
        self._session_id = f"local-{uuid.uuid4().hex[:12]}"

    @property
    def session_id(self) -> str:
        return self._session_id

    def __enter__(self) -> "SandboxSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._process is None:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)
        log.info("UrbanGround process stopped")

    def launch(self, executable: Path, *, cwd: Path) -> subprocess.Popen[bytes]:
        if self.attach:
            raise RuntimeError("Cannot launch an application in attach mode")
        if self._process is not None:
            raise RuntimeError("This session already owns an application process")
        self._process = subprocess.Popen(  # noqa: S603 - executable is resolved by deploy.py
            [str(executable)],
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        log.info("UrbanGround process started: %s", executable)
        return self._process
