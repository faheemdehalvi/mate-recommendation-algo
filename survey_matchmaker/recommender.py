from __future__ import annotations

"""Hybrid recommender using T/E cosine similarity and weighted blend."""

from typing import List, Tuple, Dict
import numpy as np
import pandas as pd

try:
    from sklearn.metrics.pairwise import cosine_similarity as _sk_cosine
    HAS_SK = True
except Exception:  # pragma: no cover
    HAS_SK = False
    _sk_cosine = None  # type: ignore


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    if HAS_SK and _sk_cosine is not None:  # pragma: no cover (prefer our simple path for unit tests)
        return float(_sk_cosine(a.reshape(1, -1), b.reshape(1, -1))[0, 0])
    # Manual cosine
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compute_match_score(TA: np.ndarray, EA: np.ndarray, TB: np.ndarray, EB: np.ndarray) -> float:
    """final_score = 0.6 * cosine(TA, TB) + 0.4 * cosine(EA, EB)"""
    t_sim = _cosine(TA, TB)
    e_sim = _cosine(EA, EB)
    score = 0.6 * t_sim + 0.4 * e_sim
    return float(max(0.0, min(1.0, score)))


def _row_vectors(traits: pd.DataFrame, engagement: pd.DataFrame, user_id: int) -> Tuple[np.ndarray, np.ndarray]:
    t_row = traits.loc[traits.user_id == user_id]
    e_row = engagement.loc[engagement.user_id == user_id]
    if t_row.empty or e_row.empty:
        raise ValueError(f"Unknown user_id {user_id}")
    T = t_row[[f"t{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    E = e_row[[f"e{i}" for i in range(10)]].to_numpy(dtype=float)[0]
    return T, E


def find_best_matches(user_id: int, traits: pd.DataFrame, engagement: pd.DataFrame, top_k: int = 5) -> List[Tuple[int, float]]:
    """Return top_k (other_user_id, score) sorted desc."""
    T0, E0 = _row_vectors(traits, engagement, user_id)
    pairs: List[Tuple[int, float]] = []
    for uid in traits.user_id.tolist():
        if uid == user_id:
            continue
        T1, E1 = _row_vectors(traits, engagement, uid)
        score = compute_match_score(T0, E0, T1, E1)
        pairs.append((int(uid), score))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:top_k]


def recommend_pairs(traits: pd.DataFrame, engagement: pd.DataFrame, *, threshold: float = 0.75, seed: int = 42) -> List[Tuple[int, int, float]]:
    """Randomly sample pairs with score > threshold. Returns list of (user_id_a, user_id_b, score)."""
    rng = np.random.default_rng(seed)
    users = traits.user_id.to_numpy(dtype=int)
    chosen: List[Tuple[int, int, float]] = []
    # Sample a limited number of pairs for speed
    n = len(users)
    if n < 2:
        return []
    idx_pairs = set()
    for _ in range(min(2000, n * 20)):
        i = int(rng.integers(0, n))
        j = int(rng.integers(0, n))
        if i == j:
            continue
        a, b = (users[min(i, j)], users[max(i, j)])
        if (a, b) in idx_pairs:
            continue
        idx_pairs.add((a, b))
        TA, EA = _row_vectors(traits, engagement, a)
        TB, EB = _row_vectors(traits, engagement, b)
        score = compute_match_score(TA, EA, TB, EB)
        if score >= threshold:
            chosen.append((int(a), int(b), float(score)))
    return chosen

