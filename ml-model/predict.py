"""
SupplyGuard ML Predictor — Standalone CLI
==========================================
Runs the full feature collection + ML prediction for a given package.

Usage:
    python ml-model/predict.py --package lodash
    python ml-model/predict.py --package event-stream --version 3.3.6
"""
import argparse
import asyncio
import sys
import os
import json

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.npm_collector import fetch_npm_metadata
from backend.services.github_collector import fetch_github_metadata
from backend.services.cve_collector import fetch_cve_data
from backend.services.feature_engineer import engineer_features, features_to_vector
from backend.ml.preprocessor import Preprocessor
from backend.ml.predictor import RiskPredictor
from backend.ml.explainer import RiskExplainer
from backend.config import get_settings

settings = get_settings()


async def predict_package(package_name: str, version: str = "latest"):
    print(f"\n🔍 Analysing package: {package_name}@{version}")
    print("─" * 60)

    # Load ML components
    preprocessor = Preprocessor(settings.preprocessor_path)
    predictor = RiskPredictor(settings.model_path)
    explainer = RiskExplainer(model=predictor.model)

    # Collect features
    print("📦 Collecting npm metadata...")
    features, raw_data = await engineer_features(package_name, version)

    fv = features_to_vector(features)
    print("🔢 Feature vector computed")

    # Preprocess
    x_scaled = preprocessor.transform(fv)

    # Predict
    risk_prob, risk_level = predictor.predict(x_scaled)
    top_factors, shap_pairs = explainer.explain(x_scaled)

    # Format output
    emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
    print(f"\n{'='*60}")
    print(f"🔐 SupplyGuard Risk Report")
    print(f"{'='*60}")
    print(f"  Package    : {package_name}")
    print(f"  Version    : {version}")
    print(f"  Risk Score : {risk_prob*100:.1f}%")
    print(f"  Risk Level : {emoji} {risk_level}")
    print(f"\n  ⚠️  Top Risk Factors:")
    for f in top_factors:
        print(f"    • {f}")
    print(f"\n  📊 Key Features:")
    print(f"    Package age    : {features.package_age_days:.0f} days")
    print(f"    Maintainers    : {features.maintainer_count}")
    print(f"    CVE count      : {features.cve_count}")
    print(f"    CVE severity   : {features.cve_severity_score:.2f}")
    print(f"    Version spike  : {features.version_spike_ratio:.2f}x")
    print(f"    Popularity     : {features.repo_popularity_score:.3f}")
    print(f"{'='*60}\n")

    return {
        "package": package_name,
        "version": version,
        "risk_probability": risk_prob,
        "risk_level": risk_level,
        "top_risk_factors": top_factors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SupplyGuard CLI Predictor")
    parser.add_argument("--package", required=True, help="npm package name")
    parser.add_argument("--version", default="latest", help="Package version")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = asyncio.run(predict_package(args.package, args.version))
    if args.json:
        print(json.dumps(result, indent=2))
