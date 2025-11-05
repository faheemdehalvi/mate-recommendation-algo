"""CLI tool to generate Mate-style profiles via OpenAI ChatCompletion."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


REPO_ROOT = Path(__file__).resolve().parent
DATA_PATH = Path("mate_db.csv")
FALLBACK_PATHS = [
    Path("data") / "mate_db.csv",
    Path("matchmaking_algo") / "data" / "mate_db.csv",
]


def load_client() -> OpenAI:
    """Instantiate an OpenAI client using the API key from the environment."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY missing. Set it in your .env file.")
    return OpenAI(api_key=api_key)


def locate_csv() -> Path:
    """Return the path to the mate_db.csv file."""
    env_path = os.getenv("MATE_DB_PATH")
    if env_path:
        explicit = Path(env_path).expanduser()
        if not explicit.is_absolute():
            explicit = (REPO_ROOT / explicit).resolve()
        if explicit.exists():
            return explicit
        raise FileNotFoundError(f"mate_db.csv not found at MATE_DB_PATH={explicit}")

    for candidate in [DATA_PATH, *FALLBACK_PATHS]:
        candidate_path = candidate if candidate.is_absolute() else (REPO_ROOT / candidate)
        if candidate_path.exists():
            return candidate_path
    raise FileNotFoundError(
        "mate_db.csv not found. Set MATE_DB_PATH or place the file in project root / data directory."
    )


def get_user_record(user_id: int, csv_path: Path) -> Dict[str, str]:
    """Fetch a user record from the CSV matching the id."""
    df = pd.read_csv(csv_path)
    matches = df[df["user_id"] == user_id]
    if matches.empty:
        raise ValueError(f"No matching user found for id={user_id}.")
    return matches.to_dict(orient="records")[0]


def build_prompt(record: Dict[str, str]) -> str:
    """Construct the generation prompt using the CSV record."""
    name = record.get("name", "Unknown")
    dob = record.get("dob") or record.get("birth_date") or "an unknown date"
    place = record.get("place_of_birth") or record.get("birth_city") or "an unknown place"
    hobbies = record.get("hobbies") or record.get("tags") or "N/A"
    interests = record.get("interests") or "N/A"
    bio = record.get("bio") or record.get("summary") or ""

    return (
        f"Generate a witty Mate-style dating profile for {name} born on {dob} in {place}. "
        f"Hobbies: {hobbies}. "
        f"Interests: {interests}. "
        f"Bio: {bio}. "
        "Make it creative, engaging, and concise with a catchy title and short paragraphs."
    )


def generate_profile_text(client: OpenAI, prompt: str) -> str:
    """Call OpenAI ChatCompletion to generate the profile text."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a witty content writer for the Mate app."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def sanitize_name(name: str) -> str:
    """Sanitize name for directory creation."""
    return re.sub(r"[^A-Za-z0-9]", "", name) or "user"


def save_profile(user_id: int, name: str, text: str) -> Path:
    """Persist the generated profile to disk."""
    safe_name = sanitize_name(name)
    output_dir = Path("profiles") / f"{user_id}_{safe_name}"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "profile.txt"
    file_path.write_text(text, encoding="utf-8")
    return file_path


def main() -> None:
    """Entry point for CLI execution."""
    try:
        client = load_client()
        csv_path = locate_csv()
        user_id = int(input("Enter user_id: ").strip())
        record = get_user_record(user_id, csv_path)
        name = record.get("name", "User")
        prompt = build_prompt(record)
        print("\n🪄 Generating profile...\n")
        profile_text = generate_profile_text(client, prompt)
        output_path = save_profile(user_id, name, profile_text)
        print(f"\n✅ Profile generated for {name}!\nSaved at: {output_path}\n")
    except Exception as exc:
        print(f"❌ Error: {exc}")


if __name__ == "__main__":
    main()
