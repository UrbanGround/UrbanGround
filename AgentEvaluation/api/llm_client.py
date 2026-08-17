"""OpenAI-compatible LLM client used by the sandbox agent."""

from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

log = logging.getLogger(__name__)

_RETRY_BASE_DELAY = 2.0
_RETRY_MAX_DELAY = 60.0
_RETRY_AFTER_CAP = 120.0


class LLMResponseError(RuntimeError):
    """Raised when a model response is empty or is not valid JSON."""


@dataclass(frozen=True)
class LLMConfig:
    """Runtime configuration for an OpenAI-compatible multimodal model endpoint."""

    api_key: str
    base_url: str
    model: str = "gpt-4.1"
    timeout: float = 180.0
    max_tokens: int = 4096
    max_attempts: int = 100

    @classmethod
    def from_env(cls, *, model: str | None = None) -> "LLMConfig":
        api_key = os.environ.get("AGENT_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing AGENT_API_KEY (or OPENAI_API_KEY)")
        return cls(
            api_key=api_key,
            base_url=(
                os.environ.get("AGENT_API_BASE")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            ),
            model=model or os.environ.get("AGENT_MODEL", "gpt-4.1"),
            timeout=float(os.environ.get("AGENT_API_TIMEOUT", "180")),
            max_tokens=int(os.environ.get("AGENT_MAX_TOKENS", "4096")),
            max_attempts=int(os.environ.get("AGENT_API_MAX_ATTEMPTS", "100")),
        )


class LLMClient:
    """Small, reusable wrapper around an OpenAI-compatible chat-completions API."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        self._client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)

    def complete(self, messages: list[dict[str, Any]], *, max_tokens: int | None = None) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    max_tokens=max_tokens or self.config.max_tokens,
                    timeout=self.config.timeout,
                )
            except (RateLimitError, InternalServerError,
                    APITimeoutError, APIConnectionError) as exc:
                # Transient failures (429 / 5xx / network / timeout): keep retrying.
                last_error = exc
                if attempt >= self.config.max_attempts:
                    break
                delay = self._retry_delay(exc, attempt)
                log.warning(
                    "LLM request failed (attempt %d/%d): %s; retrying in %.1fs",
                    attempt, self.config.max_attempts, exc, delay,
                )
                time.sleep(delay)
                continue
            text = response.choices[0].message.content
            if not text or not text.strip():
                raise LLMResponseError("The model returned an empty response.")
            return text.strip()
        if last_error is not None:
            raise last_error
        raise LLMResponseError("LLM request failed before any attempt was made.")

    @staticmethod
    def _retry_delay(exc: Exception, attempt: int) -> float:
        """Seconds to wait before the next attempt, honoring Retry-After when present."""
        response = getattr(exc, "response", None)
        retry_after = response.headers.get("retry-after") if response is not None else None
        if retry_after:
            try:
                return min(float(retry_after), _RETRY_AFTER_CAP)
            except ValueError:
                pass
        cap = min(_RETRY_BASE_DELAY * (2 ** (attempt - 1)), _RETRY_MAX_DELAY)
        return random.uniform(_RETRY_BASE_DELAY, cap)

    def complete_text(self, prompt: str, *, system_prompt: str | None = None,
                      max_tokens: int | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.complete(messages, max_tokens=max_tokens)

    @staticmethod
    def image_user_message(prompt: str, image_bytes: bytes, *,
                           image_media_type: str = "image/jpeg") -> dict[str, Any]:
        """Build one multimodal user turn for use in a persistent conversation."""
        encoded = base64.b64encode(image_bytes).decode("ascii")
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_media_type};base64,{encoded}"},
                },
            ],
        }

    def complete_with_image(self, prompt: str, image_bytes: bytes, *,
                            system_prompt: str | None = None,
                            image_media_type: str = "image/jpeg",
                            max_tokens: int | None = None) -> str:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append(self.image_user_message(
            prompt, image_bytes, image_media_type=image_media_type
        ))
        return self.complete(messages, max_tokens=max_tokens)

    @staticmethod
    def parse_json_object(text: str) -> dict[str, Any]:
        """Extract one JSON object while tolerating accidental Markdown fences or prose."""
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            value = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError) as exc:
            raise LLMResponseError(f"The model did not return a valid JSON object: {text[:300]}") from exc
        if not isinstance(value, dict):
            raise LLMResponseError("The model response must be a JSON object.")
        return value

    def complete_json(self, messages: list[dict[str, Any]], *,
                      max_tokens: int | None = None) -> dict[str, Any]:
        return self.parse_json_object(self.complete(messages, max_tokens=max_tokens))
