"""OpenAI client helpers for generating structured Mate profiles."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from openai import OpenAI

_CLIENT: Optional[OpenAI] = None


class OpenAIConfigError(RuntimeError):
    """Raised when the OpenAI client cannot be configured."""


def configure_client(api_key: str) -> OpenAI:
    """Create and cache an OpenAI client."""
    if not api_key:
        raise OpenAIConfigError("Missing OpenAI API key.")
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI(api_key=api_key)
    return _CLIENT


def generate_profile_json(
    client: OpenAI,
    prompt: str,
    template: Dict[str, Any],
) -> Dict[str, Any]:
    """Invoke OpenAI to generate a JSON profile adhering to the template contract."""
    meta = template.get("meta", {})
    model = meta.get("model_hint", "gpt-4o-mini")
    temperature = meta.get("temperature", 0.7)
    system_msg = meta.get("purpose", "You craft precise Mate dating profiles.")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=float(temperature),
        max_tokens=700,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI response was not valid JSON.") from exc

    return parsed

