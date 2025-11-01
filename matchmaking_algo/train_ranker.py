"""
Stub for future ML ranker training (e.g., XGBoost / LambdaMART style LTR).

data/interactions.csv schema (to be logged):
user_id, target_id, action {like|pass|view|message_start}, dwell_ms, ts

Suggested labeling:
- positives = like/message_start or dwell >= 2500ms
- negatives = pass or short view

Steps (future):
- Load features for (user, candidate) pairs and join with interactions.
- Train XGBoost binary classifier or ranking model.
- Export to models/ranker_xgb.json and have ranker.py load and predict.
"""

def main():
    print("Training stub. See TODO in file docstring.")


if __name__ == "__main__":
    main()

