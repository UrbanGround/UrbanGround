"""Build the complete in-memory task set used by ``run_task.py --all``.

The Unity build contains the reusable Level-1 QA and navigation payloads, but only a
couple of materialized examples for each supported pedestrian/weather variant, and the dynamic
road-closure tasks reuse the constrained-navigation payloads with a different evaluator type.
``--all`` must therefore clone the complete source sets in memory instead of treating sparse
examples as the full benchmark.  The cloned task keeps ``sourceTaskId`` so the evaluator can ask
the sandbox to load the source payload while using its new variant ID for reporting.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

TaskLoader = Callable[[Path], dict[str, Any]]


@dataclass(frozen=True)
class TaskRunSpec:
    """One runnable task, backed by a real source JSON file."""

    task_path: Path
    task: dict[str, Any]
    generated_variant: bool = False

    @property
    def task_id(self) -> str:
        return str(self.task["id"])

    @property
    def source_task_id(self) -> str | None:
        value = str(self.task.get("sourceTaskId") or "").strip()
        return value or None


# Existing files with these prefixes are sparse examples, not independent source tasks.
# They are replaced by a complete, deterministically generated set during --all.
GENERATED_VARIANT_PREFIXES = frozenset({
    "PD", "PL", "DCR", "RQ", "RN",
    "TSQ", "TSN", "OCQ", "OCN", "CLQ", "CLN", "EVQ", "EVN", "NTQ", "NTN",
})

QA_SOURCES = (("LQ", 7), ("OQ", 8), ("SQ", 9))
SHORT_NAV_SOURCE = (("SN", 0),)
LONG_NAV_SOURCE = (("LN", 2),)
CONSTRAINED_NAV_SOURCE = (("CN", 11),)

# Most variants reuse their source task's numeric type. DCR deliberately overrides type 11
# (ConstrainedNav, closure disclosed up front) with type 12 (DynamicClosureNav, closure disclosed
# after the episode has started). The DCR-* ID keeps its output separate from the source CN-* run.
VARIANT_TYPE_OVERRIDES = {"DCR": 12}

# (generated prefix, source (ID prefix, numeric type) pairs)
VARIANT_RULES: tuple[tuple[str, tuple[tuple[str, int], ...]], ...] = (
    # PedestrianShortNav (PD) was retired from the Level-5 benchmark.  Keep PD in
    # GENERATED_VARIANT_PREFIXES so sparse legacy examples are also excluded from --all,
    # but do not generate the former 80-task ShortNav reuse set anymore.
    ("PL", LONG_NAV_SOURCE),
    ("DCR", CONSTRAINED_NAV_SOURCE),
    ("RQ", QA_SOURCES),
    ("RN", SHORT_NAV_SOURCE),
    ("TSQ", QA_SOURCES),
    ("TSN", SHORT_NAV_SOURCE),
    ("OCQ", QA_SOURCES),
    ("OCN", SHORT_NAV_SOURCE),
    ("CLQ", QA_SOURCES),
    ("CLN", SHORT_NAV_SOURCE),
    ("EVQ", QA_SOURCES),
    ("EVN", SHORT_NAV_SOURCE),
    ("NTQ", QA_SOURCES),
    ("NTN", SHORT_NAV_SOURCE),
)


def _id_prefix(task: dict[str, Any]) -> str:
    return str(task.get("id", "")).split("-", 1)[0].upper()


def task_run_from_path(path: Path, load_task: TaskLoader) -> TaskRunSpec:
    resolved = path.resolve()
    return TaskRunSpec(task_path=resolved, task=load_task(resolved))


def expand_all_task_runs(paths: Iterable[Path], load_task: TaskLoader,
                         supported_types: set[int]) -> list[TaskRunSpec]:
    """Return base tasks plus every currently supported reuse variant.

    IDs use ``<variant-prefix>-<complete-source-id>``.  Including the source prefix
    (for example ``RQ-OQ-...``) makes the generated IDs stable and collision-free while
    retaining the leading prefix expected by evaluator routing.
    """
    loaded: list[TaskRunSpec] = []
    for path in paths:
        spec = task_run_from_path(path, load_task)
        if int(spec.task.get("type", -1)) in supported_types:
            loaded.append(spec)

    base_runs = [spec for spec in loaded if _id_prefix(spec.task) not in GENERATED_VARIANT_PREFIXES]
    sources: dict[tuple[str, int], list[TaskRunSpec]] = {}
    for spec in base_runs:
        key = (_id_prefix(spec.task), int(spec.task.get("type", -1)))
        sources.setdefault(key, []).append(spec)
    for values in sources.values():
        values.sort(key=lambda spec: spec.task_id)

    required_source_keys = {key for _prefix, keys in VARIANT_RULES for key in keys}
    missing_source_keys = sorted(key for key in required_source_keys if not sources.get(key))
    if missing_source_keys:
        raise ValueError(
            "Cannot completely expand --all because source task groups are missing: "
            f"{missing_source_keys}"
        )

    generated: list[TaskRunSpec] = []
    for variant_prefix, source_keys in VARIANT_RULES:
        for source_key in source_keys:
            for source in sources.get(source_key, []):
                task = deepcopy(source.task)
                task["id"] = f"{variant_prefix}-{source.task_id}"
                task["sourceTaskId"] = source.task_id
                task["type"] = VARIANT_TYPE_OVERRIDES.get(
                    variant_prefix, int(source.task["type"])
                )
                # Internal provenance only; the generated payload is never posted to Unity.
                task["_generatedVariant"] = True
                generated.append(TaskRunSpec(
                    task_path=source.task_path,
                    task=task,
                    generated_variant=True,
                ))

    result = sorted([*base_runs, *generated], key=lambda spec: spec.task_id)
    id_counts = Counter(spec.task_id for spec in result)
    duplicates = sorted(task_id for task_id, count in id_counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate task IDs after --all expansion: {duplicates}")
    return result
