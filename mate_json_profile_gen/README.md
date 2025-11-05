Mate JSON Profile Generator
===========================

This CLI builds third-person Mate profiles using a JSON specification and the OpenAI API.

Setup
-----

1. Install dependencies:

   ```bash
   pip install pandas python-dotenv openai
   ```

2. Add your API key (and optionally a custom CSV path) to `.env`:

   ```bash
   echo "OPENAI_API_KEY=sk-your-key" >> .env
   # optional override if mate_db.csv lives elsewhere
   echo "MATE_DB_PATH=/absolute/or/relative/path/to/mate_db.csv" >> .env
   ```

3. Ensure `mate_db.csv` is available. By default the CLI expects the file at `mate_json_profile_gen/data/mate_db.csv`.
   If you already have `matchmaking_algo/data/mate_db.csv`, or provide `MATE_DB_PATH`, the tool will use that location automatically.

Usage
-----

```bash
python -m mate_json_profile_gen.main
```

Enter the desired `user_id` when prompted. The script will:

* Load the JSON template at `data/profile_schema.json`.
* Build a structured prompt honoring the contract and constraints.
* Call OpenAI with `response_format=json_object`.
* Save the results into `mate_json_profile_gen/profiles/<user_id>_<Name>/profile.(txt|json)`.
* Also mirror the JSON file to `<repo_root>/profiles_json/<user_id>_<Name>/profile.json` for frontend access.

Output Contract
---------------

The model is required to respect the `profile_schema.json` contract. Generated JSON includes:

* `title` — 5–8 word hook.
* `profile_text` — Second-person free prose in narrative paragraphs (no lists, no first-person language).
* `keywords` — Three to five descriptors present in the prose.
* `tone` — Single word capturing the emotional register.

Troubleshooting
---------------

* `OPENAI_API_KEY is not set` — verify `.env` or environment variables.
* `User not found` — confirm the entry in `mate_db.csv` or adjust casing.
* JSON parsing errors — the API reply might not follow the contract; re-run or tighten the template instructions.
