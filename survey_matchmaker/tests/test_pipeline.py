from __future__ import annotations

import os
import sqlite3
import pandas as pd

from survey_matchmaker.data_generator import generate_survey_responses
from survey_matchmaker.feature_engineering import compute_traits, compute_engagement
from survey_matchmaker.recommender import compute_match_score, find_best_matches
from survey_matchmaker.database_builder import build_database


def test_end_to_end_pipeline(tmp_path):
    # Generate
    df = generate_survey_responses()
    assert df.shape[0] == 200
    # 5 metadata columns + 27 answers
    assert df.shape[1] == 5 + 27

    # Features
    traits = compute_traits(df)
    engagement = compute_engagement(df, traits)
    assert traits.shape[1] == 1 + 10
    assert engagement.shape[1] == 1 + 10
    # Values in [0,1]
    for i in range(10):
        assert traits[f"t{i}"].between(0.0, 1.0).all()
        assert engagement[f"e{i}"].between(0.0, 1.0).all()

    # Recommender score bounds
    u0 = int(traits.user_id.iloc[0])
    u1 = int(traits.user_id.iloc[1])
    import numpy as np
    TA = traits.loc[traits.user_id == u0, [f"t{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    EA = engagement.loc[engagement.user_id == u0, [f"e{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    TB = traits.loc[traits.user_id == u1, [f"t{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    EB = engagement.loc[engagement.user_id == u1, [f"e{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    score = compute_match_score(TA, EA, TB, EB)
    assert 0.0 <= score <= 1.0

    top = find_best_matches(u0, traits, engagement, top_k=5)
    assert len(top) <= 5 and len(top) > 0
    assert all(0.0 <= s <= 1.0 for _, s in top)

    # Database build
    db_path = os.path.join(tmp_path, "survey_matchmaker.db")
    build_database(df, traits, engagement, db_path)
    assert os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # Check tables exist and have rows
        for table in ("users", "survey_responses", "traits", "engagement"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            assert cur.fetchone()[0] > 0
    finally:
        conn.close()

