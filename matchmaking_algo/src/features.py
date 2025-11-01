from typing import Dict, List, Tuple, Optional

import pandas as pd

from .vedic_calendar import hindu_date_from_date, vedic_lite_weighted_score

def _normalize_text(x: str) -> str:
    return (x or "").strip().lower()


def _tag_set(s: str) -> set:
    if not isinstance(s, str):
        return set()
    return set([t.strip().lower() for t in s.split(',') if t.strip()])


def _energy_bucket(v: str) -> float:
    v = _normalize_text(v)
    # Map common survey variants
    if v in {"introvert", "low"}:
        return 0.0
    if v in {"extrovert", "high", "extravert"}:
        return 1.0
    # ambivert/medium/neutral
    return 0.5


def _humor_is_dark(v: str) -> bool:
    v = _normalize_text(v)
    return any(tok in v for tok in ["dark", "edgy", "sarcastic"])


def _humor_is_wholesome(v: str) -> bool:
    v = _normalize_text(v)
    return any(tok in v for tok in ["wholesome", "clean", "light"])


def _risk_bucket(v: str) -> float:
    v = _normalize_text(v)
    if v in {"low", "cautious"}:
        return 0.0
    if v in {"high", "bold", "adventurous"}:
        return 1.0
    return 0.5


def _parse_gender_interest(v: Optional[str]) -> List[str]:
    if not v or not isinstance(v, str):
        return []
    toks = [t.strip().lower() for t in v.split(',') if t.strip()]
    return toks


INDIA_CITY_MAP = {
    # name: (lat, lon, tz_offset_hours)
    "delhi": (28.6139, 77.2090, 5.5),
    "new delhi": (28.6139, 77.2090, 5.5),
    "mumbai": (19.0760, 72.8777, 5.5),
    "bengaluru": (12.9716, 77.5946, 5.5),
    "bangalore": (12.9716, 77.5946, 5.5),
    "chennai": (13.0827, 80.2707, 5.5),
    "kolkata": (22.5726, 88.3639, 5.5),
    "hyderabad": (17.3850, 78.4867, 5.5),
}


def _city_geocode(name: Optional[str]):
    if not name:
        return INDIA_CITY_MAP["delhi"]
    key = _normalize_text(name)
    return INDIA_CITY_MAP.get(key, INDIA_CITY_MAP["delhi"])


def _int_or_none(x) -> Optional[int]:
    try:
        if x is None or x == "":
            return None
        return int(x)
    except Exception:
        return None


def _hard_filter_flags(u: dict, c: dict, filters: dict) -> Dict[str, bool]:
    # Gender
    gender_ok = True
    if filters.get("gender", False):
        u_interest = _parse_gender_interest(u.get("gender_interest"))
        if u_interest and "any" not in u_interest:
            gender_ok = _normalize_text(c.get("gender", "")) in u_interest

    # Age
    age_ok = True
    if filters.get("age", False):
        u_min = _int_or_none(u.get("min_age_pref"))
        u_max = _int_or_none(u.get("max_age_pref"))
        c_age = _int_or_none(c.get("age")) or 0
        if u_min is not None and c_age < u_min:
            age_ok = False
        if u_max is not None and c_age > u_max:
            age_ok = False

    # City
    city_ok = True
    if filters.get("city", False):
        pref = _normalize_text(u.get("city_interest", "any"))
        if pref and pref != "any":
            city_ok = _normalize_text(c.get("city", "")) == pref

    return {"gender": bool(gender_ok), "age": bool(age_ok), "city": bool(city_ok)}


