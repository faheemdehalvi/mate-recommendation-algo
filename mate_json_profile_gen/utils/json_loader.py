"""Utilities for loading JSON prompt templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class TemplateLoadError(RuntimeError):
    """Raised when the prompt template cannot be loaded."""


def load_prompt_template(path: str | Path) -> Dict[str, Any]:
    """Load the prompt template JSON from disk.

    Args:
        path: Path to the JSON template file.

    Returns:
        Parsed JSON object.

    Raises:
        TemplateLoadError: If the file does not exist or contains invalid JSON.
    """
    template_path = Path(path)
    if not template_path.exists():
        raise TemplateLoadError(f"Template not found at {template_path}")
    try:
        with template_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise TemplateLoadError(f"Invalid JSON in template {template_path}") from exc

