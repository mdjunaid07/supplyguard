import httpx
from github import Github, GithubIntegration
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_installation_token(installation_id: int) -> str:
    """Exchange installation ID for a short-lived access token."""
    try:
        with open(settings.github_private_key_path, "r") as f:
            private_key = f.read()
        integration = GithubIntegration(settings.github_app_id, private_key)
        token = integration.get_access_token(installation_id).token
        return token
    except Exception as e:
        logger.warning(f"Could not get installation token: {e}. Falling back to PAT.")
        return settings.github_token


def get_github_client(installation_id: int | None = None) -> Github:
    """Return an authenticated PyGithub client."""
    if installation_id:
        token = get_installation_token(installation_id)
    else:
        token = settings.github_token
    return Github(token)


async def post_pr_comment(
    repo_full_name: str,
    pr_number: int,
    body: str,
    installation_id: int,
) -> str:
    """Post a comment on a Pull Request and return the comment URL."""
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"body": body}, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Posted comment on {repo_full_name}#{pr_number}: {data['html_url']}")
        return data["html_url"]
