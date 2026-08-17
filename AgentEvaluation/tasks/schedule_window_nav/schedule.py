"""LLM-assisted parsing of SF task descriptions into timed schedule stops.

SF descriptions are free-form natural language ("At 10 a.m., you've got a court hearing at
the Court of Final Appeal. You're meeting your husband at Samsung at 12 noon. ...", but also
"by 10:00", "2:00 in the afternoon", "four o'clock", 24-hour "14:00", or total-deadline
variants like "run these errands within 2 hours"). A regex parser cannot cover that variety
(measured 16/60 tasks where naive time extraction disagrees with the editor-labeled stop
count), so the schedule is parsed once per episode by the evaluation LLM and then validated
strictly against the editor-labeled ground truth:

- the number of parsed appointments must equal len(task["schedule"]) -- the stops are
  positionally aligned with the editor's ordered targets;
- every time must be "HH:MM" (24-hour) or null;
- if parsing fails after retries, the evaluator degrades to order-only scoring (arrival
  order is still judged against the editor's targets, but no on-time metrics are produced).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from api import LLMClient, LLMResponseError

log = logging.getLogger(__name__)

_TIME_TEXT_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")

PARSE_PROMPT = """You are parsing a person's daily schedule, described in natural language, for an evaluation harness.

Extract the schedule into exactly one JSON object with these fields:
- "current_time": the "now" time as "HH:MM" (24-hour) if the text states a current time (for example "It is now 9:00 AM"), otherwise null.
- "appointments": an array with EXACTLY {stop_count} entries, one per place to visit, IN THE ORDER they must be visited. Each entry is an object with:
  - "place": the name of the place (string, copied from the text),
  - "activity": a short phrase describing what happens there (string),
  - "time": the scheduled/deadline time as "HH:MM" (24-hour) if a specific time is given for this place ("at 2 p.m.", "by 10:00", "around 6 PM", "at four o'clock in the afternoon", "at 14:00" all count; "around X" still maps to X), otherwise null.
- "total_deadline": "HH:MM" (24-hour) if the text gives one overall deadline for finishing everything (for example "complete these errands within 2 hours" combined with a stated current time means current_time + 2 hours), otherwise null.
- "dwell_minutes": the per-stop dwell time in minutes if the text states one (for example "spending about 20 minutes at each place"), otherwise null.

Rules:
- Use 24-hour "HH:MM" with leading zeros; "noon" is 12:00, "midnight" is 00:00.
- The appointments array MUST contain exactly {stop_count} entries, in visiting order, even when some entries have a null time.
- "current_time" may only be set when the text explicitly states what time it is now (for example "It is now 9:00 AM", "It's currently 7:00 a.m.", "It is 9:00 AM now"). A time that merely belongs to the first appointment is NOT a current time; use null instead.
- The schedule describes one day in visiting order, so appointment times should be non-decreasing along the array. If a literal reading would break that order and the text plausibly means the other convention (for example "12:00 AM" sandwiched between late-morning and afternoon appointments almost certainly means noon, 12:00), prefer the interpretation that keeps the order sensible.
- Do not invent times that are not stated or directly implied by the text.
- Return only the JSON object, with no Markdown fences and no extra text.

