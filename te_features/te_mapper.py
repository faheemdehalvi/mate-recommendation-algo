"""Deterministic mapping from astro primitives to 10D T/E vectors.

The mapping is heuristic and rule-based, using only:
- Sidereal moon sign (element, modality via sign index)
- Nakshatra attributes (gana, yoni, nadi)
- Tithi/paksha
- Sign ruler (by moon sign)
- A stable name-hash seed to add tiny jitter ε and break ties deterministically.

All outputs are in [0,1].
"""

from __future__ import annotations

from typing import Dict, Any, Tuple, List, Sequence
import hashlib
import math

from .tables import SIGN_LORDS, ELEMENTS

# Human-readable labels and descriptions for T and E dimensions.
# These are referenced by the CLI for interactive output.
T_DIM_META: List[Tuple[str, str]] = [
    ("Openness/Curiosity", "Air signs; Jupiter/Venus rulers; Deva/Manushya gana."),
    ("Warmth/Agreeableness", "Shukla paksha, Deva gana; lower for Rakshasa."),
    ("Drive/Ambition", "Fire signs; Mars/Sun rulership; boost at tithis 2–6,18–22."),
    ("Stability/Rhythm", "Earth signs; Adi Nadi; lower for Antya Nadi."),
    ("Emotional Depth", "Water signs; higher in late Krishna paksha."),
    ("Playfulness/Humor", "Air signs; Tiger/Deer/Monkey yoni."),
    ("Intellect/Analysis", "Mercury/Jupiter rulers; small lunar harmonic terms."),
    ("Sensuality/Affection", "Venus-ruled; Cow/Elephant/Horse yoni; slight Friday boost."),
    ("Protectiveness", "Rakshasa gana; Tiger yoni (capped at 0.9)."),
    ("Communication Pace", "Air signs; slightly lower for Saturn-ruled."),
]

E_DIM_META: List[Tuple[str, str]] = [
    ("Initiative", "Mars/Sun rulers; Fire signs."),
    ("Responsiveness Window", "Maps paksha+tithi to earlier/later hours."),
    ("Novelty Seeking", "Air/Fire signs; Manushya/Rakshasa gana."),
    ("Routine Affinity", "Earth signs; Adi Nadi."),
    ("Emotional Availability", "Water signs; Deva/Manushya gana."),
    ("Pace of Attachment", "Lower for Saturn; higher for Venus/Jupiter."),
    ("Flirt Frequency", "Venus-ruled; playful yonis."),
    ("Green-flag Probability", "Composite of Warmth, Depth, Intellect."),
    ("Boundary Strength", "Rakshasa + Mars; lowered with strong Venus."),
    ("Independence", "Air/Fire + Saturn; slightly lower for Water-heavy."),
]

def get_t_dim_meta() -> Sequence[Tuple[str, str]]:
    return tuple(T_DIM_META)

def get_e_dim_meta() -> Sequence[Tuple[str, str]]:
    return tuple(E_DIM_META)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _name_seed(full_name: str) -> int:
    h = hashlib.sha1(full_name.encode("utf-8")).hexdigest()
    return int(h[:12], 16)


def _epsilon(seed: int, disable: bool) -> float:
    if disable:
        return 0.0
    return (seed % 7) / 1000.0


def _is_fire(sign: int) -> bool:
    return ELEMENTS.get(sign) == "Fire"


def _is_earth(sign: int) -> bool:
    return ELEMENTS.get(sign) == "Earth"


def _is_air(sign: int) -> bool:
    return ELEMENTS.get(sign) == "Air"


def _is_water(sign: int) -> bool:
    return ELEMENTS.get(sign) == "Water"


def _weekday_from_jd_utc(jd: float) -> int:
    # Monday=0..Sunday=6 (ISO-like). JD 2451545.0 was Saturday (2000-01-01 12:00 TT),
    # we approximate using jd+0.5 to get 00:00, then modulo 7.
    # For a rough + optional feature only.
    w = int((jd + 0.5 + 1) % 7)  # shift to Monday=0 baseline
    return w


