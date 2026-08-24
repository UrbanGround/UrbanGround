"""Reusable visual ReAct agent with text memory and privileged-state isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .llm_client import LLMClient, LLMResponseError

ActionValidator = Callable[[Any], dict[str, Any]]

ACTION_SPACE_PROMPT = """Action space (choose exactly one action per exploration turn).

Every action uses one flat JSON object. Its required `action` field is one of the literal action names listed below; include only the parameters defined for that action. The descriptions below are schemas, not example actions.

First-person mode actions:
- move: `action` = "move"; `dir` is one of "forward", "backward", "left", or "right"; `seconds` is a number in [0.05, 2.0]. Optional: `yaw_rate` and `pitch_rate` are numbers in [-180, 180] degrees per second; `jump` is a boolean; `jump_at` is a number in [0, seconds].
- sprint: same fields and ranges as move, with `action` = "sprint".
- look: `action` = "look"; `yaw` is a number in [-180, 180] degrees, where positive turns right and negative turns left; `pitch` is a number in [-90, 90] degrees, where positive looks up and negative looks down.
- jump: only the `action` field with value "jump".
- open_map: only the `action` field with value "open_map".

Map mode actions:
- map_select: `action` = "map_select"; `x` and `y` are normalized screen coordinates in [0, 1], with x increasing left-to-right and y increasing top-to-bottom.
- map_pan: `action` = "map_pan"; `east` and `north` are distances in meters, each in [-2000, 2000].
- map_zoom: `action` = "map_zoom"; `factor` is a number in [0.25, 4.0]; values below 1 move closer and values above 1 move farther.
- map_orbit: `action` = "map_orbit"; `yaw` is a number in [-180, 180] degrees and `pitch` is a number in [-90, 90] degrees.
- close_map: only the `action` field with value "close_map".

Available in both first-person and map mode:
- terminate: only the `action` field with value "terminate". Choose it once you have enough visual evidence to answer confidently; exploration ends immediately and you will then be asked for the final multiple-choice answer.

Use first-person actions only while viewing the first-person scene and map actions only while the map is visible. Never request move or sprint for longer than 2 seconds. If a larger duration is supplied, the environment clamps it and executes only 2 seconds. Do not infer or emit actions outside this complete action space.
"""

NAV_ACTION_SPACE_PROMPT = """Action space (choose exactly one action per navigation turn).

Every action uses one flat JSON object. Its required `action` field is one of the literal action names listed below; include only the parameters defined for that action. The descriptions below are schemas, not example actions.

First-person mode actions:
- move: `action` = "move"; `dir` is one of "forward", "backward", "left", or "right"; `seconds` is a number in [0.05, 2.0]. Optional: `yaw_rate` and `pitch_rate` are numbers in [-180, 180] degrees per second; `jump` is a boolean; `jump_at` is a number in [0, seconds].
- sprint: same fields and ranges as move, with `action` = "sprint".
- look: `action` = "look"; `yaw` is a number in [-180, 180] degrees, where positive turns right and negative turns left; `pitch` is a number in [-90, 90] degrees, where positive looks up and negative looks down.
- jump: only the `action` field with value "jump".
- open_map: only the `action` field with value "open_map".

Map mode actions:
- map_select: `action` = "map_select"; `x` and `y` are normalized screen coordinates in [0, 1], with x increasing left-to-right and y increasing top-to-bottom. Selecting a point changes the visible map selection. It does not invoke location lookup or route computation.
- map_pan: `action` = "map_pan"; `east` and `north` are distances in meters, each in [-2000, 2000].
- map_zoom: `action` = "map_zoom"; `factor` is a number in [0.25, 4.0]; values below 1 move closer and values above 1 move farther.
- map_orbit: `action` = "map_orbit"; `yaw` is a number in [-180, 180] degrees and `pitch` is a number in [-90, 90] degrees.
- close_map: only the `action` field with value "close_map".

The actions listed above form the complete model-facing map interface. No route-computation action is available.

Available in both first-person and map mode:
- terminate: only the `action` field with value "terminate". Choose it when you believe the task is complete or deliberately want to stop; navigation ends immediately and your current position/state is scored.

