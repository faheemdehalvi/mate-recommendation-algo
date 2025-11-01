from typing import Dict, List

import json
import pandas as pd

from .recall import CandidateGenerator, find_embedding_columns
from .features import build_features
from .ranker import AdditiveRanker


class RecommenderPipeline:
    def __init__(self, data_path: str, config_path: str):
        self.data_path = data_path
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.df = pd.read_csv(data_path)

        self.embed_cols = find_embedding_columns(self.df)
        self.cand_gen = CandidateGenerator(self.df, self.embed_cols)
        self.ranker = AdditiveRanker(self.config)
        self.recall_k = int(self.config.get("recall_k", 100))

    def recommend_all(self, topn: int = 10) -> pd.DataFrame:
        cands = self.cand_gen.topk_for_all(self.recall_k)
        feats = build_features(
            self.df,
            cands,
            self.config.get("comp_mix", {}),
            self.config.get("filters", {}),
        )
        scored = self.ranker.score(feats)

        # Rank within user and pick top-n
        scored = scored.sort_values(["user_id", "final_score"], ascending=[True, False])
        topn_df = scored.groupby("user_id").head(topn).copy()
        topn_df.rename(columns={"match_id": "match_id", "final_score": "compatibility_score"}, inplace=True)
        return topn_df[["user_id", "match_id", "compatibility_score"]]

    def recommend_for_user(self, user_id: int, topn: int = 10) -> pd.DataFrame:
        cands = {user_id: self.cand_gen.topk_for_user(user_id, self.recall_k)}
        feats = build_features(
            self.df,
            cands,
            self.config.get("comp_mix", {}),
            self.config.get("filters", {}),
        )
        if feats.empty:
            return pd.DataFrame(columns=[
                "user_id","match_id","compatibility_score",
                "filter_gender","filter_age","filter_city",
                "vedic_lite_score","vedic_confidence",
            ])
        scored = self.ranker.score(feats)
        scored = scored[scored["user_id"] == user_id].sort_values("final_score", ascending=False)
        res = scored.head(topn).copy()
        res.rename(columns={"final_score": "compatibility_score"}, inplace=True)
        return res
