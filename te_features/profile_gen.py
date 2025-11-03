"""Local witty profile generator based on T/E features and astro attributes.

No external APIs are used. Text is generated via deterministic templates with
synonym choices selected by a stable name-based seed so the same input yields
the same profile every time.
"""

from __future__ import annotations

from typing import Dict, Any, List
import hashlib
import random

from .tables import ELEMENTS, NAKSHATRA_META, SIGN_LORDS
from .te_mapper import get_t_dim_meta, get_e_dim_meta


def _seed_from_name(name: str) -> int:
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()
    return int(h[:12], 16)


def _star_for_nak(nak_id: int) -> str:
    meta = NAKSHATRA_META.get(nak_id)
    return meta["name"] if meta else f"Nakshatra {nak_id}"


def _choose(rng: random.Random, options: List[str]) -> str:
    return options[rng.randrange(len(options))]


def generate_witty_profile(te_result: Dict[str, Any], *, max_sentences: int = 5) -> str:
    """Generate a witty, compact profile from the computed T/E features.

    Args:
        te_result: Output of `te_features.compute_te`.
        max_sentences: Upper bound for number of sentences in the profile (3–6 recommended).

    Returns:
        A deterministic, human-readable paragraph.
    """
    if not isinstance(te_result, dict):
        raise ValueError("te_result must be a dict from compute_te")
    name = te_result.get("name", "This person")
    astro = te_result.get("astro", {})
    T = te_result.get("T", {})
    E = te_result.get("E", {})

    rng = random.Random(_seed_from_name(str(name)))

    moon_sign = int(astro.get("moon_sign", 1))
    element = ELEMENTS.get(moon_sign, "Fire")
    sign_lord = SIGN_LORDS.get(moon_sign, "Mars")
    nak_id = int(astro.get("nakshatra_id", 1))
    nak_name = _star_for_nak(nak_id)
    gana = astro.get("gana", "Manushya")
    yoni = astro.get("yoni", "Horse")
    paksha = astro.get("paksha", "Shukla")

    # Rank T and E dims
    t_meta = list(get_t_dim_meta())
    e_meta = list(get_e_dim_meta())
    t_sorted = sorted(((k, v) for k, v in T.items()), key=lambda kv: kv[1], reverse=True)
    e_sorted = sorted(((k, v) for k, v in E.items()), key=lambda kv: kv[1], reverse=True)

    # Map idx to label
    def t_label(idx: int) -> str:
        return t_meta[idx][0]

    def e_label(idx: int) -> str:
        return e_meta[idx][0]

    # Helpers for describing top traits
    t_top_idx = int(t_sorted[0][0][1:]) if t_sorted else 0
    e_top_idx = int(e_sorted[0][0][1:]) if e_sorted else 0

    openers = [
        f"Meet {name}, a {element.lower()}-tinged soul with {sign_lord.lower()}-ruled undertones.",
        f"{name} blends {element.lower()} ease with {sign_lord.lower()} grit—unexpectedly magnetic.",
        f"{name}? Think {element.lower()} vibes guided by {sign_lord}—effortless yet intentional.",
    ]

    nak_lines = [
        f"Born under {nak_name}, a {gana.lower()}-gana star with a {yoni.lower()} yoni.",
        f"{nak_name} natives carry that {gana.lower()} gait—there’s a quiet {yoni.lower()} confidence here.",
        f"{nak_name} lends a {gana.lower()} sheen; the {yoni.lower()} yoni adds playful edges.",
    ]

    paksha_lines = [
        f"A {paksha.lower()} paksha imprint keeps moods { _choose(rng, ['buoyant','reflective','steady']) } and intentions { _choose(rng, ['clear','tuned','centered']) }.",
        f"With a {paksha.lower()} moon, the emotional tide is { _choose(rng, ['forward-leaning','tidy','anchored']) } but still { _choose(rng, ['nuanced','warm','alive']) }.",
    ]

    # Trait & energy synthesis
    t_key = t_label(t_top_idx)
    e_key = e_label(e_top_idx)
    trait_lines = [
        f"Primary vibe: {t_key.lower()}—it shows up in the small choices.",
        f"Expect {t_key.lower()} up front, and {e_key.lower()} once the conversation warms.",
        f"The signature mix is {t_key.lower()} with a side of {e_key.lower()}—distinct but balanced.",
    ]

    # Call-to-action style closer using E
    e2_idx = int(e_sorted[1][0][1:]) if len(e_sorted) > 1 else e_top_idx
    e2_key = e_label(e2_idx)
    closers = [
        f"Message match: bring { _choose(rng, ['curiosity','banter','honesty']) } and a dash of {e2_key.lower()}.",
        f"Best lane: lead with {e_key.lower()}, flow with {e2_key.lower()}—it clicks.",
        f"Green flag: shared {e_key.lower()} energy; bonus points for {e2_key.lower()} moments.",
    ]

    sentences: List[str] = []
    sentences.append(_choose(rng, openers))
    sentences.append(_choose(rng, nak_lines))
    sentences.append(_choose(rng, paksha_lines))
    sentences.append(_choose(rng, trait_lines))
    sentences.append(_choose(rng, closers))

    # Trim to max_sentences (min 3)
    max_sentences = max(3, min(6, int(max_sentences)))
    return " " .join(sentences[:max_sentences])


__all__ = ["generate_witty_profile"]

