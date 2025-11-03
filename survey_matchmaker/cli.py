from __future__ import annotations

"""CLI for synthetic survey-based matchmaking pipeline.

Commands:
  python -m survey_matchmaker.cli --generate
  python -m survey_matchmaker.cli --compute-features
  python -m survey_matchmaker.cli --build-db
  python -m survey_matchmaker.cli --recommend --top 5
"""

import argparse
import os
import json
from typing import Tuple
import pandas as pd

from .data_generator import generate_survey_responses, save_responses_csv
from .feature_engineering import compute_traits, compute_engagement
from .recommender import find_best_matches, recommend_pairs
from .database_builder import build_database, insert_matches, _connect


OUT_DIR = "survey_matchmaker/output"
RESP_CSV = os.path.join(OUT_DIR, "survey_responses.csv")
TRAITS_CSV = os.path.join(OUT_DIR, "traits.csv")
ENG_CSV = os.path.join(OUT_DIR, "engagement.csv")
MATCHES_CSV = os.path.join(OUT_DIR, "matches.csv")
DB_PATH = os.path.join(OUT_DIR, "survey_matchmaker.db")


def _ensure_outputs() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)


def cmd_generate() -> None:
    _ensure_outputs()
    df = generate_survey_responses()
    save_responses_csv(df, RESP_CSV)
    print(f"[generate] Saved responses to {RESP_CSV} ({len(df)} users)")


def cmd_compute_features() -> None:
    _ensure_outputs()
    if not os.path.exists(RESP_CSV):
        df = generate_survey_responses()
    else:
        df = pd.read_csv(RESP_CSV)
    traits = compute_traits(df)
    engagement = compute_engagement(df, traits)
    traits.to_csv(TRAITS_CSV, index=False)
    engagement.to_csv(ENG_CSV, index=False)
    print(f"[features] Wrote {TRAITS_CSV} and {ENG_CSV}")


def cmd_build_db() -> None:
    _ensure_outputs()
    df = pd.read_csv(RESP_CSV) if os.path.exists(RESP_CSV) else generate_survey_responses()
    traits = pd.read_csv(TRAITS_CSV) if os.path.exists(TRAITS_CSV) else compute_traits(df)
    engagement = pd.read_csv(ENG_CSV) if os.path.exists(ENG_CSV) else compute_engagement(df, traits)
    build_database(df, traits, engagement, DB_PATH)
    print(f"[db] Built SQLite database at {DB_PATH}")


def cmd_recommend(top_k: int) -> None:
    _ensure_outputs()
    df = pd.read_csv(RESP_CSV)
    traits = pd.read_csv(TRAITS_CSV)
    engagement = pd.read_csv(ENG_CSV)
    # Simple demo: compute top matches for first user
    first_user = int(traits.user_id.iloc[0])
    best = find_best_matches(first_user, traits, engagement, top_k=top_k)
    print(f"[recommend] Best matches for user {first_user}: {best}")
    # Recommend pairs and persist to CSV and DB
    pairs = recommend_pairs(traits, engagement, threshold=0.75)
    pd.DataFrame(pairs, columns=["user_id_a", "user_id_b", "score"]).to_csv(MATCHES_CSV, index=False)
    print(f"[recommend] Wrote {len(pairs)} pairs to {MATCHES_CSV}")
    conn = _connect(DB_PATH)
    try:
        insert_matches(conn, [(int(a), int(b), float(s)) for a, b, s in pairs])
    finally:
        conn.close()
    print(f"[recommend] Logged matches to DB {DB_PATH}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="survey_matchmaker", add_help=True)
    p.add_argument("--generate", action="store_true")
    p.add_argument("--compute-features", action="store_true")
    p.add_argument("--build-db", action="store_true")
    p.add_argument("--recommend", action="store_true")
    p.add_argument("--top", type=int, default=5)
    args = p.parse_args(argv)

    if args.generate:
        cmd_generate()
    if args.compute_features:
        cmd_compute_features()
    if args.build_db:
        cmd_build_db()
    if args.recommend:
        cmd_recommend(args.top)
    if not (args.generate or args.compute_features or args.build_db or args.recommend):
        p.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

