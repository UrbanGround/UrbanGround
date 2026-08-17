"""Resolve and launch a packaged UrbanGround build on the local machine."""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path

from .session import SandboxSession


def default_build_folder(project_root: Path) -> Path:
    if sys.platform == "darwin":
        return project_root / "Builds" / "macOS"
    if sys.platform == "win32":
        return project_root / "Builds" / "Windows"
    if sys.platform.startswith("linux"):
        return project_root / "Builds" / "Linux"
    raise RuntimeError(
        "UrbanGround application builds are provided for macOS, Windows, and Linux. "
        "Pass --build-folder only on a supported platform."
    )


def _macos_app_executable(app_path: Path) -> Path:
    info_path = app_path / "Contents" / "Info.plist"
    if not info_path.is_file():
        raise FileNotFoundError(f"macOS application metadata not found: {info_path}")
    with info_path.open("rb") as file:
        executable_name = plistlib.load(file).get("CFBundleExecutable")
    if not executable_name:
        raise ValueError(f"CFBundleExecutable is missing from {info_path}")
    return app_path / "Contents" / "MacOS" / str(executable_name)


def resolve_executable(build_folder: Path, exe_path: str | None = None) -> Path:
    build_folder = build_folder.resolve()
    if not build_folder.is_dir():
        raise FileNotFoundError(f"Build folder not found: {build_folder}")

    if exe_path:
        candidate = Path(exe_path)
        candidate = candidate if candidate.is_absolute() else build_folder / candidate
        if candidate.suffix == ".app" or candidate.name.endswith(".app"):
            candidate = _macos_app_executable(candidate)
    elif sys.platform == "darwin":
        apps = sorted(build_folder.glob("*.app"))
        preferred_names = ("UrbanGround.app",)
        preferred = next(
            (build_folder / name for name in preferred_names
             if (build_folder / name).is_dir()),
            None,
        )
        candidate_app = preferred or (apps[0] if len(apps) == 1 else None)
        if candidate_app is None:
            raise FileNotFoundError(
                f"Expected one .app in {build_folder}, found {len(apps)}; pass --exe-path"
            )
        candidate = _macos_app_executable(candidate_app)
    elif sys.platform == "win32":
        preferred_names = ("UrbanGround.exe",)
        preferred = next(
            (build_folder / name for name in preferred_names
             if (build_folder / name).is_file()),
            None,
        )
        executables = sorted(build_folder.glob("*.exe"))
        candidate = preferred or (executables[0] if len(executables) == 1 else Path())
    elif sys.platform.startswith("linux"):
        preferred_names = ("UrbanGround.x86_64",)
        preferred = next(
            (build_folder / name for name in preferred_names
             if (build_folder / name).is_file()),
            None,
        )
        executables = sorted(build_folder.glob("*.x86_64"))
        candidate = preferred or (executables[0] if len(executables) == 1 else Path())
    else:
        raise RuntimeError(
            "UrbanGround application builds are provided for macOS, Windows, and Linux"
        )

    if not candidate.is_file():
        raise FileNotFoundError(f"UrbanGround executable not found: {candidate}")
    return candidate.resolve()


def task_directory_for_build(build_folder: Path) -> Path:
    task_dir = build_folder.resolve() / "task"
    if not task_dir.is_dir():
        raise FileNotFoundError(
            f"Packaged task directory not found: {task_dir}. "
            "Keep the task directory beside the distributed application."
        )
    return task_dir


def launch_build(
    session: SandboxSession, build_folder: Path, exe_path: str | None = None
) -> Path:
    executable = resolve_executable(build_folder, exe_path)
    session.launch(executable, cwd=build_folder.resolve())
    return executable


def prepare_deployment_archive(local_folder: Path) -> None:
    """Compatibility shim for older diagnostic scripts; local launches need no archive."""
    if not local_folder.resolve().is_dir():
        raise FileNotFoundError(f"Build folder not found: {local_folder}")
    return None


def deploy_and_launch(
    session: SandboxSession,
    local_folder: Path,
    exe_relative_path: str | None = None,
    archive_path: Path | None = None,
) -> Path:
    """Compatibility name retained for the repository's older integration probes."""
    del archive_path
    return launch_build(session, local_folder, exe_relative_path)
