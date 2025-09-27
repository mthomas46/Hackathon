"""GitHub Pull Requests API routes with OpenAPI documentation."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class PullRequestInfo(BaseModel):
    """Pull request information model."""
    number: int
    title: str
    author: str
    state: str
    created_at: str
    updated_at: str
    merged: bool


@router.get(
    "/{owner}/{repo}",
    response_model=List[PullRequestInfo],
    summary="List Pull Requests",
    description="List pull requests for a repository."
)
async def list_pull_requests(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    state: str = Query("open", description="PR state")
) -> List[PullRequestInfo]:
    """List pull requests."""
    return [
        PullRequestInfo(
            number=i,
            title=f"PR {i}: Feature implementation",
            author="contributor",
            state=state,
            created_at="2023-01-01T00:00:00Z",
            updated_at=datetime.now(timezone.utc).isoformat(),
            merged=state == "closed"
        )
        for i in range(1, 4)
    ]