Use first-person actions only while viewing the first-person scene and map actions only while the map is visible. Never request move or sprint for longer than 2 seconds. If a larger duration is supplied, the environment clamps it and executes only 2 seconds. Do not infer or emit actions outside this complete action space.
"""

REACT_PROTOCOL_PROMPT = """Follow a visual ReAct loop on every exploration turn:
1. Observation: extract only relevant visible evidence from the current screenshot.
2. Reason: use that evidence and your remembered prior observations/actions to decide what to inspect next.
3. Action: choose exactly one action from the action space.

Return exactly one JSON object and no Markdown or extra text. The top-level object must contain exactly these fields:
- `observation`: a non-empty string containing concise visible evidence.
- `reason`: a non-empty string containing the concise reason for the next action.
- `action`: one flat action object conforming to exactly one schema in the action space above.

The nested action object must use the string field `action` for its action name. Do not use a `type` field, do not key the object by the action name, and do not add unavailable parameters. No concrete numeric action example is provided; select every parameter solely from current visual evidence and conversation memory.
During exploration, do not answer the multiple-choice question. When the visible evidence is sufficient, choose terminate; you will then be explicitly asked for the final answer. If you do not terminate, exploration ends automatically when the turn limit is reached.
You receive only task text, screenshots, and conversation memory. Never assume access to hidden simulator state.
"""

FINAL_ANSWER_SCHEMA_PROMPT = """Return exactly one JSON object with no Markdown or extra text:
{"answer":"A|B|C|D","reason":"brief evidence-based reason grounded in the visual exploration"}
"""

NAV_REACT_PROTOCOL_PROMPT = """Follow a visual ReAct loop on every navigation turn:
1. Observation: extract only relevant visible evidence from the current screenshot (street layout, signs, crossings, obstacles, distance travelled).
2. Reason: use that evidence and your remembered prior observations/actions to decide what to do next in order to reach the destination.
3. Action: choose exactly one action from the action space.

Return exactly one JSON object and no Markdown or extra text. The top-level object must contain exactly these fields:
- `observation`: a non-empty string containing concise visible evidence.
- `reason`: a non-empty string containing the concise reason for the next action.
- `action`: one flat action object conforming to exactly one schema in the action space above.

