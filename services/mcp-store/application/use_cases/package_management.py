"""Package Management Use Case - Application Layer."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.repositories.package_repository import (
    PackageRepository,
    EntityNotFoundError,
    DuplicateEntityError,
)
from services.mcp_store.domain.repositories.storage_repository import StorageRepository
from services.mcp_store.domain.services.compression_service import CompressionService
from services.mcp_store.domain.value_objects.package_status import PackageStatus
from services.mcp_store.application.dto.package_dto import (
    CreatePackageRequest,
    UploadVersionRequest,
    UpdatePackageRequest,
    SearchPackagesRequest,
    PackageResponse,
    PackageSummaryResponse,
    DownloadURLResponse,
    PackageStatsResponse,
)

logger = logging.getLogger(__name__)


class PackageManagementUseCase:
    """
    Use case for managing MCP packages.
    
    Handles creating, uploading, downloading, and updating packages.
    """
    
    def __init__(
        self,
        package_repo: PackageRepository,
        storage_repo: StorageRepository,
        compression_service: CompressionService,
        max_package_size_mb: int = 500,
    ):
        self.package_repo = package_repo
        self.storage_repo = storage_repo
        self.compression_service = compression_service
        self.max_package_size_bytes = max_package_size_mb * 1024 * 1024
        logger.info(f"Package management use case initialized (max_size={max_package_size_mb}MB)")
    
    async def create_package(self, request: CreatePackageRequest) -> PackageResponse:
        """
        Create a new MCP package.
        
        Args:
            request: Package creation request
            
        Returns:
            Created package
            
        Raises:
            DuplicateEntityError: If package name already exists
        """
        logger.info(f"Creating package: {request.name}")
        
        # Check if package name is already taken
        existing = await self.package_repo.get_by_name(request.name)
        if existing:
            raise DuplicateEntityError(f"Package with name '{request.name}' already exists")
        
        # Create package entity
        package = MCPPackage(
            package_id=str(uuid.uuid4()),
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            author=request.author,
            author_email=request.author_email,
            homepage_url=request.homepage_url,
            repository_url=request.repository_url,
            documentation_url=request.documentation_url,
            license=request.license,
            status=PackageStatus.DRAFT,
            tags=request.tags,
            categories=request.categories,
            is_public=request.is_public,
            owner_id=request.owner_id,
        )
        
        # Save to repository
        await self.package_repo.save(package)
        
        logger.info(f"Package created: {package.package_id}")
        return self._to_package_response(package)
    
    async def upload_version(
        self,
        request: UploadVersionRequest,
        file_content: bytes,
    ) -> PackageResponse:
        """
        Upload a new version of a package.
        
        Args:
            request: Version upload request
            file_content: Raw bytes of the .mcp file
            
        Returns:
            Updated package with new version
            
        Raises:
            EntityNotFoundError: If package doesn't exist
            ValueError: If version already exists or file is too large
        """
        logger.info(f"Uploading version {request.version} for package {request.package_id}")
        
        # Validate file size
        if len(file_content) > self.max_package_size_bytes:
            raise ValueError(
                f"Package file too large: {len(file_content)} bytes "
                f"(max: {self.max_package_size_bytes} bytes)"
            )
        
        # Get package
        package = await self.package_repo.get_by_id(request.package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {request.package_id}")
        
        # Check if version already exists
        if package.get_version(request.version):
            raise ValueError(f"Version {request.version} already exists")
        
        # Compress file
        compressed_content = self.compression_service.compress(file_content)
        
        # Upload to storage
        storage_path = f"{package.name}/{request.version}/package.mcp.zst"
        await self.storage_repo.upload(
            file_path=storage_path,
            file_content=compressed_content,
            content_type="application/octet-stream"
        )
        
        # Create version entity
        version = MCPVersion(
            version=request.version,
            package_id=request.package_id,
            storage_path=storage_path,
            file_size_bytes=len(compressed_content),
            checksum=version.calculate_checksum(file_content),
            changelog=request.changelog,
            release_notes=request.release_notes,
            is_prerelease=request.is_prerelease,
            dependencies=request.dependencies,
            min_python_version=request.min_python_version,
            max_python_version=request.max_python_version,
            published_at=datetime.now(),
        )
        
        # Add version to package
        package.add_version(version)
        
        # Update package
        await self.package_repo.update(package)
        
        logger.info(
            f"Version uploaded: {version.version} "
            f"(size: {len(file_content):,} → {len(compressed_content):,} bytes)"
        )
        
        return self._to_package_response(package, include_versions=True)
    
    async def download_version(
        self,
        package_id: str,
        version: Optional[str] = None,
    ) -> bytes:
        """
        Download a package version.
        
        Args:
            package_id: Package ID
            version: Version string (defaults to latest)
            
        Returns:
            Decompressed .mcp file content
            
        Raises:
            EntityNotFoundError: If package or version not found
        """
        logger.info(f"Downloading package {package_id} version {version or 'latest'}")
        
        # Get package
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        # Get version
        if version:
            pkg_version = package.get_version(version)
        else:
            pkg_version = package.get_latest_version()
        
        if not pkg_version:
            raise EntityNotFoundError(f"Version not found: {version or 'latest'}")
        
        if pkg_version.is_yanked:
            raise ValueError(f"Version {pkg_version.version} has been yanked: {pkg_version.yank_reason}")
        
        # Download from storage
        compressed_content = await self.storage_repo.download(pkg_version.storage_path)
        
        # Decompress
        decompressed_content = self.compression_service.decompress(
            compressed_content,
            max_output_size=self.max_package_size_bytes * 2  # Allow for compression expansion
        )
        
        # Verify checksum
        if not pkg_version.verify_checksum(decompressed_content):
            raise ValueError("Checksum mismatch - file may be corrupted")
        
        # Update download stats
        package.increment_downloads(version=pkg_version.version)
        await self.package_repo.update(package)
        
        logger.info(f"Downloaded: {len(decompressed_content):,} bytes")
        
        return decompressed_content
    
    async def get_download_url(
        self,
        package_id: str,
        version: Optional[str] = None,
        expiration_seconds: int = 3600,
    ) -> DownloadURLResponse:
        """
        Get a pre-signed download URL.
        
        Args:
            package_id: Package ID
            version: Version string (defaults to latest)
            expiration_seconds: URL validity duration
            
        Returns:
            Download URL response
            
        Raises:
            EntityNotFoundError: If package or version not found
        """
        logger.info(f"Generating download URL for {package_id} version {version or 'latest'}")
        
        # Get package and version
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        if version:
            pkg_version = package.get_version(version)
        else:
            pkg_version = package.get_latest_version()
        
        if not pkg_version:
            raise EntityNotFoundError(f"Version not found: {version or 'latest'}")
        
        if pkg_version.is_yanked:
            raise ValueError(f"Version {pkg_version.version} has been yanked")
        
        # Generate download URL
        download_url = await self.storage_repo.get_download_url(
            file_path=pkg_version.storage_path,
            expiration_seconds=expiration_seconds
        )
        
        return DownloadURLResponse(
            download_url=download_url,
            expires_at=datetime.now() + timedelta(seconds=expiration_seconds),
            file_size_bytes=pkg_version.file_size_bytes,
            checksum=pkg_version.checksum,
        )
    
    async def get_package(self, package_id: str, include_versions: bool = True) -> PackageResponse:
        """
        Get a package by ID.
        
        Args:
            package_id: Package ID
            include_versions: Whether to include version list
            
        Returns:
            Package response
            
        Raises:
            EntityNotFoundError: If package not found
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        return self._to_package_response(package, include_versions)
    
    async def get_package_by_name(self, name: str, include_versions: bool = True) -> PackageResponse:
        """
        Get a package by name.
        
        Args:
            name: Package name
            include_versions: Whether to include version list
            
        Returns:
            Package response
            
        Raises:
            EntityNotFoundError: If package not found
        """
        package = await self.package_repo.get_by_name(name)
        if not package:
            raise EntityNotFoundError(f"Package not found: {name}")
        
        return self._to_package_response(package, include_versions)
    
    async def search_packages(self, request: SearchPackagesRequest) -> List[PackageSummaryResponse]:
        """
        Search for packages.
        
        Args:
            request: Search request
            
        Returns:
            List of matching packages
        """
        packages = await self.package_repo.search(
            query=request.query or "",
            tags=request.tags,
            categories=request.categories,
            limit=request.limit,
        )
        
        return [self._to_package_summary(pkg) for pkg in packages]
    
    async def list_packages(
        self,
        limit: int = 100,
        offset: int = 0,
        include_private: bool = False
    ) -> List[PackageSummaryResponse]:
        """List all packages."""
        packages = await self.package_repo.list_all(limit, offset, include_private)
        return [self._to_package_summary(pkg) for pkg in packages]
    
    async def get_popular_packages(self, limit: int = 20) -> List[PackageSummaryResponse]:
        """Get most popular packages."""
        packages = await self.package_repo.get_popular(limit)
        return [self._to_package_summary(pkg) for pkg in packages]
    
    async def get_recent_packages(self, limit: int = 20) -> List[PackageSummaryResponse]:
        """Get recently published packages."""
        packages = await self.package_repo.get_recent(limit)
        return [self._to_package_summary(pkg) for pkg in packages]
    
    async def update_package(
        self,
        package_id: str,
        request: UpdatePackageRequest
    ) -> PackageResponse:
        """
        Update package metadata.
        
        Args:
            package_id: Package ID
            request: Update request
            
        Returns:
            Updated package
            
        Raises:
            EntityNotFoundError: If package not found
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        # Update fields if provided
        if request.display_name:
            package.display_name = request.display_name
        if request.description:
            package.description = request.description
        if request.author:
            package.author = request.author
        if request.author_email is not None:
            package.author_email = request.author_email
        if request.homepage_url is not None:
            package.homepage_url = request.homepage_url
        if request.repository_url is not None:
            package.repository_url = request.repository_url
        if request.documentation_url is not None:
            package.documentation_url = request.documentation_url
        if request.license:
            package.license = request.license
        if request.tags is not None:
            package.tags = request.tags
        if request.categories is not None:
            package.categories = request.categories
        
        package.updated_at = datetime.now()
        
        await self.package_repo.update(package)
        
        return self._to_package_response(package)
    
    async def publish_package(self, package_id: str) -> PackageResponse:
        """Publish a package."""
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        package.publish()
        await self.package_repo.update(package)
        
        logger.info(f"Package published: {package_id}")
        return self._to_package_response(package)
    
    async def get_package_stats(self, package_id: str) -> PackageStatsResponse:
        """Get package statistics."""
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise EntityNotFoundError(f"Package not found: {package_id}")
        
        return PackageStatsResponse(
            package_id=package.package_id,
            name=package.name,
            total_downloads=package.total_downloads,
            download_count_30d=package.download_count_30d,
            download_count_7d=0,  # Would need time-series data
            download_count_24h=0,  # Would need time-series data
            star_count=package.star_count,
            version_count=len(package.versions),
            latest_version=package.latest_version,
        )
    
    def _to_package_response(
        self,
        package: MCPPackage,
        include_versions: bool = False
    ) -> PackageResponse:
        """Convert package entity to response DTO."""
        data = package.to_dict(include_versions=include_versions)
        return PackageResponse(**data)
    
    def _to_package_summary(self, package: MCPPackage) -> PackageSummaryResponse:
        """Convert package entity to summary response."""
        return PackageSummaryResponse(
            package_id=package.package_id,
            name=package.name,
            display_name=package.display_name,
            description=package.description,
            author=package.author,
            latest_version=package.latest_version,
            total_downloads=package.total_downloads,
            star_count=package.star_count,
            tags=package.tags,
            categories=package.categories,
            popularity_score=package.get_popularity_score(),
        )
