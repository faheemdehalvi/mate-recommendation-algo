import argparse
from pathlib import Path

from src.pipeline import RecommenderPipeline


def run_batch(root: Path):
    data_path = str(root / "data" / "mate_db.csv")
    config_path = str(root / "config.json")
    pipe = RecommenderPipeline(data_path, config_path)
    out = pipe.recommend_all(topn=10)
    out_path = root / "recommendations_simple.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


def run_single(root: Path, user_id: int, topn: int):
    data_path = str(root / "data" / "mate_db.csv")
    config_path = str(root / "config.json")
    pipe = RecommenderPipeline(data_path, config_path)
    recs = pipe.recommend_for_user(user_id, topn=topn)

    # Enrich with profile basics for readability
    by_id = {int(r["user_id"]): r for r in pipe.df.to_dict(orient="records")}
    if recs.empty:
        print(f"No compatible candidates found for user_id={user_id} with current filters.")
        return
    print(f"Top {topn} matches for user_id={user_id}:")
    for _, row in recs.iterrows():
        m_id = int(row["match_id"])
        prof = by_id.get(m_id, {})
        name = prof.get("name")
        age = prof.get("age")
        city = prof.get("city")
        score = float(row["compatibility_score"])
        vscore = float(row.get("vedic_lite_score", 0.0))
        vconf = float(row.get("vedic_confidence", 0.0))
        print(f"- {m_id}: {name} ({age}, {city}) — score={score:.4f} [V:{vscore:.2f}/C:{vconf:.2f}]")


def run_interactive(root: Path):
    data_path = str(root / "data" / "mate_db.csv")
    config_path = str(root / "config.json")
    pipe = RecommenderPipeline(data_path, config_path)
    user_ids = set(map(int, pipe.df["user_id"].tolist()))
    print("Mate Recommender — Interactive Mode")
    print("Press Enter on user_id to exit.")
    while True:
        raw_uid = input("Enter user_id: ").strip()
        if raw_uid == "":
            break
        if not raw_uid.isdigit():
            print("Please enter a numeric user_id.")
            continue
        uid = int(raw_uid)
        if uid not in user_ids:
            print(f"user_id {uid} not found. Try another.")
            continue
        raw_topn = input("Top-N [default 5]: ").strip()
        topn = 5 if raw_topn == "" else max(1, int(raw_topn))
        recs = pipe.recommend_for_user(uid, topn=topn)
        if recs.empty:
            print("No compatible candidates found with current filters.\n")
            continue
        by_id = {int(r["user_id"]): r for r in pipe.df.to_dict(orient="records")}
        print(f"Top {topn} matches for user_id={uid}:")
        for _, row in recs.iterrows():
            m_id = int(row["match_id"])
            prof = by_id.get(m_id, {})
            name = prof.get("name")
            age = prof.get("age")
            city = prof.get("city")
            score = float(row["compatibility_score"])
            vscore = float(row.get("vedic_lite_score", 0.0))
            vconf = float(row.get("vedic_confidence", 0.0))
            print(f"- {m_id}: {name} ({age}, {city}) — score={score:.4f} [V:{vscore:.2f}/C:{vconf:.2f}]")
        print("")


def main():
    parser = argparse.ArgumentParser(description="Mate recommender runner")
    parser.add_argument("--user_id", type=int, default=None, help="User ID to query")
    parser.add_argument("--topn", type=int, default=5, help="Top-N matches to display")
    parser.add_argument("--interactive", action="store_true", help="Interactive prompt to query user IDs")
    args = parser.parse_args()

    root = Path(__file__).parent
    if args.interactive:
        run_interactive(root)
    elif args.user_id is not None:
        run_single(root, args.user_id, args.topn)
    else:
        run_batch(root)


if __name__ == "__main__":
    main()
