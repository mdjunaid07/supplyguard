"""
Webhook Signature Validator
============================
Verifies GitHub HMAC-SHA256 webhook signatures to ensure
requests are genuinely from GitHub.
"""
import hashlib
import hmac
from fastapi import Request, HTTPException
from backend.config import get_settings

settings = get_settings()


async def verify_github_signature(request: Request) -> bytes:
    """
    Read the raw body, verify the X-Hub-Signature-256 header.
    Returns the raw body bytes for downstream parsing.
    Raises HTTP 401 on invalid or missing signature.
    """
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()

    if not settings.github_webhook_secret:
        # Dev mode: skip verification
        return body

    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    expected = hmac.new(
        settings.github_webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    received = signature_header[len("sha256="):]

    if not hmac.compare_digest(expected, received):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    return body