def build_features(
    df: pd.DataFrame,
    candidates: Dict[int, List[Tuple[int, float]]],
    comp_mix: dict,
    filters: Optional[dict] = None,
) -> pd.DataFrame:
    rows = []
    by_id = {int(r["user_id"]): r for r in df.to_dict(orient="records")}
    filters = filters or {}

    for uid, cands in candidates.items():
        u = by_id.get(int(uid))
        if not u:
            continue
        u_tags = _tag_set(u.get("tags", ""))
        u_age = int(u.get("age", 0) or 0)
        u_energy = _energy_bucket(u.get("social_energy", ""))
        u_dark = _humor_is_dark(u.get("humor_style", ""))
        u_wholesome = _humor_is_wholesome(u.get("humor_style", ""))
        u_risk = _risk_bucket(u.get("risk_taking", ""))

        for cid, base_sim in cands:
            c = by_id.get(int(cid))
            if not c:
                continue
            # Hard filters before assembling features
            fflags = _hard_filter_flags(u, c, filters)
            if not (fflags["gender"] and fflags["age"] and fflags["city"]):
                continue
            c_tags = _tag_set(c.get("tags", ""))
            c_age = int(c.get("age", 0) or 0)
            c_energy = _energy_bucket(c.get("social_energy", ""))
            c_dark = _humor_is_dark(c.get("humor_style", ""))
            c_wholesome = _humor_is_wholesome(c.get("humor_style", ""))
            c_risk = _risk_bucket(c.get("risk_taking", ""))

            tag_overlap = len(u_tags & c_tags)
            age_gap = abs(u_age - c_age)

            energy_comp = 1 if (u_energy <= 0.25 and c_energy >= 0.75) or (u_energy >= 0.75 and c_energy <= 0.25) else 0
            humor_comp = 1 if (u_dark and c_wholesome) or (u_wholesome and c_dark) else 0
            risk_comp = 1 if (u_risk <= 0.25 and c_risk >= 0.75) or (u_risk >= 0.75 and c_risk <= 0.25) else 0

            comp_index = (
                comp_mix.get("energy", 0.34) * energy_comp
                + comp_mix.get("humor", 0.33) * humor_comp
                + comp_mix.get("risk", 0.33) * risk_comp
            )

            # Vedic-lite scoring
            vedic_lite_score = 0.0
            vedic_confidence = 0.0
            u_dob = _normalize_text(str(u.get("birth_date", "")))
            c_dob = _normalize_text(str(c.get("birth_date", "")))
            if u_dob and c_dob and len(u_dob) == 10 and len(c_dob) == 10:
                vedic_lite_score = vedic_lite_weighted_score(u_dob, c_dob)
                # City-based confidence
                u_lat, u_lon, u_tz = _city_geocode(u.get("birth_city"))
                c_lat, c_lon, c_tz = _city_geocode(c.get("birth_city"))
                try:
                    u_cal = hindu_date_from_date(u_dob, u_lat, u_lon, u_tz)
                    c_cal = hindu_date_from_date(c_dob, c_lat, c_lon, c_tz)
                    # Boost confidence if birth_time present for each side
                    u_conf = float(u_cal.get("confidence", 0.0))
                    c_conf = float(c_cal.get("confidence", 0.0))
                    if _normalize_text(str(u.get("birth_time", ""))):
                        u_conf = min(1.0, u_conf + 0.15)
                    if _normalize_text(str(c.get("birth_time", ""))):
                        c_conf = min(1.0, c_conf + 0.15)
                    vedic_confidence = max(0.0, min(1.0, min(u_conf, c_conf)))
                except Exception:
                    vedic_lite_score = 0.0
                    vedic_confidence = 0.0

            rows.append({
                "user_id": int(uid),
                "match_id": int(cid),
                "base_sim": float(base_sim),
                "tag_overlap": int(tag_overlap),
                "age_gap": int(age_gap),
                "energy_comp": int(energy_comp),
                "humor_comp": int(humor_comp),
                "risk_comp": int(risk_comp),
                "comp_index": float(comp_index),
                "filter_gender": fflags["gender"],
                "filter_age": fflags["age"],
                "filter_city": fflags["city"],
                "vedic_lite_score": float(vedic_lite_score),
                "vedic_confidence": float(vedic_confidence),
            })

    feats = pd.DataFrame(rows)

    # TODO(Copilot): Add per-trait diffs: for each t_i, add abs(t_i - t_i_prime)
    # TODO(Copilot): Add age_penalty into ranker (configurable)
    return feats
