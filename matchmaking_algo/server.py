from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pathlib import Path
from src.pipeline import RecommenderPipeline
from profile_service import ProfileInput, build_profile_prompt_dict


class Card(BaseModel):
    user_id: Optional[int] = None
    match_id: int
    compatibility_score: float
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    tags: Optional[str] = None
    filters: Optional[dict] = None
    vedic: Optional[dict] = None


app = FastAPI(title="Mate Recommender API")

# Load pipeline at startup
ROOT = Path(__file__).parent
DATA_PATH = str(ROOT / "data" / "mate_db.csv")
CONFIG_PATH = str(ROOT / "config.json")
PIPE = RecommenderPipeline(DATA_PATH, CONFIG_PATH)


@app.get("/api/feed")
def feed(user_id: int, topn: int = 10):
    if user_id not in set(PIPE.df.user_id.astype(int).tolist()):
        raise HTTPException(status_code=404, detail="user_id not found")
    recs = PIPE.recommend_for_user(user_id, topn=topn)
    # Enrich cards with a few profile fields
    by_id = {int(r["user_id"]): r for r in PIPE.df.to_dict(orient="records")}

    cards = []
    for _, row in recs.iterrows():
        m_id = int(row["match_id"])
        prof = by_id.get(m_id, {})
        filter_meta = {
            "gender": bool(row.get("filter_gender", True)),
            "age": bool(row.get("filter_age", True)),
            "city": bool(row.get("filter_city", True)),
        }
        vedic_meta = {
            "score": float(row.get("vedic_lite_score", 0.0)),
            "confidence": float(row.get("vedic_confidence", 0.0)),
        }
        cards.append(Card(
            user_id=int(user_id),
            match_id=m_id,
            compatibility_score=float(row["compatibility_score"]),
            name=prof.get("name"),
            age=prof.get("age"),
            city=prof.get("city"),
            tags=prof.get("tags"),
            filters=filter_meta,
            vedic=vedic_meta,
        ).dict())
    return {"cards": cards}


# TODO(Copilot): Add filters: min_age, max_age, city, gender_interest via query params


@app.post("/api/profile/prompt")
def profile_prompt(payload: ProfileInput):
    try:
        prompt = build_profile_prompt_dict(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return prompt
