from __future__ import annotations

import importlib
from typing import Any


def _basic_checks(out: dict[str, Any]) -> None:
    assert "T" in out and "E" in out and "astro" in out and "resolved_place" in out
    assert len(out["T"]) == 10 and len(out["E"]) == 10
    for k, v in out["T"].items():
        assert k.startswith("t") and isinstance(v, float)
        assert 0.0 <= v <= 1.0
    for k, v in out["E"].items():
        assert k.startswith("e") and isinstance(v, float)
        assert 0.0 <= v <= 1.0
    astro = out["astro"]
    assert 1 <= astro["moon_sign"] <= 12
    assert 1 <= astro["nakshatra_id"] <= 27
    assert 1 <= astro["tithi_id"] <= 30
    assert astro["paksha"] in ("Shukla", "Krishna")
    assert 0.0 <= astro["confidence"] <= 1.0


def test_compute_te_deterministic_same_inputs():
    from te_features import compute_te

    out1 = compute_te("Jaden Ekbote", "2003-02-11", "04:35", "Hubli, IN")
    out2 = compute_te("Jaden Ekbote", "2003-02-11", "04:35", "Hubli, IN")
    _basic_checks(out1)
    _basic_checks(out2)
    assert out1["T"] == out2["T"]
    assert out1["E"] == out2["E"]
    assert out1["astro"]["moon_sign"] == out2["astro"]["moon_sign"]
    assert out1["astro"]["nakshatra_id"] == out2["astro"]["nakshatra_id"]


def test_compute_te_forces_fallback(monkeypatch):
    from te_features import compute_te
    import te_features.astro_offline as ao

    # Force fallback path
    monkeypatch.setattr(ao, "HAS_SWISSEPH", False, raising=False)
    monkeypatch.setattr(ao, "swe", None, raising=False)
    importlib.reload(ao)

    out = compute_te("Test User", "1990-01-15", "12:00", "Hubballi, IN")
    _basic_checks(out)
    # Confidence should reflect fallback penalty (<= 0.7 typically)
    assert out["astro"]["confidence"] <= 0.9

