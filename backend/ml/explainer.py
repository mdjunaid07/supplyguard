"""
SHAP Explainer
==============
Generates human-readable risk factor explanations using SHAP values.
Falls back to rule-based explanation if SHAP is unavailable.
"""
import numpy as np
from typing import List, Tuple, Any
from backend.utils.logger import get_logger

logger = get_logger(__name__)

FEATURE_LABELS = {
    "package_age_days": "Package age",
    "maintainer_count": "Maintainer count",
    "maintainer_account_age": "Maintainer account age",
    "commits_per_month": "Commit activity",
    "release_frequency": "Release frequency",
    "version_spike_ratio": "Version release spike",
    "contributor_growth_rate": "Contributor growth rate",
    "repo_popularity_score": "Repository popularity",
    "ownership_change_flag": "Ownership change detected",
    "download_trend_score": "Download trend",
    "cve_count": "Known CVEs",
    "cve_severity_score": "CVE severity score",
    "dependency_depth": "Dependency depth",
    "historical_risk_score": "Historical risk score",
}

FEATURE_NAMES = list(FEATURE_LABELS.keys())


class RiskExplainer:
    def __init__(self, model: Any = None, preprocessor: Any = None):
        self.model = model
        self.preprocessor = preprocessor
        self._explainer = None
        self._init_shap()

    def _init_shap(self):
        if self.model is None:
            return
        try:
            import shap
            model_type = type(self.model).__name__
            if "RandomForest" in model_type or "GradientBoosting" in model_type:
                self._explainer = shap.TreeExplainer(self.model)
            else:
                self._explainer = shap.LinearExplainer(
                    self.model, masker=shap.maskers.Independent(np.zeros((1, 14)))
                )
            logger.info(f"SHAP explainer initialised for {model_type}")
        except Exception as e:
            logger.warning(f"SHAP unavailable: {e}. Using rule-based explanations.")

    def explain(
        self, x_raw: np.ndarray, top_n: int = 5
    ) -> Tuple[List[str], List[Tuple[str, float]]]:
        """
        Returns:
            top_risk_factors: list of human-readable strings
            shap_pairs: list of (feature_name, shap_value) tuples
        """
        if self._explainer is not None:
            return self._shap_explain(x_raw, top_n)
        return self._rule_explain(x_raw, top_n)

    def _shap_explain(
        self, x: np.ndarray, top_n: int
    ) -> Tuple[List[str], List[Tuple[str, float]]]:
        try:
            shap_values = self._explainer.shap_values(x)
            # For classifiers: shap_values may be list [class0, class1]
            vals = shap_values[1] if isinstance(shap_values, list) else shap_values
            vals = np.array(vals).flatten()
            pairs = sorted(
                zip(FEATURE_NAMES, vals), key=lambda x: abs(x[1]), reverse=True
            )[:top_n]
            factors = []
            for name, val in pairs:
                direction = "increases" if val > 0 else "reduces"
                label = FEATURE_LABELS.get(name, name)
                factors.append(f"{label} {direction} risk (SHAP={val:.3f})")
            return factors, [(n, float(v)) for n, v in pairs]
        except Exception as e:
            logger.warning(f"SHAP explain error: {e}")
            return self._rule_explain(x, top_n)

    @staticmethod
    def _rule_explain(
        x: np.ndarray, top_n: int
    ) -> Tuple[List[str], List[Tuple[str, float]]]:
        """Heuristic rule-based explanation using raw feature values."""
        v = x.flatten()
        rules: List[Tuple[str, float]] = []

        checks = [
            ("package_age_days",       v[0] < 90,    0.30, "Very new package (< 90 days old)"),
            ("package_age_days",       v[0] < 365,   0.15, "Package is less than 1 year old"),
            ("maintainer_count",       v[1] <= 1,    0.25, "Single maintainer — high bus-factor risk"),
            ("version_spike_ratio",    v[5] > 2,     0.30, "Sudden surge in release activity"),
            ("ownership_change_flag",  v[8] == 1,    0.40, "Potential ownership change detected"),
            ("cve_count",              v[10] > 0,    min(v[10] * 0.05, 0.30), f"{int(v[10])} known CVE(s) found"),
            ("cve_severity_score",     v[11] > 0.5,  0.25, "High CVE severity score"),
            ("download_trend_score",   v[9] < -0.3,  0.20, "Downloads dropping significantly"),
            ("repo_popularity_score",  v[7] < 0.01,  0.15, "Very low repository popularity"),
            ("commits_per_month",      v[3] < 1,     0.15, "Inactive development (< 1 commit/month)"),
            ("historical_risk_score",  v[13] > 0.5,  v[13] * 0.20, "Elevated historical risk score"),
        ]

        for feat, condition, weight, msg in checks:
            if condition:
                rules.append((msg, weight))

        rules.sort(key=lambda x: x[1], reverse=True)
        top = rules[:top_n]
        factors = [msg for msg, _ in top]
        pairs = [(msg, w) for msg, w in top]
        return factors if factors else ["No significant risk factors identified"], pairs
