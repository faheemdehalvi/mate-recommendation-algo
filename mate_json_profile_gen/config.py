"""Configuration helpers for the Mate JSON profile generator."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment and defaults."""

    openai_api_key: str
    data_path: Path
    template_path: Path


DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "mate_db.csv"
DEFAULT_TEMPLATE = Path(__file__).resolve().parent / "data" / "profile_schema.json"
DATA_FALLBACKS = [
    Path("data") / "mate_db.csv",
    Path("matchmaking_algo") / "data" / "mate_db.csv",
    Path("mate_db.csv"),
]
REPO_ROOT = Path(__file__).resolve().parents[1]


def _resolve_data_path(explicit: Optional[str]) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"mate_db.csv not found at explicit path: {path}")
        return path

    if DEFAULT_DATA.exists():
        return DEFAULT_DATA
    for candidate in DATA_FALLBACKS:
        candidate_path = candidate if candidate.is_absolute() else (REPO_ROOT / candidate)
        if candidate_path.exists():
            return candidate_path
    raise FileNotFoundError("mate_db.csv not found. Please place it in mate_json_profile_gen/data/")


def load_settings(env_file: Optional[str] = None) -> Settings:
    """Load application settings from environment variables."""
    load_dotenv(env_file)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set in the environment.")
    data_path = _resolve_data_path(os.getenv("MATE_DB_PATH"))
    if not DEFAULT_TEMPLATE.exists():
        raise FileNotFoundError(f"profile_schema.json missing at {DEFAULT_TEMPLATE}")
    return Settings(
        openai_api_key=api_key,
        data_path=data_path,
        template_path=DEFAULT_TEMPLATE,
    )
