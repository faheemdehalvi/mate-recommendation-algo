"""
Lightweight Vedic calendar utilities (offline, no external APIs).

Functions provided:
- hindu_date_from_date(date, latitude, longitude, tz) -> dict with keys
  {"tithi", "paksha", "nakshatra", "yoga", "confidence"}
- vedic_lite_weighted_score(dob_user: str, dob_cand: str) -> float in [0,1]

Notes:
- This is a simplified, deterministic placeholder suitable for MVP scoring.
- Confidence is higher when birth_time is present (handled by caller) and
  for dates nearer solstices/equinoxes we lower confidence slightly to
  simulate variability.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict


TITHIS = [f"Tithi_{i}" for i in range(1, 31)]
PAKSHAS = ["Shukla", "Krishna"]
NAKSHATRAS = [f"Nakshatra_{i}" for i in range(1, 28)]
YOGAS = [f"Yoga_{i}" for i in range(1, 28)]


def _parse_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def hindu_date_from_date(d: str, latitude: float, longitude: float, tz: float) -> Dict:
    # Deterministic mapping based on day-of-year
    dt = _parse_date(d)
    doy = dt.timetuple().tm_yday
    tithi = TITHIS[(doy * 3) % 30]
    paksha = PAKSHAS[(doy // 15) % 2]
    nakshatra = NAKSHATRAS[doy % 27]
    yoga = YOGAS[(doy * 2) % 27]

    # Confidence heuristic in [0,1]
    # Base by latitude band and day-of-year spread
    lat_factor = max(0.6, 1.0 - abs(latitude) / 180.0)
    equinox_band = 1.0 - (abs((doy % 182) - 91) / 91.0) * 0.2  # down-weight near equinox
    confidence = max(0.0, min(1.0, 0.6 * lat_factor * equinox_band + 0.2))

    return {
        "tithi": tithi,
        "paksha": paksha,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "confidence": confidence,
    }


def vedic_lite_weighted_score(dob_user: str, dob_cand: str) -> float:
    """
    Simplified compatibility measure based on day-of-year distance.
    Returns value in [0,1], higher is better.
    """
    try:
        du = _parse_date(dob_user)
        dc = _parse_date(dob_cand)
    except Exception:
        return 0.0

    dy_u = du.timetuple().tm_yday
    dy_c = dc.timetuple().tm_yday
    diff = abs(dy_u - dy_c)
    # wrap around 365
    diff = min(diff, 365 - diff)
    # Near-opposite birthdays and near-same both get decent scores
    # Use a smooth kernel peaking at 0 and 182.5
    same = 1.0 - (diff / 91.25)  # ~quarter-year decay
    opp = 1.0 - (abs(diff - 182.5) / 91.25)
    score = max(0.0, 0.6 * max(same, 0.0) + 0.4 * max(opp, 0.0))
    return min(1.0, score)

