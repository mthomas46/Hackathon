"""GitHub Repositories API routes with OpenAPI documentation."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class RepositoryInfo(BaseModel):
    """Repository information model."""
    name: str
    owner: str
    description: Optional[str]
    private: bool
    language: Optional[str]
    stars: int
    forks: int
    issues: int
    created_at: str
    updated_at: str


@router.get(
    "/{owner}/{repo}",
    response_model=RepositoryInfo,
    summary="Get Repository Information",
    description="Retrieve detailed information about a GitHub repository."
)
async def get_repository(
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name")
) -> RepositoryInfo:
    """Get repository information."""
    # Mock data
    return RepositoryInfo(
        name=repo,
        owner=owner,
        description=f"Repository {repo} owned by {owner}",
        private=False,
        language="Python",
        stars=42,
        forks=12,
        issues=7,
        created_at="2023-01-01T00:00:00Z",
        updated_at=datetime.now(timezone.utc).isoformat()
    )


@router.get(
    "/",
    response_model=List[RepositoryInfo],
    summary="List Repositories",
    description="List repositories with optional filtering."
)
async def list_repositories(
    owner: Optional[str] = Query(None, description="Filter by owner"),
    language: Optional[str] = Query(None, description="Filter by language"),
    sort: str = Query("stars", description="Sort field"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
) -> List[RepositoryInfo]:
    """List repositories."""
    # Mock data
    return [
        RepositoryInfo(
            name=f"repo-{i}",
            owner=owner or "sample-owner",
            description=f"Sample repository {i}",
            private=False,
            language=language or "Python",
            stars=100 - i,
            forks=20 - i,
            issues=5 - i,
            created_at="2023-01-01T00:00:00Z",
            updated_at=datetime.now(timezone.utc).isoformat()
        )
        for i in range(min(limit, 5))
    ]
