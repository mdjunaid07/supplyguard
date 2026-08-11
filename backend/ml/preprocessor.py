"""
ML Preprocessor
================
Loads/saves the fitted StandardScaler + SimpleImputer pipeline.
Handles missing values and feature normalisation.
"""
import numpy as np
import joblib
import os
from typing import List
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Preprocessor:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.pipeline: Pipeline | None = None
        self._load()

    def _load(self):
        if os.path.exists(self.model_path):
            self.pipeline = joblib.load(self.model_path)
            logger.info(f"Preprocessor loaded from {self.model_path}")
        else:
            logger.warning(
                f"Preprocessor not found at {self.model_path}. "
                "Using identity transform until model is trained."
            )

    def transform(self, feature_vector: List[float]) -> np.ndarray:
        """Normalise a single feature vector."""
        x = np.array(feature_vector, dtype=float).reshape(1, -1)
        if self.pipeline is None:
            return x
        return self.pipeline.transform(x)

    @staticmethod
    def build_pipeline() -> Pipeline:
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
