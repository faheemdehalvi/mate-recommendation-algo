"""Utility functions for persisting generated profiles."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", name or "")
    return cleaned or "user"


def _profiles_root() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles"


def _frontend_root() -> Path:
    return Path(__file__).resolve().parents[2] / "profiles_json"


def save_outputs(user_id: int, name: str, data: Dict[str, Any]) -> Path:
    """Persist both text and JSON outputs for the generated profile.

    Returns:
        Path to the profile output directory.
    """
    root = _profiles_root()
    root.mkdir(parents=True, exist_ok=True)

    dir_path = root / f"{user_id}_{_sanitize_name(name)}"
    dir_path.mkdir(parents=True, exist_ok=True)

    profile_text = data.get("profile_text", "")
    txt_path = dir_path / "profile.txt"
    txt_path.write_text(profile_text, encoding="utf-8")

    json_path = dir_path / "profile.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    frontend_root = _frontend_root()
    frontend_root.mkdir(parents=True, exist_ok=True)
    frontend_dir = frontend_root / f"{user_id}_{_sanitize_name(name)}"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    frontend_json = frontend_dir / "profile.json"
    frontend_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    return dir_path
