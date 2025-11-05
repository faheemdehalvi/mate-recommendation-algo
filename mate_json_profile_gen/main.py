"""CLI entry point for generating Mate profiles via JSON contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .config import Settings, load_settings
from .utils.json_loader import load_prompt_template
from .utils.openai_client import configure_client, generate_profile_json
from .utils.profile_saver import save_outputs
from .utils.prompt_formatter import build_openai_prompt


def get_user_record(user_id: int, csv_path: Path) -> Dict[str, Any]:
    """Fetch the CSV record for the requested user."""
    df = pd.read_csv(csv_path)
    subset = df[df["user_id"] == user_id]
    if subset.empty:
        raise ValueError(f"User id {user_id} not found in {csv_path}.")
    return subset.to_dict(orient="records")[0]


def main() -> None:
    """Run the CLI flow."""
    try:
        settings: Settings = load_settings()
        template = load_prompt_template(settings.template_path)
        client = configure_client(settings.openai_api_key)

        user_id = int(input("Enter user_id: ").strip())

        record = get_user_record(user_id, settings.data_path)
        name = record.get("name", "User")
        prompt = build_openai_prompt(template, record)

        print("\n🪄 Generating third-person profile...\n")
        result = generate_profile_json(client, prompt, template)

        output_dir = save_outputs(user_id, name, result)
        print(f"\n✅ Profile generated for {name}!")
        print(f"Saved to {output_dir}\n")
    except Exception as exc:
        print(f"❌ Error: {exc}")


if __name__ == "__main__":
    main()
