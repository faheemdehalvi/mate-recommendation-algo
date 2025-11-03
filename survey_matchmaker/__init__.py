"""Synthetic survey-based T/E pipeline for matchmaking research.

Modules:
- data_generator: creates deterministic synthetic survey responses for 200 users.
- feature_engineering: derives T (t0..t9) and E (e0..e9) embeddings.
- recommender: hybrid cosine-based similarity and pairing utilities.
- database_builder: builds and populates an SQLite database with users, responses, traits, engagement, matches.
- cli: orchestrates steps from the command line.

No external APIs and no network usage.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.1.0"

