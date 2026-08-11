"""
CVE / Vulnerability Collector
==============================
Queries the NIST National Vulnerability Database (NVD) API v2
to find known CVEs for a given npm package.
"""
import httpx
from datetime import datetime
from typing import Dict, Any, List
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

SEVERITY_WEIGHTS = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
    "NONE": 0.0,
}


async def fetch_cve_data(package_name: str) -> Dict[str, Any]:
    """Return CVE count and weighted severity score for a package."""
    params: Dict[str, Any] = {
        "keywordSearch": package_name,
        "resultsPerPage": 20,
    }
    headers = {}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(NVD_API, params=params, headers=headers)
            if resp.status_code == 403:
                logger.warning("NVD API rate-limited (no API key). Using fallback.")
                return _empty_cve()
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning(f"CVE fetch error for {package_name}: {e}")
        return _empty_cve()

    vulnerabilities: List[Dict] = data.get("vulnerabilities", [])
    cve_count = len(vulnerabilities)
    severity_score = _compute_severity_score(vulnerabilities)

    recent_cves = _recent_cves(vulnerabilities, days=365)

    return {
        "cve_count": cve_count,
        "cve_severity_score": round(severity_score, 4),
        "recent_cve_count": recent_cves,
        "cve_ids": [
            v.get("cve", {}).get("id", "") for v in vulnerabilities[:5]
        ],
    }


def _compute_severity_score(vulnerabilities: List[Dict]) -> float:
    """Weighted average severity across all CVEs."""
    if not vulnerabilities:
        return 0.0
    scores = []
    for v in vulnerabilities:
        cve = v.get("cve", {})
        metrics = cve.get("metrics", {})
        # Try CVSSv3 first, then v2
        severity = "NONE"
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            entries = metrics.get(key, [])
            if entries:
                severity = (
                    entries[0]
                    .get("cvssData", {})
                    .get("baseSeverity", "NONE")
                    .upper()
                )
                break
        scores.append(SEVERITY_WEIGHTS.get(severity, 0.0))
    return sum(scores) / len(scores)


def _recent_cves(vulnerabilities: List[Dict], days: int = 365) -> int:
    now = datetime.utcnow()
    count = 0
    for v in vulnerabilities:
        published = v.get("cve", {}).get("published", "")
        try:
            dt = datetime.fromisoformat(published.replace("Z", ""))
            if (now - dt).days <= days:
                count += 1
        except Exception:
            pass
    return count


def _empty_cve() -> Dict[str, Any]:
    return {
        "cve_count": 0,
        "cve_severity_score": 0.0,
        "recent_cve_count": 0,
        "cve_ids": [],
    }
