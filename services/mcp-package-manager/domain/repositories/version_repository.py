"""Version Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.package_version import PackageVersion


class VersionRepository(ABC):
    """Abstract repository for PackageVersion entities."""
    
    @abstractmethod
    async def add(self, version: PackageVersion) -> None:
        """Add package version."""
        pass
    
    @abstractmethod
    async def get_by_package_and_version(
        self, package_id: str, version: str
    ) -> Optional[PackageVersion]:
        """Get version by package ID and version string."""
        pass
    
    @abstractmethod
    async def list_by_package(self, package_id: str) -> List[PackageVersion]:
        """List all versions for a package."""
        pass
    
    @abstractmethod
    async def get_latest(self, package_id: str) -> Optional[PackageVersion]:
        """Get latest version for a package."""
        pass
    
    @abstractmethod
    async def delete(self, package_id: str, version: str) -> None:
        """Delete a version."""
        pass
    
    @abstractmethod
    async def update(self, version: PackageVersion) -> None:
        """Update version."""
        pass

