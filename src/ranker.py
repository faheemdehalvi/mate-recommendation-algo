from typing import Dict

import pandas as pd


class AdditiveRanker:
    def __init__(self, config: Dict):
        self.w_sim = float(config.get("weights", {}).get("similarity", 0.30))
        self.w_comp = float(config.get("weights", {}).get("complementarity", 0.20))
        self.w_vedic = float(config.get("weights", {}).get("vedic_lite", 0.50))
        self.vedic_min_conf = float(config.get("vedic", {}).get("min_conf", 0.30))
        self.vedic_low_shrink = float(config.get("vedic", {}).get("low_conf_shrink", 0.5))
        # Legacy fields kept but unused in the final score
        self.w_nov = float(config.get("weights", {}).get("novelty", 0.0))
        self.w_pri = float(config.get("weights", {}).get("prior", 0.0))
        self.novelty_value = float(config.get("novelty_value", 0.05))
        self.prior_value = float(config.get("prior_value", 0.0))
        self.age_penalty = float(config.get("age_penalty", 0.0))

    def score(self, feats: pd.DataFrame) -> pd.DataFrame:
        df = feats.copy()
        df["novelty"] = self.novelty_value
        df["prior"] = self.prior_value

        # Confidence-aware Vedic weighting
        import numpy as np
        if "vedic_confidence" in df.columns:
            conf = df["vedic_confidence"].astype(float)
        else:
            # empty or missing column
            conf = pd.Series(0.0, index=df.index)
        vedic_weight = np.where(conf >= self.vedic_min_conf, self.w_vedic, self.w_vedic * self.vedic_low_shrink)

        # Compute final additive score
        df["final_score"] = (
            self.w_sim * df.get("base_sim", 0.0)
            + self.w_comp * df.get("comp_index", 0.0)
            + vedic_weight * df.get("vedic_lite_score", 0.0)
            - self.age_penalty * df.get("age_gap", 0)
        )
        return df


# TODO(Copilot): If models/ranker_xgb.json exists, use XGBoost predict_proba instead of additive weights
