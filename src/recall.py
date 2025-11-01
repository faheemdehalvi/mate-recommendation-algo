from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity


class CandidateGenerator:
    """
    Cosine-similarity candidate generator over standardized embeddings.
    Embedding columns are detected or provided and standardized via StandardScaler.
    """

    def __init__(self, df: pd.DataFrame, embed_cols: List[str]):
        self.df = df.reset_index(drop=True).copy()
        self.embed_cols = embed_cols

        # Map user_id <-> index
        self.user_id_col = "user_id"
        if self.user_id_col not in self.df.columns:
            raise ValueError("Expected 'user_id' column in dataframe")

        self.user_ids = self.df[self.user_id_col].tolist()
        self.id_to_idx = {uid: i for i, uid in enumerate(self.user_ids)}

        # Prepare standardized matrix
        X = self.df[self.embed_cols].astype(float).fillna(0.0).to_numpy()
        self.scaler = StandardScaler()
        X_std = self.scaler.fit_transform(X)
        # Cosine similarity across all users
        self.sim_matrix = cosine_similarity(X_std)

    def topk_for_user(self, user_id: int, k: int) -> List[Tuple[int, float]]:
        if user_id not in self.id_to_idx:
            return []
        idx = self.id_to_idx[user_id]
        sims = self.sim_matrix[idx].copy()
        # Exclude self
        sims[idx] = -np.inf
        # Argpartition then sort for top-k
        k_eff = min(k, len(sims) - 1)
        if k_eff <= 0:
            return []
        top_idx = np.argpartition(sims, -k_eff)[-k_eff:]
        # Sort descending
        top_sorted = top_idx[np.argsort(sims[top_idx])[::-1]]
        return [(int(self.user_ids[j]), float(sims[j])) for j in top_sorted]

    def topk_for_all(self, k: int) -> Dict[int, List[Tuple[int, float]]]:
        result: Dict[int, List[Tuple[int, float]]] = {}
        for uid in self.user_ids:
            result[uid] = self.topk_for_user(uid, k)
        return result


def find_embedding_columns(df: pd.DataFrame) -> List[str]:
    cols = [c for c in df.columns if c.startswith("t_") or c.startswith("e_")]
    if not cols:
        raise ValueError("No embedding columns found (expected t_* or e_* columns)")
    # Sort for consistency
    return sorted(cols)

