"""
Feature Engineer
================
Combines raw npm / GitHub / CVE data into the standardised
14-feature vector used by the ML model.
"""
import asyncio
from typing import Dict, Any, List, Tuple

from backend.services.npm_collector import fetch_npm_metadata
from backend.services.github_collector import fetch_github_metadata
from backend.services.cve_collector import fetch_cve_data
from backend.db.models import PackageFeatures
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def engineer_features(
    package_name: str,
    version: str,
    dependency_depth: int = 0,
    historical_risk_score: float = 0.0,
) -> Tuple[PackageFeatures, Dict[str, Any]]:
    """
    Collect all raw data and produce:
    - PackageFeatures (clean feature vector)
    - raw_data dict (for storage / report)
    """
    # Parallel data collection
    npm_meta, cve_data = await asyncio.gather(
        fetch_npm_metadata(package_name),
        fetch_cve_data(package_name),
    )
    gh_meta = await fetch_github_metadata(package_name, npm_meta)

    # Maintainer account age — approximate from npm registration
    # (npm doesn't expose account age directly; we use package_age as proxy)
    maintainer_account_age = npm_meta.get("package_age_days", 0) / 365.0

    # Ownership change flag: heuristic — if version_spike_ratio > 2 AND
    # maintainer_count changed recently (we don't have history, so check spike)
    ownership_change_flag = int(npm_meta.get("version_spike_ratio", 0) > 2.5)

    features = PackageFeatures(
        package_name=package_name,
        version=version,
        # npm-derived
        package_age_days=float(npm_meta.get("package_age_days", 0)),
        maintainer_count=int(npm_meta.get("maintainer_count", 0)),
        maintainer_account_age=float(maintainer_account_age),
        release_frequency=float(npm_meta.get("release_frequency", 0)),
        version_spike_ratio=float(npm_meta.get("version_spike_ratio", 0)),
        download_trend_score=float(npm_meta.get("download_trend_score", 0)),
        # GitHub-derived
        commits_per_month=float(gh_meta.get("commits_per_month", 0)),
        contributor_growth_rate=float(gh_meta.get("contributor_growth_rate", 0)),
        repo_popularity_score=float(gh_meta.get("repo_popularity_score", 0)),
        ownership_change_flag=int(ownership_change_flag),
        # CVE-derived
        cve_count=int(cve_data.get("cve_count", 0)),
        cve_severity_score=float(cve_data.get("cve_severity_score", 0)),
        # Context
        dependency_depth=int(dependency_depth),
        historical_risk_score=float(historical_risk_score),
    )

    raw_data = {
        "npm": npm_meta,
        "github": gh_meta,
        "cve": cve_data,
    }

    logger.info(f"Features engineered for {package_name}@{version}")
    return features, raw_data


def features_to_vector(features: PackageFeatures) -> List[float]:
    """Convert PackageFeatures to ordered float list for ML model input."""
    return [
        features.package_age_days,
        features.maintainer_count,
        features.maintainer_account_age,
        features.commits_per_month,
        features.release_frequency,
        features.version_spike_ratio,
        features.contributor_growth_rate,
        features.repo_popularity_score,
        features.ownership_change_flag,
        features.download_trend_score,
        features.cve_count,
        features.cve_severity_score,
        features.dependency_depth,
        features.historical_risk_score,
    ]


FEATURE_NAMES = [
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
