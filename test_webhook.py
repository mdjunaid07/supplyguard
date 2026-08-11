import httpx
import json
import hmac
import hashlib

# Match the GITHUB_WEBHOOK_SECRET from your .env
WEBHOOK_SECRET = "mysecretkey2006"

# We use a real but random public repo and commits if possible,
# or just fake ones to see the webhook trigger and DB save.
# For extraction to actually find changes, we'd need a real repo's SHAs.
# Let's just use what's in the README for the basic connectivity test.
payload = {
    "action": "opened",
    "number": 42,
    "pull_request": {
        "number": 42,
        "base": {"sha": "abc123def456abc123def456abc123def456abc1"},
        "head": {"sha": "def456abc123def456abc123def456abc123def4"},
    },
    "repository": {
        "full_name": "mdjunaid07/Movie_Database"
    },
    "installation": {"id": 12345678}
}

body = json.dumps(payload).encode()
sig = "sha256=" + hmac.new(
    WEBHOOK_SECRET.encode(), body, hashlib.sha256
).hexdigest()

try:
    response = httpx.post(
        "http://localhost:8000/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
        timeout=10.0
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
