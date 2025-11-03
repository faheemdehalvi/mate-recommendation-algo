"""Top-level API for T/E feature computation.

Exposes `compute_te` which returns a dict containing:
- input echo, resolved place, astro primitives, T and E vectors, and version.

This package performs all computations offline. If `pyswisseph` is available,
high-precision positions are used; otherwise a deterministic low-precision
fallback is applied (documented in astro_offline.py).
"""

from __future__ import annotations

from . import astro_offline
from .te_mapper import compute_vectors
from .profile_gen import generate_witty_profile
from typing import Dict, Any


def compute_te(
    full_name: str,
    dob: str,
    tob: str,
    place: str,
    *,
    disable_hash_jitter: bool = False,
    include_raw_astro: bool = True,
) -> Dict[str, Any]:
    """Compute T/E features for a person given birth details.

    Args:
        full_name: e.g., "Jaden Ekbote".
        dob: Date of birth in YYYY-MM-DD (local calendar) string.
        tob: Time of birth in HH:MM (24h local) string.
        place: Free-text city or "lat,lon,offset"; resolved via local gazetteer.
        disable_hash_jitter: If True, disables tiny deterministic name-based jitter.
        include_raw_astro: Kept for forward-compat; astro primitives are always included.

    Returns:
        A dict per the requested schema containing `astro`, `T`, `E`, and metadata.
    """
    if not isinstance(full_name, str) or not full_name.strip():
        raise ValueError("full_name must be a non-empty string")
    if not isinstance(dob, str) or not isinstance(tob, str) or not isinstance(place, str):
        raise ValueError("dob, tob, and place must be strings")

    resolved = astro_offline.resolve_place(place)
    astro = astro_offline.compute_astro(dob=dob, tob=tob, place=resolved)

    T, E = compute_vectors(
        name=full_name,
        astro=astro,
        disable_hash_jitter=disable_hash_jitter,
    )

    out: Dict[str, Any] = {
        "name": full_name,
        "inputs": {"dob": dob, "tob": tob, "place": place},
        "resolved_place": resolved,
        "astro": astro,
        "T": {f"t{i}": float(T[i]) for i in range(10)},
        "E": {f"e{i}": float(E[i]) for i in range(10)},
        "version": "astro_offline_v1.0",
    }
    return out

__all__ = ["compute_te", "generate_witty_profile"]
