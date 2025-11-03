"""Static lookup tables for sidereal astrology primitives.

Includes:
- SIGN_LORDS: 1..12 (Aries..Pisces) → lord in TitleCase.
- ELEMENTS: 1..12 → Fire/Earth/Air/Water.
- NAKSHATRA_META: 1..27 → {name,gana,yoni,nadi} with TitleCase strings.

Notes:
- Nadi follows a repeating pattern Adi→Madhya→Antya across nakshatras.
- Gana/yoni values follow common traditional assignments suitable for offline use.
"""

from __future__ import annotations

from typing import Dict

# Aries..Pisces
SIGN_LORDS: Dict[int, str] = {
    1: "Mars",
    2: "Venus",
    3: "Mercury",
    4: "Moon",
    5: "Sun",
    6: "Mercury",
    7: "Venus",
    8: "Mars",
    9: "Jupiter",
    10: "Saturn",
    11: "Saturn",
    12: "Jupiter",
}

ELEMENTS: Dict[int, str] = {
    1: "Fire",
    2: "Earth",
    3: "Air",
    4: "Water",
    5: "Fire",
    6: "Earth",
    7: "Air",
    8: "Water",
    9: "Fire",
    10: "Earth",
    11: "Air",
    12: "Water",
}


def _nadi_for(n: int) -> str:
    # Repeating Adi, Madhya, Antya pattern across 27 nakshatras
    idx = (n - 1) % 3
    return ("Adi", "Madhya", "Antya")[idx]


NAKSHATRA_META: Dict[int, Dict[str, str]] = {
    1: {"name": "Ashwini", "gana": "Deva", "yoni": "Horse", "nadi": _nadi_for(1)},
    2: {"name": "Bharani", "gana": "Manushya", "yoni": "Elephant", "nadi": _nadi_for(2)},
    3: {"name": "Krittika", "gana": "Rakshasa", "yoni": "Sheep", "nadi": _nadi_for(3)},
    4: {"name": "Rohini", "gana": "Manushya", "yoni": "Serpent", "nadi": _nadi_for(4)},
    5: {"name": "Mrigashira", "gana": "Deva", "yoni": "Serpent", "nadi": _nadi_for(5)},
    6: {"name": "Ardra", "gana": "Rakshasa", "yoni": "Dog", "nadi": _nadi_for(6)},
    7: {"name": "Punarvasu", "gana": "Deva", "yoni": "Cat", "nadi": _nadi_for(7)},
    8: {"name": "Pushya", "gana": "Deva", "yoni": "Sheep", "nadi": _nadi_for(8)},
    9: {"name": "Ashlesha", "gana": "Rakshasa", "yoni": "Cat", "nadi": _nadi_for(9)},
    10: {"name": "Magha", "gana": "Rakshasa", "yoni": "Rat", "nadi": _nadi_for(10)},
    11: {"name": "Purva Phalguni", "gana": "Manushya", "yoni": "Rat", "nadi": _nadi_for(11)},
    12: {"name": "Uttara Phalguni", "gana": "Manushya", "yoni": "Cow", "nadi": _nadi_for(12)},
    13: {"name": "Hasta", "gana": "Deva", "yoni": "Buffalo", "nadi": _nadi_for(13)},
    14: {"name": "Chitra", "gana": "Rakshasa", "yoni": "Tiger", "nadi": _nadi_for(14)},
    15: {"name": "Swati", "gana": "Deva", "yoni": "Buffalo", "nadi": _nadi_for(15)},
    16: {"name": "Vishakha", "gana": "Rakshasa", "yoni": "Tiger", "nadi": _nadi_for(16)},
    17: {"name": "Anuradha", "gana": "Deva", "yoni": "Deer", "nadi": _nadi_for(17)},
    18: {"name": "Jyeshtha", "gana": "Rakshasa", "yoni": "Deer", "nadi": _nadi_for(18)},
    19: {"name": "Mula", "gana": "Rakshasa", "yoni": "Dog", "nadi": _nadi_for(19)},
    20: {"name": "Purva Ashadha", "gana": "Manushya", "yoni": "Monkey", "nadi": _nadi_for(20)},
    21: {"name": "Uttara Ashadha", "gana": "Manushya", "yoni": "Mongoose", "nadi": _nadi_for(21)},
    22: {"name": "Shravana", "gana": "Deva", "yoni": "Monkey", "nadi": _nadi_for(22)},
    23: {"name": "Dhanishta", "gana": "Rakshasa", "yoni": "Lion", "nadi": _nadi_for(23)},
    24: {"name": "Shatabhisha", "gana": "Rakshasa", "yoni": "Horse", "nadi": _nadi_for(24)},
    25: {"name": "Purva Bhadrapada", "gana": "Manushya", "yoni": "Lion", "nadi": _nadi_for(25)},
    26: {"name": "Uttara Bhadrapada", "gana": "Manushya", "yoni": "Cow", "nadi": _nadi_for(26)},
    27: {"name": "Revati", "gana": "Deva", "yoni": "Elephant", "nadi": _nadi_for(27)},
}


def _validate() -> None:
    # Validate keys and TitleCase-ish values
    assert all(1 <= k <= 12 for k in SIGN_LORDS.keys())
    assert all(v and v[0].isupper() for v in SIGN_LORDS.values())
    assert set(ELEMENTS.keys()) == set(range(1, 13))
    for k, v in NAKSHATRA_META.items():
        assert 1 <= k <= 27
        for key in ("name", "gana", "yoni", "nadi"):
            s = v[key]
            assert isinstance(s, str) and s and s[0].isupper(), f"Bad TitleCase for {key} in nak {k}"


_validate()

