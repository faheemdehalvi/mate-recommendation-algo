from __future__ import annotations

"""Feature engineering: derive T (t0..t9) and E (e0..e9) from survey responses.

Deterministic transformations with bounded outputs [0,1].
"""

from typing import Tuple
import numpy as np
import pandas as pd


def _avg_s(df: pd.DataFrame, s_idx: int) -> np.ndarray:
    cols = [f"s{s_idx}_q{i}" for i in range(1, 4)]
    return df[cols].mean(axis=1).to_numpy(dtype=float) / 5.0


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def compute_traits(df: pd.DataFrame) -> pd.DataFrame:
    """Compute T0..T9 per spec. Returns a DataFrame with user_id + t0..t9."""
    out = pd.DataFrame()
    out["user_id"] = df["user_id"]
    t0 = _avg_s(df, 1)  # Humor
    t1 = _avg_s(df, 2)  # Empathy
    t2 = _avg_s(df, 3)  # Curiosity
    t3 = _avg_s(df, 4)  # Discipline
    t4 = _avg_s(df, 5)  # Authenticity
    t5 = _avg_s(df, 6)  # Communication
    t6 = _avg_s(df, 7)  # Optimism
    t7 = _avg_s(df, 8)  # Emotional depth
    t8 = _avg_s(df, 9)  # Affection
    t9 = (t3 + t4 + t5) / 3.0  # Stability composite

    for i, arr in enumerate([t0, t1, t2, t3, t4, t5, t6, t7, t8, t9]):
        out[f"t{i}"] = np.clip(arr, 0.0, 1.0)
    return out


def compute_engagement(df: pd.DataFrame, traits: pd.DataFrame, *, seed: int = 42) -> pd.DataFrame:
    """Compute E0..E9. Deterministic via seeded RNG per user."""
    rng = np.random.default_rng(seed)
    out = pd.DataFrame()
    out["user_id"] = df["user_id"]

    T = traits.set_index("user_id")
    # Pull traits as arrays aligned with df
    ta = np.column_stack([T.loc[df["user_id"], f"t{i}"].to_numpy(dtype=float) for i in range(10)])
    t0, t1, t2, t3, t4, t5, t6, t7, t8, t9 = [ta[:, i] for i in range(10)]

    # e0: Humor response time → random(0.5–1) * T0 (deterministic per user)
    # We generate a per-user multiplier using a seeded RNG stream.
    mult = rng.random(size=len(df)) * 0.5 + 0.5
    e0 = mult * t0

    # e1: Emotional reciprocity → avg(T1, T7, T8)
    e1 = (t1 + t7 + t8) / 3.0

    # e2: Novelty seeking → avg(T2, T6)
    e2 = (t2 + t6) / 2.0

    # e3: Stability vs chaos → 1 - T9
    e3 = 1.0 - t9

    # e4: Communication frequency → 0.5 + (T5 / 2)
    e4 = 0.5 + (t5 / 2.0)

    # e5: Responsiveness variance → random(0–0.2) + (1 - e3)
    noise = rng.random(size=len(df)) * 0.2
    e5 = noise + (1.0 - e3)

    # e6: Attachment speed → sigmoid(T7 + T8 - T9)
    e6 = _sigmoid(t7 + t8 - t9)

    # e7: Humor adaptability → (T0 + T2 + T6) / 3
    e7 = (t0 + t2 + t6) / 3.0

    # e8: Empathy modulation → (T1 + T7) / 2
    e8 = (t1 + t7) / 2.0

    # e9: Independence → (1 - T5)
    e9 = 1.0 - t5

    e_list = [e0, e1, e2, e3, e4, e5, e6, e7, e8, e9]
    for i, arr in enumerate(e_list):
        out[f"e{i}"] = np.clip(arr, 0.0, 1.0)
    return out

