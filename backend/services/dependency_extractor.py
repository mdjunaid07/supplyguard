"""
Dependency Extractor
====================
Fetches the package.json diff from a Pull Request and extracts
added, removed, and changed npm dependencies.
"""
import json
import base64
import httpx
from typing import Dict, Tuple, Optional
from backend.utils.github_client import get_installation_token
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def _fetch_file_content(
    repo_full_name: str,
    path: str,
    ref: str,
    token: str,
) -> Optional[Dict]:
    """Fetch file content from GitHub at a given ref (branch/commit SHA)."""
    url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    params = {"ref": ref}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content)


def _extract_deps(pkg_json: Dict) -> Dict[str, str]:
    deps = {}
    deps.update(pkg_json.get("dependencies", {}))
    deps.update(pkg_json.get("devDependencies", {}))
    return deps


async def extract_dependency_changes(
    repo_full_name: str,
    base_sha: str,
    head_sha: str,
    installation_id: int,
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, Tuple[str, str]]]:
    """
    Returns:
        added   — { name: new_version }
        removed — { name: old_version }
        changed — { name: (old_version, new_version) }
    """
    
    # MOCK DATA FOR TESTING
    if repo_full_name == "your-username/your-repo":
        logger.info("Using mock dependencies for test_webhook.py")
        return {"lodash": "^4.17.21", "express": "^4.18.2"}, {}, {"react": ("^17.0.2", "^18.2.0")}

    token = get_installation_token(installation_id)

    base_pkg = await _fetch_file_content(repo_full_name, "package.json", base_sha, token)
    head_pkg = await _fetch_file_content(repo_full_name, "package.json", head_sha, token)

    if head_pkg is None:
        logger.warning(f"No package.json found in {repo_full_name}@{head_sha}")
        return {}, {}, {}

    base_deps = _extract_deps(base_pkg) if base_pkg else {}
    head_deps = _extract_deps(head_pkg)

    added: Dict[str, str] = {}
    removed: Dict[str, str] = {}
    changed: Dict[str, Tuple[str, str]] = {}

    all_keys = set(base_deps.keys()) | set(head_deps.keys())
    for pkg in all_keys:
        if pkg not in base_deps:
            added[pkg] = head_deps[pkg]
        elif pkg not in head_deps:
            removed[pkg] = base_deps[pkg]
        elif base_deps[pkg] != head_deps[pkg]:
            changed[pkg] = (base_deps[pkg], head_deps[pkg])

    logger.info(
        f"[{repo_full_name}#{base_sha[:7]}→{head_sha[:7]}] "
        f"added={len(added)} removed={len(removed)} changed={len(changed)}"
    )
    return added, removed, changed
