"""Package Management Application Service."""

from typing import List, Optional, Dict, Any

from ...domain.entities.package import MCPPackage
from ...domain.entities.package_version import PackageVersion
from ...domain.repositories.package_repository import PackageRepository
from ...domain.repositories.version_repository import VersionRepository


class PackageService:
    """
    Application service for package management.
    
    Handles CRUD operations and business logic for MCP packages.
    """
    
    def __init__(
        self,
        package_repo: PackageRepository,
        version_repo: VersionRepository,
    ):
        """
        Initialize package service.
        
        Args:
            package_repo: Package repository
            version_repo: Version repository
        """
        self.package_repo = package_repo
        self.version_repo = version_repo
    
    async def create_package(
        self,
        name: str,
        version: str,
        description: str = "",
        author: str = "",
        **kwargs,
    ) -> MCPPackage:
        """
        Create new package.
        
        Args:
            name: Package name
            version: Initial version
            description: Package description
            author: Package author
            **kwargs: Additional attributes
            
        Returns:
            Created package
        """
        package = MCPPackage(
            name=name,
            version=version,
            description=description,
            author=author,
            **kwargs,
        )
        
        # Calculate checksum
        package.calculate_checksum()
        
        # Save package
        await self.package_repo.add(package)
        
        # Create initial version
        pkg_version = PackageVersion(
            package_id=package.package_id,
            version=version,
            changelog="Initial version",
            created_by=author,
        )
        await self.version_repo.add(pkg_version)
        
        return package
    
    async def get_package(self, package_id: str) -> Optional[MCPPackage]:
        """
        Get package by ID.
        
        Args:
            package_id: Package ID
            
        Returns:
            Package or None
        """
        return await self.package_repo.get_by_id(package_id)
    
    async def get_package_by_name(self, name: str, version: Optional[str] = None) -> Optional[MCPPackage]:
        """
        Get package by name and optionally version.
        
        Args:
            name: Package name
            version: Optional version string
            
        Returns:
            Package or None
        """
        if version:
            return await self.package_repo.get_by_name_and_version(name, version)
        return await self.package_repo.get_by_name(name)
    
    async def update_package(
        self,
        package_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
    ) -> MCPPackage:
        """
        Update package.
        
        Args:
            package_id: Package ID
            description: New description
            tags: New tags
            status: New status
            
        Returns:
            Updated package
            
        Raises:
            ValueError: If package not found
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Update fields
        if description is not None:
            package.description = description
        
        if tags is not None:
            package.tags = tags
        
        if status is not None:
            if status == "published":
                package.publish()
            elif status == "deprecated":
                package.deprecate()
            else:
                package.status = status
        
        # Recalculate checksum
        package.calculate_checksum()
        
        await self.package_repo.update(package)
        return package
    
    async def delete_package(self, package_id: str) -> None:
        """
        Delete package.
        
        Args:
            package_id: Package ID
        """
        await self.package_repo.delete(package_id)
    
    async def add_knowledge_item(
        self,
        package_id: str,
        content: str,
        item_type: str = "text",
        relevance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MCPPackage:
        """
        Add knowledge item to package.
        
        Args:
            package_id: Package ID
            content: Knowledge content
            item_type: Type of knowledge
            relevance: Relevance score
            metadata: Additional metadata
            
        Returns:
            Updated package
            
        Raises:
            ValueError: If package not found
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        package.add_knowledge_item(
            content=content,
            item_type=item_type,
            relevance=relevance,
            metadata=metadata,
        )
        
        # Update checksum
        package.calculate_checksum()
        
        await self.package_repo.update(package)
        return package
    
    async def validate_package(self, package_id: str) -> MCPPackage:
        """
        Validate package.
        
        Args:
            package_id: Package ID
            
        Returns:
            Validated package with status
            
        Raises:
            ValueError: If package not found
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        package.validate()
        await self.package_repo.update(package)
        
        return package
    
    async def list_packages(self) -> List[MCPPackage]:
        """
        List all packages.
        
        Returns:
            List of packages
        """
        return await self.package_repo.list_all()
    
    async def search_packages(self, query: str) -> List[MCPPackage]:
        """
        Search packages.
        
        Args:
            query: Search query
            
        Returns:
            List of matching packages
        """
        return await self.package_repo.search(query)
    
    async def get_package_versions(self, package_id: str) -> List[PackageVersion]:
        """
        Get all versions for a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            List of versions
        """
        return await self.version_repo.list_by_package(package_id)
    
    async def get_latest_version(self, package_id: str) -> Optional[PackageVersion]:
        """
        Get latest version for a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            Latest version or None
        """
        return await self.version_repo.get_latest(package_id)

