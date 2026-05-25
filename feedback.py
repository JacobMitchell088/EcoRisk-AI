import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from limiter import limiter
from scan import verify_turnstile

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

# Personal Access Token (fine-grained, "Issues: Read and write" on the target
# repo only). Held server-side ONLY — never expose this to the frontend.
GITHUB_FEEDBACK_PAT = os.getenv("GITHUB_FEEDBACK_PAT", "")
# Target repository in "owner/repo" form, e.g. "jacobmitchell088/EcoRisk-AI"
GITHUB_FEEDBACK_REPO = os.getenv("GITHUB_FEEDBACK_REPO", "")


class FeedbackRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=120, description="Feedback title / header")
    body: str = Field(..., min_length=5, max_length=5000, description="What's good, bad, or wanted")
    contact_email: Optional[str] = Field(
        None, max_length=254, description="Optional email for a reply"
    )
    rating: Optional[int] = Field(None, ge=1, le=5, description="Optional 1–5 star rating")
    captcha_token: str = Field(
        ..., min_length=1, max_length=2048, description="Cloudflare Turnstile token"
    )


def build_issue_body(req: FeedbackRequest) -> str:
    """Assemble a Markdown issue body from the submitted feedback."""
    lines: list[str] = []

    if req.rating is not None:
        stars = "★" * req.rating + "☆" * (5 - req.rating)
        lines.append(f"**Rating:** {stars} ({req.rating}/5)")
        lines.append("")

    lines.append(req.body.strip())
    lines.append("")
    lines.append("---")

    if req.contact_email:
        lines.append(f"**Contact:** {req.contact_email.strip()}")
    else:
        lines.append("_No contact email provided._")

    lines.append("")
    lines.append("_Submitted via the in-app Provide Feedback widget._")

    return "\n".join(lines)


@router.post("/feedback")
@limiter.limit("5/hour")
async def submit_feedback(request: Request, req: FeedbackRequest):
    if not GITHUB_FEEDBACK_PAT or not GITHUB_FEEDBACK_REPO:
        logger.error("Feedback endpoint not configured: missing GITHUB_FEEDBACK_PAT or GITHUB_FEEDBACK_REPO")
        raise HTTPException(status_code=500, detail="Feedback is not configured on the server.")

    is_human = await verify_turnstile(
        req.captcha_token,
        request.client.host if request.client else None,
    )
    if not is_human:
        raise HTTPException(status_code=400, detail="Human verification failed")

    payload = {
        "title": req.title.strip(),
        "body": build_issue_body(req),
        "labels": ["feedback"],
    }

    url = f"https://api.github.com/repos/{GITHUB_FEEDBACK_REPO}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_FEEDBACK_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            issue = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("GitHub issue creation failed: HTTP %s", exc.response.status_code)
        raise HTTPException(status_code=502, detail="Could not submit feedback to GitHub. Please try again later.")
    except httpx.RequestError as exc:
        logger.error("GitHub issue creation request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach GitHub. Please try again later.")

    logger.info("Feedback issue created: #%s", issue.get("number"))
    return {"ok": True, "issue_number": issue.get("number"), "issue_url": issue.get("html_url")}