def compute_vectors(*, name: str, astro: Dict[str, Any], disable_hash_jitter: bool) -> Tuple[list[float], list[float]]:
    """Compute 10D T and E vectors from astro primitives.

    Args:
        name: full name string used to generate stable jitter.
        astro: dict from compute_astro containing positions and attributes.
        disable_hash_jitter: if True, no jitter.

    Returns:
        (T, E) lists with 10 floats each in [0,1].
    """
    seed = _name_seed(name)
    eps = _epsilon(seed, disable_hash_jitter)

    moon_sign = int(astro["moon_sign"])  # 1..12
    nak_gana = astro["gana"]
    nak_yoni = astro["yoni"]
    nak_nadi = astro["nadi"]
    tithi = int(astro["tithi_id"])  # 1..30
    paksha = astro["paksha"]
    sign_lord = astro["sign_lord"]
    moon_sid = float(astro["moon_lon_sidereal"])  # degrees
    jd_utc = float(astro["jd_utc"])  # for optional weekday

    # Helpers
    is_air = _is_air(moon_sign)
    is_fire = _is_fire(moon_sign)
    is_earth = _is_earth(moon_sign)
    is_water = _is_water(moon_sign)

    # Numerical encoders for harmonic terms
    sin_m = math.sin(math.radians(moon_sid))
    cos_m = math.cos(math.radians(moon_sid))

    # t0 Openness: Air, Jupiter/Venus, Deva/Manushya
    t0 = 0.45
    if is_air:
        t0 += 0.18
    if sign_lord in ("Jupiter", "Venus"):
        t0 += 0.12
    if nak_gana in ("Deva", "Manushya"):
        t0 += 0.08
    t0 = _clamp01(t0 + eps)

    # t1 Warmth: Shukla, Deva; penalty Rakshasa
    t1 = 0.5
    if paksha == "Shukla":
        t1 += 0.12
    if nak_gana == "Deva":
        t1 += 0.12
    if nak_gana == "Rakshasa":
        t1 -= 0.12
    t1 = _clamp01(t1 + eps)

    # t2 Drive: Fire + Mars/Sun; +0.05 early tithis (2-6,18-22)
    t2 = 0.45
    if is_fire:
        t2 += 0.18
    if sign_lord in ("Mars", "Sun"):
        t2 += 0.15
    if (2 <= tithi <= 6) or (18 <= tithi <= 22):
        t2 += 0.05
    t2 = _clamp01(t2 + eps)

    # t3 Stability: Earth + Nadi=Adi; penalty Nadi=Antya
    t3 = 0.45
    if is_earth:
        t3 += 0.18
    if nak_nadi == "Adi":
        t3 += 0.10
    if nak_nadi == "Antya":
        t3 -= 0.10
    t3 = _clamp01(t3 + eps)

    # t4 Emotional Depth: Water + Krishna upper tithis (16..30)
    t4 = 0.45
    if is_water:
        t4 += 0.18
    if paksha == "Krishna" and tithi >= 20:
        t4 += 0.10
    t4 = _clamp01(t4 + eps)

    # t5 Playfulness: Air + Tiger/Deer/Monkey yoni
    t5 = 0.45
    if is_air:
        t5 += 0.12
    if nak_yoni in ("Tiger", "Deer", "Monkey"):
        t5 += 0.12
    t5 = _clamp01(t5 + eps)

    # t6 Intellect: Mercury/Jupiter ruled; add small harmonic terms
    t6 = 0.45
    if sign_lord in ("Mercury", "Jupiter"):
        t6 += 0.15
    t6 += 0.04 * ((sin_m + 1) / 2)  # small contribution from lunar phase angle
    t6 += 0.04 * ((cos_m + 1) / 2)
    t6 = _clamp01(t6 + eps)

    # t7 Sensuality: Venus + Cow/Elephant/Horse; +0.05 if Friday (optional)
    t7 = 0.45
    if sign_lord == "Venus":
        t7 += 0.15
    if nak_yoni in ("Cow", "Elephant", "Horse"):
        t7 += 0.10
    weekday = _weekday_from_jd_utc(jd_utc)
    if weekday == 4:  # Friday
        t7 += 0.05
    t7 = _clamp01(t7 + eps)

    # t8 Protectiveness: Rakshasa + Tiger; cap 0.9
    t8 = 0.40
    if nak_gana == "Rakshasa":
        t8 += 0.20
    if nak_yoni == "Tiger":
        t8 += 0.12
    t8 = min(0.9, _clamp01(t8 + eps))

    # t9 Communication Pace: Air; penalty Saturn-ruled
    t9 = 0.5
    if is_air:
        t9 += 0.15
    if sign_lord == "Saturn":
        t9 -= 0.12
    t9 = _clamp01(t9 + eps)

    T = [t0, t1, t2, t3, t4, t5, t6, t7, t8, t9]

    # E-features (engagement/energy)
    # e0 Initiative: Mars/Sun + Fire
    e0 = 0.45 + (0.15 if sign_lord in ("Mars", "Sun") else 0.0) + (0.12 if is_fire else 0.0)
    e0 = _clamp01(e0 + eps)

    # e1 Responsiveness window: Map paksha+tithi linearly. Shukla early → lower value, Krishna late → higher.
    span = (tithi - 1) / 29.0
    base = span if paksha == "Krishna" else (1.0 - span)
    e1 = _clamp01(0.2 + 0.6 * base + eps)

    # e2 Novelty seeking: Air/Fire + Manushya/Rakshasa
    e2 = 0.45
    if is_air or is_fire:
        e2 += 0.15
    if nak_gana in ("Manushya", "Rakshasa"):
        e2 += 0.12
    e2 = _clamp01(e2 + eps)

    # e3 Routine affinity: Earth + Adi Nadi
    e3 = 0.45
    if is_earth:
        e3 += 0.15
    if nak_nadi == "Adi":
        e3 += 0.10
    e3 = _clamp01(e3 + eps)

    # e4 Emotional availability: Water + Deva/Manushya
    e4 = 0.45
    if is_water:
        e4 += 0.15
    if nak_gana in ("Deva", "Manushya"):
        e4 += 0.10
    e4 = _clamp01(e4 + eps)

    # e5 Pace of attachment: ↓ Saturn; ↑ Venus/Jupiter
    e5 = 0.5
    if sign_lord == "Saturn":
        e5 -= 0.12
    if sign_lord in ("Venus", "Jupiter"):
        e5 += 0.12
    e5 = _clamp01(e5 + eps)

    # e6 Flirt frequency: Venus + playful yonis
    e6 = 0.45
    if sign_lord == "Venus":
        e6 += 0.15
    if nak_yoni in ("Tiger", "Deer", "Monkey"):
        e6 += 0.10
    e6 = _clamp01(e6 + eps)

    # e7 Green-flag probability: composite of t1,t4,t6
    e7 = _clamp01((T[1] * 0.35 + T[4] * 0.35 + T[6] * 0.30) + eps)

    # e8 Boundary strength: ↑ Rakshasa + Mars; ↓ extreme Venus
    e8 = 0.45
    if nak_gana == "Rakshasa":
        e8 += 0.15
    if sign_lord == "Mars":
        e8 += 0.12
    if sign_lord == "Venus" and T[7] > 0.7:
        e8 -= 0.08
    e8 = _clamp01(e8 + eps)

    # e9 Independence: Air/Fire + Saturn; ↓ Water-heavy combos
    e9 = 0.45
    if is_air or is_fire:
        e9 += 0.12
    if sign_lord == "Saturn":
        e9 += 0.10
    if is_water and T[4] > 0.65:
        e9 -= 0.08
    e9 = _clamp01(e9 + eps)

    E = [e0, e1, e2, e3, e4, e5, e6, e7, e8, e9]
    return T, E
