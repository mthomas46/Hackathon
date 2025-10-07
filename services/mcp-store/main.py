"""
MCP Store Service - Main FastAPI Application

'Docker for Knowledge Graphs' - Package, version, and distribute MCP contexts.
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.mcp_store.domain.value_objects.package_status import PackageStatus
from services.mcp_store.domain.services.compression_service import CompressionService
from services.mcp_store.application.use_cases.package_management import PackageManagementUseCase
from services.mcp_store.application.dto.package_dto import (
    CreatePackageRequest,
    UpdatePackageRequest,
    UploadPackageVersionRequest,
    UpdatePackageVersionRequest,
    MCPPackageResponse,
    MCPVersionResponse,
)
from services.mcp_store.infrastructure.config import get_settings
from services.mcp_store.infrastructure.database import init_database, get_database
from services.mcp_store.infrastructure.repositories import (
    SqlitePackageRepository,
    MinioStorageRepository,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app."""
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Initialize database
    db = init_database(settings)
    await db.create_tables()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Store service")
    await db.close()


# Create FastAPI app
app = FastAPI(
    title="MCP Store",
    description="'Docker for Knowledge Graphs' - Package, version, and distribute MCP contexts",
    version=settings.service_version,
    lifespan=lifespan,
)


# Dependency injection
def get_package_management_use_case() -> PackageManagementUseCase:
    """Get PackageManagementUseCase with dependencies."""
    db = get_database()
    
    # Create repositories
    async def get_session():
        async with db.session() as session:
            return session
    
    # For simplicity, create sync versions - in production, use proper async DI
    storage_repo = MinioStorageRepository(
        endpoint=settings.storage_endpoint,
        access_key=settings.storage_access_key or "minioadmin",
        secret_key=settings.storage_secret_key or "minioadmin",
        bucket=settings.storage_bucket,
        use_ssl=settings.storage_use_ssl,
    )
    
    compression_service = CompressionService(compression_level=3)
    
    # Note: This is a simplified approach. In production, use proper async session management
    # We'll need to refactor this to properly handle async sessions
    return PackageManagementUseCase(
        package_repo=None,  # Will be injected per request
        storage_repo=storage_repo,
        compression_service=compression_service,
    )


# ============================================================================
# Package Endpoints
# ============================================================================

@app.post("/packages", response_model=MCPPackageResponse, status_code=201)
async def create_package(request: CreatePackageRequest):
    """
    Create a new MCP package.
    
    This initializes package metadata without any versions.
    """
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            package = await use_case.create_package(request)
            return package
    except Exception as e:
        logger.error(f"Failed to create package: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/packages/{package_id}", response_model=MCPPackageResponse)
async def get_package(package_id: str):
    """Get package details by ID."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            package = await use_case.get_package(package_id)
            if not package:
                raise HTTPException(status_code=404, detail=f"Package {package_id} not found")
            return package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/packages/{package_id}", response_model=MCPPackageResponse)
async def update_package(package_id: str, request: UpdatePackageRequest):
    """Update package metadata."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            package = await use_case.update_package(package_id, request)
            return package
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/packages/{package_id}", status_code=204)
async def delete_package(package_id: str):
    """Delete a package and all its versions."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            await use_case.delete_package(package_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete package: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/packages", response_model=List[MCPPackageResponse])
async def list_packages(
    owner_id: Optional[str] = Query(None),
    status: Optional[PackageStatus] = Query(None),
    is_public: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    categories: Optional[str] = Query(None),  # Comma-separated
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List and search packages.
    
    Supports filtering by owner, status, visibility, tags, and categories.
    Supports full-text search across name and description.
    """
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            # Parse tags and categories
            tag_list = tags.split(",") if tags else None
            category_list = categories.split(",") if categories else None
            
            packages = await use_case.list_packages(
                owner_id=owner_id,
                status=status,
                is_public=is_public,
                search_query=search,
                tags=tag_list,
                categories=category_list,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )
            return packages
    except Exception as e:
        logger.error(f"Failed to list packages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Version Endpoints
# ============================================================================

@app.post("/packages/{package_id}/versions", response_model=MCPVersionResponse, status_code=201)
async def upload_version(
    package_id: str,
    version_string: str = Query(..., description="Semantic version (e.g., 1.0.0)"),
    release_notes: Optional[str] = Query(None),
    file: UploadFile = File(..., description=".mcp package file"),
):
    """
    Upload a new version of a package.
    
    The file will be compressed, checksummed, and stored in MinIO/S3.
    """
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            # Read file content
            file_content = await file.read()
            
            # Create async iterator from bytes
            async def file_stream():
                yield file_content
            
            version = await use_case.upload_package_version(
                package_id=package_id,
                version_string=version_string,
                file_stream=file_stream(),
                content_type=file.content_type or "application/octet-stream",
                release_notes=release_notes,
            )
            return version
    except Exception as e:
        logger.error(f"Failed to upload version: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/packages/{package_id}/versions/{version_id}", response_model=MCPVersionResponse)
async def get_version(package_id: str, version_id: str):
    """Get version details."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            version = await use_case.get_package_version(version_id)
            if not version:
                raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
            return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/packages/{package_id}/versions")
async def list_versions(
    package_id: str,
    is_active: Optional[bool] = Query(True),
) -> List[MCPVersionResponse]:
    """List all versions for a package."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            versions = await use_case.list_package_versions(package_id, is_active)
            return versions
    except Exception as e:
        logger.error(f"Failed to list versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/packages/{package_id}/versions/{version_id}/download")
async def download_version(package_id: str, version_id: str):
    """
    Download a package version.
    
    Returns the .mcp file as a streaming response.
    """
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            # Get version metadata
            version = await use_case.get_package_version(version_id)
            if not version:
                raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
            
            # Download file stream
            file_stream = await use_case.download_package_version(version_id)
            
            # Return as streaming response
            return StreamingResponse(
                file_stream,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={package_id}-{version.version_string}.mcp",
                    "X-Checksum": version.checksum,
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/packages/{package_id}/versions/{version_id}", response_model=MCPVersionResponse)
async def update_version(
    package_id: str,
    version_id: str,
    request: UpdatePackageVersionRequest
):
    """Update version metadata (e.g., release notes, active status)."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            version = await use_case.update_package_version(version_id, request)
            return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/packages/{package_id}/versions/{version_id}", status_code=204)
async def delete_version(package_id: str, version_id: str):
    """Delete a specific version."""
    try:
        db = get_database()
        async with db.session() as session:
            package_repo = SqlitePackageRepository(session)
            storage_repo = MinioStorageRepository(
                endpoint=settings.storage_endpoint,
                access_key=settings.storage_access_key or "minioadmin",
                secret_key=settings.storage_secret_key or "minioadmin",
                bucket=settings.storage_bucket,
                use_ssl=settings.storage_use_ssl,
            )
            compression_service = CompressionService()
            
            use_case = PackageManagementUseCase(
                package_repo=package_repo,
                storage_repo=storage_repo,
                compression_service=compression_service,
            )
            
            await use_case.delete_package_version(version_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MCP Store",
        "version": settings.service_version,
        "description": "'Docker for Knowledge Graphs' - Package, version, and distribute MCP contexts",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
        log_level="info"
    )
