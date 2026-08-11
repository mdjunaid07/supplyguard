"""
GitHub Repository Collector
============================
Fetches stars, forks, contributors, commit velocity, and repo age
from the GitHub REST API for a given npm package (via repository URL).
"""
import httpx
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

GH_API = "https://api.github.com"


def _extract_github_repo(npm_meta: Dict[str, Any]) -> Optional[str]:
    """Try to pull a 'owner/repo' string from npm metadata homepage/repository."""
    candidates = [
        npm_meta.get("homepage", ""),
        str(npm_meta.get("repository", {}).get("url", "") if isinstance(npm_meta.get("repository"), dict) else ""),
    ]
    for c in candidates:
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", c or "")
        if m:
            return m.group(1).rstrip(".git")
    return None


async def fetch_github_metadata(
    package_name: str,
    npm_meta: Dict[str, Any],
) -> Dict[str, Any]:
    repo_slug = _extract_github_repo(npm_meta)
    if not repo_slug:
        logger.info(f"No GitHub repo found for {package_name}")
        return _empty_github_meta()

    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        # Repo metadata
        try:
            r = await client.get(f"{GH_API}/repos/{repo_slug}")
            if r.status_code != 200:
                return _empty_github_meta()
            repo = r.json()
        except Exception as e:
            logger.warning(f"GitHub API error for {repo_slug}: {e}")
            return _empty_github_meta()

        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        open_issues = repo.get("open_issues_count", 0)

        created_at = datetime.fromisoformat(
            repo.get("created_at", "2020-01-01T00:00:00Z").replace("Z", "+00:00")
        )
        repo_age_days = (datetime.now(timezone.utc) - created_at).days

        # Contributors count (first page only — max 30)
        contributor_count = 0
        try:
            cr = await client.get(
                f"{GH_API}/repos/{repo_slug}/contributors",
                params={"per_page": 30, "anon": "false"},
            )
            if cr.status_code == 200:
                contributor_count = len(cr.json())
        except Exception:
            pass

        # Commit activity (last 52 weeks)
        commits_per_month = 0.0
        contributor_growth_rate = 0.0
        try:
            ca = await client.get(f"{GH_API}/repos/{repo_slug}/stats/commit_activity")
            if ca.status_code == 200:
                weeks = ca.json()  # list of 52 weekly objects
                total = sum(w.get("total", 0) for w in weeks)
                commits_per_month = total / 12.0
                # Growth: compare last 4 weeks vs prior 4 weeks
                if len(weeks) >= 8:
                    recent = sum(w.get("total", 0) for w in weeks[-4:])
                    prior = sum(w.get("total", 0) for w in weeks[-8:-4])
                    if prior > 0:
                        contributor_growth_rate = (recent - prior) / prior
        except Exception:
            pass

        repo_popularity_score = _popularity(stars, forks, watchers, open_issues)

        return {
            "repo_slug": repo_slug,
            "stars": stars,
            "forks": forks,
            "watchers": watchers,
            "open_issues": open_issues,
            "repo_age_days": repo_age_days,
            "contributor_count": contributor_count,
            "commits_per_month": round(commits_per_month, 2),
            "contributor_growth_rate": round(contributor_growth_rate, 4),
            "repo_popularity_score": round(repo_popularity_score, 4),
        }


def _popularity(stars: int, forks: int, watchers: int, issues: int) -> float:
    """Normalised popularity score in [0, 1]."""
    raw = stars * 0.5 + forks * 0.3 + watchers * 0.1 + max(0, 1000 - issues) * 0.1
    return min(raw / 10000.0, 1.0)


def _empty_github_meta() -> Dict[str, Any]:
    return {
        "repo_slug": "",
        "stars": 0,
        "forks": 0,
        "watchers": 0,
        "open_issues": 0,
        "repo_age_days": 0,
        "contributor_count": 0,
        "commits_per_month": 0.0,
        "contributor_growth_rate": 0.0,
        "repo_popularity_score": 0.0,
    }
