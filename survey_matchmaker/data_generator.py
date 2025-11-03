from __future__ import annotations

"""Synthetic data generator for survey-based matchmaking.

Generates 200 users with 9 surveys × 3 questions each (Likert 1..5).
Deterministic using a fixed RNG seed.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import random
import os
import pandas as pd


SURVEY_COUNT = 9
QUESTIONS_PER_SURVEY = 3
N_USERS = 200
GLOBAL_SEED = 42


@dataclass(frozen=True)
class User:
    user_id: int
    name: str
    age: int
    gender: str
    city: str


def _fake_name(rng: random.Random, i: int) -> str:
    firsts = [
        "Alex", "Jordan", "Taylor", "Riley", "Casey", "Avery", "Morgan", "Reese",
        "Quinn", "Skyler", "Rowan", "Parker", "Dakota", "Emerson", "Finley",
    ]
    lasts = [
        "Lee", "Patel", "Kim", "Garcia", "Smith", "Brown", "Singh", "Khan",
        "Nguyen", "Chen", "Sharma", "Das", "Iyer", "Mehta", "Roy",
    ]
    return f"{rng.choice(firsts)} {rng.choice(lasts)}"


def _fake_city(rng: random.Random) -> str:
    cities = [
        "Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad",
        "Pune", "Kolkata", "Jaipur", "Ahmedabad", "Surat",
        "New York", "London", "Paris", "Berlin", "Singapore",
    ]
    return rng.choice(cities)


def generate_users(n: int = N_USERS, *, seed: int = GLOBAL_SEED) -> List[User]:
    rng = random.Random(seed)
    users: List[User] = []
    for i in range(1, n + 1):
        name = _fake_name(rng, i)
        age = rng.randint(18, 45)
        gender = rng.choice(["M", "F"])  # binary for simplicity per spec
        city = _fake_city(rng)
        users.append(User(i, name, age, gender, city))
    return users


def generate_survey_responses(n: int = N_USERS, *, seed: int = GLOBAL_SEED) -> pd.DataFrame:
    """Create a DataFrame of 200 users × (metadata + 27 questions)."""
    users = generate_users(n, seed=seed)
    rng = random.Random(seed + 123)

    records: List[Dict[str, int | str]] = []
    for u in users:
        row: Dict[str, int | str] = {
            "user_id": u.user_id,
            "name": u.name,
            "age": u.age,
            "gender": u.gender,
            "city": u.city,
        }
        for s in range(1, SURVEY_COUNT + 1):
            for q in range(1, QUESTIONS_PER_SURVEY + 1):
                key = f"s{s}_q{q}"
                # Likert 1..5; mildly biased by survey to vary distributions
                base = rng.randint(1, 5)
                if s in (1, 3, 7):
                    base = min(5, base + (1 if rng.random() < 0.2 else 0))
                row[key] = base
        records.append(row)

    df = pd.DataFrame.from_records(records)
    return df


def save_responses_csv(df: pd.DataFrame, path: str = "survey_matchmaker/output/survey_responses.csv") -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path