Schedule text:
{description}"""

FIX_PROMPT = (
    "The JSON you returned is invalid for this reason: {error}. Return a corrected JSON "
    "object only. Remember: exactly {stop_count} appointment entries in visiting order, "
    "every time either \"HH:MM\" (24-hour) or null."
)


@dataclass(frozen=True)
class ScheduleStopSpec:
    """One parsed appointment, positionally aligned with task["schedule"][index]."""

    index: int
    place: str
    activity: str
    deadline_minutes: int | None  # minutes since midnight, or None when untimed


@dataclass(frozen=True)
class ParsedSchedule:
    """The validated result of parsing one SF task description."""

    current_time_minutes: int | None
    stops: list[ScheduleStopSpec]
    total_deadline_minutes: int | None
    dwell_minutes: float | None
    # "llm": parsed and validated by the LLM; "fallback_order_only": parsing failed, stops
    # carry no times and the evaluator must only score visiting order.
    parse_status: str
    raw_response: str | None = None
    parse_error: str | None = None

    @property
    def has_time_windows(self) -> bool:
        """Whether any usable time information was parsed (per-stop or total deadline)."""
        return any(stop.deadline_minutes is not None for stop in self.stops) or (
            self.total_deadline_minutes is not None
        )

    def first_deadline_minutes(self) -> int | None:
        for stop in self.stops:
            if stop.deadline_minutes is not None:
                return stop.deadline_minutes
        return self.total_deadline_minutes


def _parse_time_text(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    match = _TIME_TEXT_RE.match(str(value).strip())
    if not match:
        raise LLMResponseError(f"{field_name} must be \"HH:MM\" (24-hour) or null, got {value!r}")
    return int(match.group(1)) * 60 + int(match.group(2))


def _validate_payload(payload: dict[str, Any], expected_stops: int) -> ParsedSchedule:
    appointments = payload.get("appointments")
    if not isinstance(appointments, list):
        raise LLMResponseError("\"appointments\" must be an array")
    if len(appointments) != expected_stops:
        raise LLMResponseError(
            f"expected exactly {expected_stops} appointments, got {len(appointments)}"
        )
    stops: list[ScheduleStopSpec] = []
    for index, entry in enumerate(appointments):
        if not isinstance(entry, dict):
            raise LLMResponseError(f"appointment {index + 1} must be an object")
        stops.append(ScheduleStopSpec(
            index=index,
            place=str(entry.get("place") or f"Stop {index + 1}").strip(),
            activity=str(entry.get("activity") or "").strip(),
            deadline_minutes=_parse_time_text(entry.get("time"), f"appointments[{index}].time"),
        ))
    dwell = payload.get("dwell_minutes")
    if dwell is not None:
        try:
            dwell = float(dwell)
        except (TypeError, ValueError) as exc:
            raise LLMResponseError(f"dwell_minutes must be a number or null, got {dwell!r}") from exc
        if dwell <= 0:
            dwell = None
    return ParsedSchedule(
        current_time_minutes=_parse_time_text(payload.get("current_time"), "current_time"),
        stops=stops,
        total_deadline_minutes=_parse_time_text(payload.get("total_deadline"), "total_deadline"),
        dwell_minutes=dwell,
        parse_status="llm",
    )


def fallback_schedule(stop_count: int, error: str) -> ParsedSchedule:
    """Order-only schedule used when LLM parsing fails: no times, positions only."""
    return ParsedSchedule(
        current_time_minutes=None,
        stops=[ScheduleStopSpec(index=index, place=f"Stop {index + 1}", activity="",
                                deadline_minutes=None)
               for index in range(stop_count)],
        total_deadline_minutes=None,
        dwell_minutes=None,
        parse_status="fallback_order_only",
        parse_error=error,
    )


def parse_schedule(llm: LLMClient, description: str, expected_stops: int,
                   retry_count: int = 2) -> ParsedSchedule:
    """Parse one SF description into a validated ParsedSchedule.

    On every validation failure the model gets one correction turn quoting the error;
    after `retry_count + 1` attempts the caller falls back to order-only scoring.
    """
    prompt = PARSE_PROMPT.format(stop_count=expected_stops, description=description.strip())
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    last_error = ""
    raw = ""
    for _attempt in range(retry_count + 1):
        try:
            raw = llm.complete(messages, max_tokens=1024)
            schedule = _validate_payload(llm.parse_json_object(raw), expected_stops)
            return ParsedSchedule(**{**schedule.__dict__, "raw_response": raw})
        except (LLMResponseError, ValueError, TypeError) as exc:
            last_error = str(exc)
            log.warning("Schedule parse attempt failed: %s", last_error)
            messages.extend([
                {"role": "assistant", "content": raw},
                {"role": "user", "content": FIX_PROMPT.format(
                    error=last_error, stop_count=expected_stops)},
            ])
    return fallback_schedule(expected_stops, last_error)


def format_clock(minutes: int) -> str:
    """Render minutes-since-midnight (possibly >= 1440) as HH:MM."""
    minutes = minutes % 1440
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_state_clock(state: dict[str, Any]) -> float | None:
    """Extract the sandbox clock ("HH:MM:SS") from a /state payload, as fractional minutes."""
    value = state.get("time")
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60.0
    except ValueError:
        return None
