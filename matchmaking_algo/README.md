Mate Recommender (Twitter/X-style, two-stage)

Overview
- Candidate Generation (recall): cosine nearest neighbors over standardized user embeddings (t_* ∪ e_*).
- Feature Assembly: base similarity, tag overlap, age gap, complementarity (energy, humor, risk).
- Heavy Ranker: additive weighted score read from config.json (ML-pluggable later).

Quickstart
- Create a virtualenv and install deps:
  - `cd mate-recs`
  - `python -m pip install -r requirements.txt`
- Run batch to produce recommendations:
  - `python main.py`
  - Outputs `recommendations_simple.csv` with top-10 matches per user.

Optional API
- `uvicorn server:app --reload --port 8000`
- GET `http://localhost:8000/api/feed?user_id=1&topn=10`

Project layout
- `data/mate_db.csv` — single-table DB of user profiles and vectors plus preferences
- `src/recall.py` — cosine recall on standardized embeddings
- `src/features.py` — feature assembly (overlap + complementarity)
- `src/ranker.py` — additive scorer reading `config.json`
- `src/pipeline.py` — orchestration (recall → features → rank)
- `main.py` — batch job to write `recommendations_simple.csv`
- `server.py` — optional FastAPI endpoint `/api/feed`
- `train_ranker.py` — stub for future ML ranker

Acceptance criteria
- Loads `data/mate_db.csv` and finds `[t_* ∪ e_*]` columns
- Standardizes vectors before cosine
- Recall with `K = config.recall_k`
- Computes features: similarity, overlap, complementarity, age_gap
- Scores with additive weights from `config.json`
- Saves `recommendations_simple.csv` with top-10 per user
- API returns `{"cards": [...]}` with top-N

Notes
- Complementarity mapping: introvert↔extrovert, dark↔wholesome, low↔high risk.
- Configurable weights and knobs in `config.json`.

Preferences & Filters
- Dataset fields: `gender_interest` (e.g., any/M/F/NB, comma-separated), `min_age_pref`, `max_age_pref`, `city_interest` (comma-separated)
- Config `filters` in `config.json`:
  - `respect_gender_interest` (default true)
  - `respect_age_range` (default true)
  - `respect_city_preference` (default false)
  - `reciprocal` — require mutual match of interests/ranges (default false)
