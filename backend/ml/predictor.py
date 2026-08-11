"""
ML Predictor
=============
Loads the trained ensemble model and returns risk probability
along with the classified risk level.
"""
import os
import numpy as np
import joblib
from typing import Tuple
from backend.utils.logger import get_logger

logger = get_logger(__name__)

THRESHOLDS = {
    "LOW": (0.0, 0.35),
    "MEDIUM": (0.35, 0.70),
    "HIGH": (0.70, 1.01),
}


class RiskPredictor:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self._load()

    def _load(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info(f"Risk model loaded from {self.model_path}")
        else:
            logger.warning(
                f"Model not found at {self.model_path}. "
                "Using heuristic scoring until model is trained."
            )

    def predict(self, x: np.ndarray) -> Tuple[float, str]:
        """
        Returns:
            risk_probability: float in [0, 1]
            risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
        """
        if self.model is not None:
            try:
                prob = float(self.model.predict_proba(x)[0][1])
            except Exception as e:
                logger.error(f"Model prediction error: {e}")
                prob = self._heuristic_score(x)
        else:
            prob = self._heuristic_score(x)

        level = self._classify(prob)
        return round(prob, 4), level

    @staticmethod
    def _heuristic_score(x: np.ndarray) -> float:
        """
        Fallback heuristic when no model is available.
        Uses raw feature values with hand-tuned weights.
        """
        # Feature order: package_age, maintainer_count, maintainer_age,
        # commits/month, release_freq, version_spike, contributor_growth,
        # popularity, ownership_change, download_trend, cve_count,
        # cve_severity, dep_depth, hist_risk
        v = x.flatten()
        score = 0.0
        # Penalise young packages (< 180 days)
        if v[0] < 180:
            score += 0.15
        # Penalise low maintainer count
        if v[1] <= 1:
            score += 0.10
        # Penalise version spikes
        score += min(v[5] * 0.08, 0.20)
        # Reward high popularity
        score -= v[7] * 0.10
        # Penalise ownership change flag
        score += v[8] * 0.20
        # Penalise CVEs
        score += min(v[10] * 0.03, 0.15)
        score += v[11] * 0.10
        # Penalise historical risk
        score += v[13] * 0.10
        return max(0.0, min(score, 1.0))

    @staticmethod
    def _classify(prob: float) -> str:
        if prob < 0.35:
            return "LOW"
        elif prob < 0.70:
            return "MEDIUM"
        return "HIGH"