The nested action object must use the string field `action` for its action name. Do not use a `type` field, do not key the object by the action name, and do not add unavailable parameters. No concrete numeric action example is provided; select every parameter solely from current visual evidence and conversation memory.
Keep navigating turn after turn until you believe you have arrived at the destination, then choose terminate so the current state can be scored. You may also choose terminate if you deliberately decide to stop. If you do not terminate, navigation ends automatically on arrival or when the turn limit is reached; there is no final answer to submit for this task.
You receive only task text, screenshots, and conversation memory. A fixed start or goal description may be included in the task instruction. Never assume access to updated simulator state such as current coordinates or a distance-remaining readout. If you need global context, open the map and inspect the markers made visible by the task. The map does not compute or display a route.
"""


@dataclass(frozen=True)
class ReActStep:
    """One validated Observe-Reason-Act decision."""

    observation: str
    reason: str
    action: dict[str, Any]
    raw_response: str
    raw_responses: list[str]
    model_attempts: int


@dataclass(frozen=True)
class FinalAnswer:
    """One parsed final multiple-choice answer."""

    answer: Any
    reason: str
    raw_response: str


@dataclass
class ConversationMemory:
    """Text-only episodic memory; historical images are summarized by model responses."""

    system_prompt: str
    messages: list[dict[str, Any]] = field(init=False)

    def __post_init__(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def request_messages(self, current_user_message: dict[str, Any]) -> list[dict[str, Any]]:
        return [*self.messages, current_user_message]

    def remember_turn(self, user_text: str, assistant_text: str) -> None:
        self.messages.extend([
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ])


class VisualReActAgent:
    """Stateful visual agent that owns prompting, memory, parsing, and retries.

    The environment remains outside this class. In particular, simulator telemetry may be used
    by the caller inside `validate_action`, but is never accepted as an observation and therefore
    cannot accidentally be serialized into an LLM request.
    """

    def __init__(self, llm: LLMClient, task_prompt: str, task_description: str,
                 retry_count: int = 2, action_space_prompt: str = ACTION_SPACE_PROMPT,
                 react_protocol_prompt: str = REACT_PROTOCOL_PROMPT):
        self.llm = llm
        self.task_description = task_description.strip()
        self.retry_count = retry_count
        system_prompt = "\n\n".join((
            task_prompt.strip(), action_space_prompt.strip(), react_protocol_prompt.strip()
        ))
        self.memory = ConversationMemory(system_prompt)
        self._task_introduced = False

    @property
    def conversation(self) -> list[dict[str, Any]]:
        """Expose a read-only-by-convention view for diagnostics and tests."""
        return self.memory.messages

    def _exploration_prompt(self, extra_context: str | None = None) -> str:
        task = ""
        if not self._task_introduced:
            task = f"Task:\n{self.task_description}\n\n"
        notice = f"{extra_context.strip()}\n\n" if extra_context and extra_context.strip() else ""
        return (
            task
            + notice
            + "Current observation: inspect only the attached screenshot. Use your conversation "
              "memory to continue the visual ReAct loop and choose exactly one next action."
        )

    def plan(self, screenshot: bytes, validate_action: ActionValidator,
             extra_context: str | None = None) -> ReActStep:
        """Observe the current screenshot, reason from memory, and return one validated action.

        `extra_context` optionally injects a one-off notice ahead of the standard exploration
        prompt for this turn only (for example, a dynamically appearing road closure notice).
        It is folded into `user_text` so it is preserved verbatim in conversation memory once
        this turn is remembered, letting the agent recall it on every subsequent turn.
        """
        user_text = self._exploration_prompt(extra_context)
        image_message = self.llm.image_user_message(user_text, screenshot)
        attempt_messages = self.memory.request_messages(image_message)
        raw_responses: list[str] = []
        last_error = ""

        for attempt in range(self.retry_count + 1):
            raw = self.llm.complete(attempt_messages)
            raw_responses.append(raw)
            try:
                payload = self.llm.parse_json_object(raw)
                observation = str(payload.get("observation", "")).strip()[:1000]
                reason = str(payload.get("reason", "")).strip()[:1000]
                if not observation:
                    raise LLMResponseError("observation must be a non-empty string")
                if not reason:
                    raise LLMResponseError("reason must be a non-empty string")
                action = validate_action(payload.get("action"))
                self.memory.remember_turn(user_text, raw)
                self._task_introduced = True
                return ReActStep(
                    observation=observation,
                    reason=reason,
                    action=action,
                    raw_response=raw,
                    raw_responses=raw_responses,
                    model_attempts=attempt + 1,
                )
            except (LLMResponseError, ValueError, TypeError, OverflowError) as exc:
                last_error = str(exc)
                attempt_messages.extend([
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": (
                        "The response could not be executed. Correct only the JSON response. "
                        "Follow the exploration schema exactly and choose an action valid for "
                        "the interface visible in the current screenshot."
                    )},
                ])

        raise ValueError(
            f"Agent failed to produce a valid ReAct action after {self.retry_count + 1} attempts: "
            f"{last_error}; raw_responses={raw_responses!r}"
        )

    def answer(self, screenshot: bytes, parse_answer: Callable[[Any], Any]) -> FinalAnswer:
        """Answer from the final screenshot and the complete text conversation memory."""
        user_text = (
            "Exploration is complete. Use the attached final screenshot and your complete "
            "conversation memory to answer the original task.\n\n"
            + FINAL_ANSWER_SCHEMA_PROMPT
        )
        image_message = self.llm.image_user_message(user_text, screenshot)
        raw = self.llm.complete(self.memory.request_messages(image_message))
        payload = self.llm.parse_json_object(raw)
        answer = parse_answer(payload.get("answer"))
        reason = str(payload.get("reason", "")).strip()[:2000]
        if answer is None:
            raise LLMResponseError("answer must be exactly one of A, B, C, or D")
        if not reason:
            raise LLMResponseError("final reason must be a non-empty string")
        self.memory.remember_turn(user_text, raw)
        return FinalAnswer(answer=answer, reason=reason, raw_response=raw)
