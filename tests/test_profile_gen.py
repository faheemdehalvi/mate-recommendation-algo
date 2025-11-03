from __future__ import annotations

from te_features import compute_te
from te_features.profile_gen import generate_witty_profile


def test_profile_deterministic_and_nonempty():
    te = compute_te("Sample User", "1995-07-12", "08:10", "Delhi, IN")
    p1 = generate_witty_profile(te)
    p2 = generate_witty_profile(te)
    assert isinstance(p1, str) and len(p1) > 20
    assert p1 == p2  # deterministic for same inputs
    assert te["name"] in p1

