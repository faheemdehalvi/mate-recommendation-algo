"""Helpers for assembling OpenAI prompts from templates and user records."""

from __future__ import annotations

import json
from typing import Any, Dict


def _split_csv_field(value: Any) -> list[str]:
    if not value or not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_openai_prompt(template: Dict[str, Any], record: Dict[str, Any]) -> str:
    """Create a rich instruction prompt for the OpenAI model.

    Args:
        template: JSON template describing constraints and style.
        record: CSV row for the selected user.

    Returns:
        Fully formatted instruction string.
    """
    meta = template.get("meta", {})
    constraints = template.get("hard_constraints", {})
    style = template.get("style_guidelines", {})
    output_contract = template.get("output_contract", {})

    hobbies = _split_csv_field(record.get("hobbies") or record.get("tags"))
    interests = _split_csv_field(record.get("interests"))
    keywords = sorted(set(hobbies + interests))

    contract_summary = json.dumps(output_contract, indent=2, ensure_ascii=False)

    prompt_parts = [
        meta.get("purpose", ""),
        "",
        f"Hard constraints: {constraints.get('perspective', '')}",
        "Explicitly ensure the narrative references the subject by name (e.g., 'Sakshi is a hardworking individual') and never uses first-person phrasing such as 'I am' or 'Hi, I'm'.",
        f"Tense directive: {constraints.get('tense', 'Use present tense.')}",
        f"Formatting rule: {constraints.get('format', '')}",
        f"Forbidden openers: {', '.join(constraints.get('no_generic_openers', []))}",
        f"Avoid clichés: {', '.join(constraints.get('no_boilerplate', []))}",
        (
            "Word count target: "
            f"{constraints.get('length', {}).get('min_words', 'N/A')} - "
            f"{constraints.get('length', {}).get('max_words', 'N/A')} words."
        ),
        "",
        f"Voice guidance: {style.get('voice', '')}",
        f"Cadence guidance: {style.get('cadence', '')}",
        f"Diction guidance: {style.get('diction', '')}",
        f"Keyword usage: {style.get('keywords_usage', '')}",
        "Never reference zodiac or astrology in any form.",
        "",
        "Subject details for the narrative:",
        f"Name: {_stringify(record.get('name'))}",
        f"Date of birth: {_stringify(record.get('dob') or record.get('birth_date'))}",
        f"Time of birth: {_stringify(record.get('time_of_birth') or record.get('birth_time'))}",
        f"Place of birth: {_stringify(record.get('place_of_birth') or record.get('birth_city'))}",
        f"Gender: {_stringify(record.get('gender'))}",
        f"City: {_stringify(record.get('city'))}",
        f"Hobbies: {', '.join(hobbies) if hobbies else 'n/a'}",
        f"Interests: {', '.join(interests) if interests else 'n/a'}",
        f"Bio: {_stringify(record.get('bio') or record.get('summary'))}",
        f"Additional keywords to weave naturally: {', '.join(keywords) if keywords else 'none supplied'}",
        "",
        "Output must strictly adhere to this JSON schema (no extra fields):",
        contract_summary,
    ]
    return "\n".join(part for part in prompt_parts if part is not None)
