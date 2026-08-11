"""
SupplyGuard ML Training Pipeline
=================================
Trains Logistic Regression, Random Forest, and Gradient Boosting models
on supply-chain risk features, evaluates them, and saves the best model.

Usage:
    python ml-model/train.py
    python ml-model/train.py --data path/to/data.csv --output ml-model/models/
"""
import argparse
import os
import sys
import joblib
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    confusion_matrix,
    f1_score,
)

FEATURE_COLS = [
    "package_age_days",
    "maintainer_count",
    "maintainer_account_age",
    "commits_per_month",
    "release_frequency",
    "version_spike_ratio",
    "contributor_growth_rate",
    "repo_popularity_score",
    "ownership_change_flag",
    "download_trend_score",
    "cve_count",
    "cve_severity_score",
    "dependency_depth",
    "historical_risk_score",
]
TARGET_COL = "is_malicious"


def load_data(csv_path: str) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(csv_path)
    # Clean any stray non-numeric values
    for col in FEATURE_COLS + [TARGET_COL]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=[TARGET_COL])
    X = df[FEATURE_COLS]
    y = df[TARGET_COL].astype(int)
    print(f"✅ Loaded {len(df)} samples | Malicious: {y.sum()} | Benign: {(y==0).sum()}")
    return X, y


def build_pipeline(clf) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", clf),
    ])


def evaluate(model: Pipeline, X_test, y_test, name: str) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\n{'='*50}")
    print(f"📊 {name}")
    print(f"{'='*50}")
    print(f"  AUC-ROC : {auc:.4f}")
    print(f"  F1 Score: {f1:.4f}")
    print(f"  Confusion Matrix:\n    {cm}")
    print(classification_report(y_test, y_pred, target_names=["Benign", "Malicious"]))

    return {"name": name, "auc": auc, "f1": f1, "model": model}


def train(data_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    X, y = load_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(
            C=1.0, class_weight="balanced", max_iter=1000, random_state=42
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        ),
    }

    results = []
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, clf in models.items():
        print(f"\n🔧 Training {name}...")
        pipeline = build_pipeline(clf)

        # Cross-validation
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv,
                                    scoring="roc_auc", n_jobs=-1)
        print(f"  CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        pipeline.fit(X_train, y_train)
        result = evaluate(pipeline, X_test, y_test, name)
        results.append(result)

    # Pick best model by AUC
    best = max(results, key=lambda r: r["auc"])
    print(f"\n🏆 Best model: {best['name']} (AUC={best['auc']:.4f})")

    # Save best model
    model_path = os.path.join(output_dir, "model.pkl")
    joblib.dump(best["model"], model_path)
    print(f"✅ Best model saved → {model_path}")

    # Save standalone preprocessor (imputer + scaler only, for backend use)
    preproc_path = os.path.join(output_dir, "preprocessor.pkl")
    preproc_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preproc_pipeline.fit(X_train)
    joblib.dump(preproc_pipeline, preproc_path)
    print(f"✅ Preprocessor saved → {preproc_path}")

    # Save feature importance (Random Forest / GB)
    try:
        clf = best["model"].named_steps["classifier"]
        if hasattr(clf, "feature_importances_"):
            importances = pd.Series(
                clf.feature_importances_, index=FEATURE_COLS
            ).sort_values(ascending=False)
            print("\n📌 Feature Importances:")
            print(importances.to_string())
            importances.to_csv(os.path.join(output_dir, "feature_importances.csv"))
    except Exception:
        pass

    return model_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SupplyGuard ML Trainer")
    parser.add_argument(
        "--data",
        default=os.path.join(os.path.dirname(__file__), "data", "sample_dataset.csv"),
        help="Path to training CSV",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "models"),
        help="Directory to save trained models",
    )
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"❌ Data file not found: {args.data}")
        sys.exit(1)

    train(args.data, args.output)
