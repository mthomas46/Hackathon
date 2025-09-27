"""GitHub Issues API routes with OpenAPI documentation."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class IssueInfo(BaseModel):
    """Issue information model."""
    number: int
    title: str
    author: str
    state: str
    labels: List[str]
    created_at: str
    updated_at: str


@router.get(
    "/{owner}/{repo}",
    response_model=List[IssueInfo],
    summary="List Issues",
    description="List issues for a repository."
)
async def list_issues(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    state: str = Query("open", description="Issue state"),
    labels: Optional[str] = Query(None, description="Filter by labels")
) -> List[IssueInfo]:
    """List issues."""
    return [
        IssueInfo(
            number=i,
            title=f"Issue {i}: Bug report",
            author="user",
            state=state,
            labels=["bug", "high-priority"] if labels else ["bug"],
            created_at="2023-01-01T00:00:00Z",
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        for i in range(1, 4)
    ]
