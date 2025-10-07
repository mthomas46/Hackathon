"""DTOs for Package Management."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# --- Request DTOs ---

class CreatePackageRequest(BaseModel):
    """Request to create a new package."""
    name: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    display_name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    author: str = Field(..., min_length=2, max_length=100)
    author_email: Optional[str] = None
    homepage_url: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: str = "MIT"
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    is_public: bool = True
    owner_id: str = "default"


class UploadVersionRequest(BaseModel):
    """Request to upload a new version."""
    package_id: str
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$")
    changelog: str = ""
    release_notes: str = ""
    is_prerelease: bool = False
    dependencies: Dict[str, str] = Field(default_factory=dict)
    min_python_version: Optional[str] = None
    max_python_version: Optional[str] = None


class UpdatePackageRequest(BaseModel):
    """Request to update package metadata."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    homepage_url: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class SearchPackagesRequest(BaseModel):
    """Request to search packages."""
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)


# --- Response DTOs ---

class PackageVersionResponse(BaseModel):
    """Response for a single package version."""
    version: str
    package_id: str
    storage_path: str
    file_size_bytes: int
    checksum: str
    changelog: str
    release_notes: str
    is_prerelease: bool
    is_yanked: bool
    yank_reason: Optional[str]
    created_at: datetime
    published_at: Optional[datetime]
    download_count: int
    dependencies: Dict[str, Any]
    min_python_version: Optional[str]
    max_python_version: Optional[str]


class PackageResponse(BaseModel):
    """Response for a single package."""
    package_id: str
    name: str
    display_name: str
    description: str
    author: str
    author_email: Optional[str]
    homepage_url: Optional[str]
    repository_url: Optional[str]
    documentation_url: Optional[str]
    license: str
    status: str
    latest_version: Optional[str]
    tags: List[str]
    categories: List[str]
    total_downloads: int
    download_count_30d: int
    star_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    owner_id: str
    is_public: bool
    embedding_count: int
    document_count: int
    entity_count: int
    relationship_count: int
    popularity_score: float
    versions: Optional[List[PackageVersionResponse]] = None


class PackageSummaryResponse(BaseModel):
    """Lightweight package summary for lists."""
    package_id: str
    name: str
    display_name: str
    description: str
    author: str
    latest_version: Optional[str]
    total_downloads: int
    star_count: int
    tags: List[str]
    categories: List[str]
    popularity_score: float


class DownloadURLResponse(BaseModel):
    """Response with pre-signed download URL."""
    download_url: str
    expires_at: datetime
    file_size_bytes: int
    checksum: str


class PackageStatsResponse(BaseModel):
    """Statistics for a package."""
    package_id: str
    name: str
    total_downloads: int
    download_count_30d: int
    download_count_7d: int
    download_count_24h: int
    star_count: int
    version_count: int
    latest_version: Optional[str]
