"""Offline astronomy primitives and place resolution.

This module provides:
 - resolve_place: resolve a free-text place via local CSV gazetteer or
   explicit "lat,lon,offset" input; returns a dict with name, lat, lon, tz_offset.
 - compute_astro: compute UTC Julian Day, tropical/sidereal longitudes of Sun/Moon,
   Lahiri ayanamsa, and derived indices (moon sign, nakshatra, tithi, paksha),
   plus lookup attributes (gana, yoni, nadi, sign_lord) and a confidence score.

No network calls are made. If `pyswisseph` is available, high-precision positions
are used. Otherwise, we fall back to deterministic, low-precision algorithms with
documented limits:
 - Sun longitude: approximate analytic solution of the solar mean anomaly;
   typical error ±1°.
 - Moon longitude: a reduced-term series (Meeus-inspired) with a handful of
   dominant periodic terms; typical error ±3–5°.
 - Lahiri ayanamsa: linear approximation anchored at ~24.0° in 2025,
   secular drift −50.29″/yr.

These are sufficient for coarse sidereal sign/nakshatra mapping for offline use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import math
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

try:
    import swisseph as swe  # type: ignore
    HAS_SWISSEPH = True
except Exception:  # pragma: no cover - absence is a supported path
    swe = None  # type: ignore
    HAS_SWISSEPH = False


from .tables import NAKSHATRA_META, SIGN_LORDS, ELEMENTS


_GAZETTEER_CACHE: Optional[list[dict[str, str]]] = None


def _data_path(filename: str) -> Path:
    """Return absolute path to a file in the project-level data/ directory."""
    here = Path(__file__).resolve()
    root = here.parent.parent
    return root / "data" / filename


def _load_gazetteer() -> list[dict[str, str]]:
    global _GAZETTEER_CACHE
    if _GAZETTEER_CACHE is not None:
        return _GAZETTEER_CACHE
    path = _data_path("cities_min.csv")
    if not path.exists():
        raise FileNotFoundError(f"Gazetteer not found at {path}")
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    _GAZETTEER_CACHE = rows
    return rows


def _try_parse_latlon_offset(s: str) -> Optional[Tuple[float, float, float]]:
    try:
        parts = [p.strip() for p in s.split(",")]
        if len(parts) != 3:
            return None
        lat = float(parts[0])
        lon = float(parts[1])
        off = float(parts[2])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and -14 <= off <= 14):
            return None
        return lat, lon, off
    except Exception:
        return None


def resolve_place(place: str) -> Dict[str, Any]:
    """Resolve a place string using the offline gazetteer or lat,lon,offset.

    Args:
        place: free-text, e.g. "Hubli, IN" or "15.36,75.12,5.5".

    Returns:
        {"name": str, "lat": float, "lon": float, "tz_offset": float}

    Raises:
        ValueError: if the place cannot be resolved.
    """
    if not isinstance(place, str) or not place.strip():
        raise ValueError("place must be a non-empty string")

    # First, support explicit lat,lon,offset input.
    parsed = _try_parse_latlon_offset(place)
    if parsed is not None:
        lat, lon, off = parsed
        return {
            "name": f"{lat:.4f},{lon:.4f}",
            "lat": float(lat),
            "lon": float(lon),
            "tz_offset": float(off),
            "_resolved_via": "latlon",
        }

    # Gazetteer lookup
    target = place.strip().lower().replace(" ", "")
    target = target.replace("\u200c", "")  # zero-width chars
    rows = _load_gazetteer()

    def norm_name(r: dict[str, str]) -> str:
        nm = (r.get("name", "") + "," + r.get("country", "")).lower()
        return nm.replace(" ", "")

    # Prioritize exact city,country match; fallback to startswith by city
    candidates = [r for r in rows if norm_name(r) == target]
    if not candidates:
        # also try loose match where user might not include country
        city_only = target.split(",")[0]
        candidates = [r for r in rows if r.get("name", "").lower().replace(" ", "") == city_only]

    if not candidates:
        raise ValueError(
            "Place not found in local gazetteer and not in 'lat,lon,offset' format."
        )

    r = candidates[0]
    return {
        "name": f"{r['name']}, {r['country']}",
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "tz_offset": float(r["tz_offset_hours"]),
        "_resolved_via": "gazetteer",
    }


def _parse_local_dt(dob: str, tob: str) -> Tuple[datetime, bool]:
    """Parse local date/time strings. Returns dt (naive) and flag minute_missing."""
    try:
        y, m, d = [int(x) for x in dob.split("-")]
        hhmm = tob.split(":")
        if len(hhmm) == 1:
            h = int(hhmm[0])
            mi = 0
            minute_missing = True
        else:
            h = int(hhmm[0])
            mi = int(hhmm[1])
            minute_missing = False
        return datetime(y, m, d, h, mi), minute_missing
    except Exception:
        raise ValueError("Invalid dob/tob format. Expected YYYY-MM-DD and HH:MM")


def _to_utc(dt_local: datetime, tz_offset_hours: float) -> datetime:
    # Local time = UTC + offset  =>  UTC = Local - offset
    return (dt_local - timedelta(hours=tz_offset_hours)).replace(tzinfo=timezone.utc)


def _julian_day(dt_utc: datetime) -> float:
    """Compute Julian Day (UTC) for a datetime in UTC.

    Algorithm: Fliegel & Van Flandern / classic Meeus-style JD conversion.
    """
    y = dt_utc.year
    m = dt_utc.month
    d = dt_utc.day
    hh = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600 + dt_utc.microsecond / 3_600_000_000
    if m <= 2:
        y -= 1
        m += 12
    A = y // 100
    B = 2 - A + (A // 4)
    JD0 = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return JD0 + hh / 24.0


def _sun_longitude_deg_approx(jd: float) -> float:
    """Low-precision solar ecliptic longitude (tropical), degrees [0,360).
    Accuracy ~±1°. Source: simplified mean anomaly + equation of center.
    """
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360.0
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    return lam % 360.0


def _moon_longitude_deg_approx(jd: float) -> float:
    """Low-precision lunar ecliptic longitude (tropical), degrees [0,360).
    Reduced series; typical error ±3–5°. Sufficient for sign/nakshatra binning.
    """
    T = (jd - 2451545.0) / 36525.0
    L0 = (218.3164477 + 481267.88123421 * T - 0.0015786 * T * T) % 360.0  # mean lon
    D = math.radians((297.8501921 + 445267.1114034 * T - 0.0018819 * T * T) % 360.0)
    M = math.radians((357.5291092 + 35999.0502909 * T - 0.0001536 * T * T) % 360.0)
    Mp = math.radians((134.9633964 + 477198.8675055 * T + 0.0087414 * T * T) % 360.0)
    F = math.radians((93.2720950 + 483202.0175233 * T - 0.0036539 * T * T) % 360.0)

    # Dominant periodic terms for longitude (Meeus-like)
    lon = L0
    lon += 6.289 * math.sin(Mp)
    lon += 1.274 * math.sin(2 * D - Mp)
    lon += 0.658 * math.sin(2 * D)
    lon += 0.214 * math.sin(2 * Mp)
    lon += 0.110 * math.sin(D)
    lon += 0.059 * math.sin(2 * D - 2 * Mp)
    lon += 0.057 * math.sin(2 * D - M - Mp)
    lon += 0.053 * math.sin(2 * D + Mp)
    lon += 0.046 * math.sin(2 * D - M)
    return lon % 360.0


def _ayanamsa_lahiri_deg_linear(dt_utc: datetime) -> float:
    """Approximate Lahiri ayanamsa in degrees via linear model.
    Anchor ~24.0° at year 2025 with secular drift −50.29″/yr.
    """
    year = dt_utc.year + (dt_utc.timetuple().tm_yday - 1) / (366 if _is_leap(dt_utc.year) else 365)
    drift_deg_per_year = -50.29 / 3600.0
    return (24.0 + drift_deg_per_year * (year - 2025.0)) % 360.0


def _is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _calc_longitudes(jd_utc: float, dt_utc: datetime) -> Tuple[float, float, float, bool]:
    """Return (sun_lon_trop, moon_lon_trop, ayanamsa, used_fallback)."""
    if HAS_SWISSEPH and swe is not None:
        try:
            sun = swe.calc_ut(jd_utc, swe.SUN)
            moon = swe.calc_ut(jd_utc, swe.MOON)
            sun_lon = float(sun[0][0])
            moon_lon = float(moon[0][0])
            # Ayanamsa Lahiri
            try:
                ayan = float(swe.get_ayanamsa_ut(jd_utc, swe.SIDM_LAHIRI))
            except Exception:
                ayan = float(swe.get_ayanamsa(jd_utc))  # type: ignore
            return sun_lon % 360.0, moon_lon % 360.0, ayan % 360.0, False
        except Exception:
            # fall through to approximation
            pass

    # Fallback
    sun_lon = _sun_longitude_deg_approx(jd_utc)
    moon_lon = _moon_longitude_deg_approx(jd_utc)
    ayan = _ayanamsa_lahiri_deg_linear(dt_utc)
    return sun_lon, moon_lon, ayan, True


def _idx_from_angle(angle_deg: float, sector_deg: float, count: int) -> int:
    return 1 + int((angle_deg % 360.0) // sector_deg)


def compute_astro(*, dob: str, tob: str, place: Dict[str, Any]) -> Dict[str, Any]:
    """Compute astro primitives and derived attributes.

    Args:
        dob: YYYY-MM-DD
        tob: HH:MM (24h local)
        place: dict from resolve_place()

    Returns:
        A dict with positions and derived indices per schema.
    """
    dt_local, minute_missing = _parse_local_dt(dob, tob)
    tz_offset = float(place["tz_offset"])  # hours
    dt_utc = _to_utc(dt_local, tz_offset)
    jd_utc = _julian_day(dt_utc)

    sun_lon_trop, moon_lon_trop, ayanamsa_deg, used_fallback = _calc_longitudes(jd_utc, dt_utc)
    sun_lon_sid = (sun_lon_trop - ayanamsa_deg) % 360.0
    moon_lon_sid = (moon_lon_trop - ayanamsa_deg) % 360.0

    moon_sign = _idx_from_angle(moon_lon_sid, 30.0, 12)
    nakshatra_id = _idx_from_angle(moon_lon_sid, 360.0 / 27.0, 27)
    tithi_id = _idx_from_angle((moon_lon_trop - sun_lon_trop) % 360.0, 12.0, 30)
    paksha = "Shukla" if 1 <= tithi_id <= 15 else "Krishna"

    # Lookup attributes
    nak = NAKSHATRA_META.get(nakshatra_id)
    if not nak:
        raise ValueError("Nakshatra metadata missing for id: %d" % nakshatra_id)
    gana = nak["gana"]
    yoni = nak["yoni"]
    nadi = nak["nadi"]
    sign_lord = SIGN_LORDS.get(moon_sign)

    # Confidence
    confidence = 0.9
    if place.get("_resolved_via") != "gazetteer":
        confidence -= 0.3
    if minute_missing:
        confidence -= 0.2
    if used_fallback:
        confidence -= 0.2
    # Moon near nakshatra boundary (<0.2°)
    width = 360.0 / 27.0
    pos_in = moon_lon_sid % width
    edge_dist = min(pos_in, width - pos_in)
    if edge_dist < 0.2:
        confidence -= 0.1
    confidence = max(0.0, min(1.0, confidence))

    return {
        "jd_utc": float(jd_utc),
        "ayanamsa_deg": float(ayanamsa_deg),
        "sun_lon_tropical": float(sun_lon_trop),
        "moon_lon_tropical": float(moon_lon_trop),
        "sun_lon_sidereal": float(sun_lon_sid),
        "moon_lon_sidereal": float(moon_lon_sid),
        "moon_sign": int(moon_sign),
        "nakshatra_id": int(nakshatra_id),
        "tithi_id": int(tithi_id),
        "paksha": paksha,
        "gana": gana,
        "yoni": yoni,
        "nadi": nadi,
        "sign_lord": sign_lord,
        "confidence": float(confidence),
    }

