"""
npm Registry Collector
======================
Fetches package metadata from the npm registry API.
"""
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)

NPM_REGISTRY = "https://registry.npmjs.org"
NPM_DOWNLOADS = "https://api.npmjs.org/downloads/point"


async def fetch_npm_metadata(package_name: str) -> Dict[str, Any]:
    """Return enriched metadata dict for a given npm package."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Core registry data
        reg_url = f"{NPM_REGISTRY}/{package_name}"
        try:
            resp = await client.get(reg_url)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"npm registry error for {package_name}: {e}")
            return _empty_npm_meta(package_name)

        # Download stats (last 3 months)
        downloads_last_month = 0
        downloads_prev_month = 0
        try:
            dl_resp = await client.get(f"{NPM_DOWNLOADS}/last-month/{package_name}")
            if dl_resp.status_code == 200:
                downloads_last_month = dl_resp.json().get("downloads", 0)
            dl_prev = await client.get(
                f"{NPM_DOWNLOADS}/2024-01-01:2024-03-31/{package_name}"
            )
            if dl_prev.status_code == 200:
                downloads_prev_month = dl_prev.json().get("downloads", 0)
        except Exception:
            pass

        return _parse_npm_data(data, downloads_last_month, downloads_prev_month)


def _parse_npm_data(
    data: Dict,
    downloads_last_month: int,
    downloads_prev_month: int,
) -> Dict[str, Any]:
    name = data.get("name", "")
    time_data = data.get("time", {})
    versions = list(data.get("versions", {}).keys())

    # Package age
    created_str = time_data.get("created")
    created_dt = _parse_iso(created_str)
    now = datetime.now(timezone.utc)
    package_age_days = (now - created_dt).days if created_dt else 0

    # Version timeline — detect release spikes
    version_timestamps: List[datetime] = []
    for v, ts in time_data.items():
        if v in ("created", "modified"):
            continue
        dt = _parse_iso(ts)
        if dt:
            version_timestamps.append(dt)
    version_timestamps.sort()

    version_spike_ratio = _compute_version_spike(version_timestamps)
    release_frequency = len(version_timestamps) / max(package_age_days / 30, 1)

    # Maintainers
    maintainers: List[Dict] = data.get("maintainers", [])
    maintainer_count = len(maintainers)

    # Download trend score
    download_trend_score = 0.0
    if downloads_prev_month > 0:
        download_trend_score = (downloads_last_month - downloads_prev_month) / max(
            downloads_prev_month, 1
        )

    return {
        "name": name,
        "package_age_days": package_age_days,
        "maintainer_count": maintainer_count,
        "maintainers": [m.get("name", "") for m in maintainers],
        "version_count": len(versions),
        "release_frequency": round(release_frequency, 4),
        "version_spike_ratio": round(version_spike_ratio, 4),
        "downloads_last_month": downloads_last_month,
        "download_trend_score": round(download_trend_score, 4),
        "latest_version": data.get("dist-tags", {}).get("latest", ""),
        "description": data.get("description", ""),
        "homepage": data.get("homepage", ""),
        "license": data.get("license", ""),
    }


def _compute_version_spike(timestamps: List[datetime]) -> float:
    """Ratio of releases in last 30 days vs prior 30–90 days."""
    if len(timestamps) < 2:
        return 0.0
    now = datetime.now(timezone.utc)
    last_30 = sum(1 for t in timestamps if (now - t).days <= 30)
    prev_30_90 = sum(1 for t in timestamps if 30 < (now - t).days <= 90)
    if prev_30_90 == 0:
        return float(last_30)
    return last_30 / prev_30_90


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _empty_npm_meta(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "package_age_days": 0,
        "maintainer_count": 0,
        "maintainers": [],
        "version_count": 0,
        "release_frequency": 0.0,
        "version_spike_ratio": 0.0,
        "downloads_last_month": 0,
        "download_trend_score": 0.0,
        "latest_version": "",
        "description": "",
        "homepage": "",
        "license": "",
    }
