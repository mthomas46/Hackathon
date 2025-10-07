"""Marketplace discovery and engagement functionality for MCP Store.

Provides trending, starring, and discovery features for package exploration.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.repositories.package_repository import (
    PackageRepository,
    EntityNotFoundError,
)

logger = logging.getLogger(__name__)


class MarketplaceError(Exception):
    """Base exception for marketplace errors."""
    pass


class MarketplaceUseCase:
    """
    Use case for marketplace discovery and engagement features.
    
    Features:
    - Star/unstar packages
    - Get trending packages
    - Get popular tags/categories
    - Featured packages
    - Download tracking
    """
    
    def __init__(self, package_repo: PackageRepository):
        self.package_repo = package_repo
        logger.info("MarketplaceUseCase initialized")
    
    async def star_package(self, package_id: str, user_id: str) -> Dict[str, Any]:
        """
        Star a package (increment star count).
        
        Args:
            package_id: Package to star
            user_id: User starring the package
            
        Returns:
            Updated package info with new star count
            
        Note: In a production system, you'd track user-package relationships
        to prevent duplicate stars. This is a simplified version.
        """
        try:
            package = await self.package_repo.get_package_by_id(package_id)
            if not package:
                raise MarketplaceError(f"Package {package_id} not found")
            
            package.increment_star_count()
            await self.package_repo.update_package(package)
            
            logger.info(f"User {user_id} starred package {package_id} (stars: {package.star_count})")
            
            return {
                "package_id": package.package_id,
                "package_name": package.name,
                "star_count": package.star_count,
                "starred_by": user_id,
            }
        except MarketplaceError:
            raise
        except Exception as e:
            logger.error(f"Failed to star package: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to star package: {e}") from e
    
    async def unstar_package(self, package_id: str, user_id: str) -> Dict[str, Any]:
        """
        Unstar a package (decrement star count).
        
        Args:
            package_id: Package to unstar
            user_id: User unstarring the package
            
        Returns:
            Updated package info with new star count
        """
        try:
            package = await self.package_repo.get_package_by_id(package_id)
            if not package:
                raise MarketplaceError(f"Package {package_id} not found")
            
            package.decrement_star_count()
            await self.package_repo.update_package(package)
            
            logger.info(f"User {user_id} unstarred package {package_id} (stars: {package.star_count})")
            
            return {
                "package_id": package.package_id,
                "package_name": package.name,
                "star_count": package.star_count,
                "unstarred_by": user_id,
            }
        except MarketplaceError:
            raise
        except Exception as e:
            logger.error(f"Failed to unstar package: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to unstar package: {e}") from e
    
    async def record_download(self, package_id: str) -> None:
        """
        Record a package download (increment download count).
        
        Args:
            package_id: Package that was downloaded
        """
        try:
            package = await self.package_repo.get_package_by_id(package_id)
            if not package:
                logger.warning(f"Attempted to record download for non-existent package {package_id}")
                return
            
            package.increment_download_count()
            await self.package_repo.update_package(package)
            
            logger.info(f"Recorded download for package {package_id} (downloads: {package.download_count})")
        except Exception as e:
            logger.error(f"Failed to record download: {e}", exc_info=True)
            # Don't raise - downloads tracking is non-critical
    
    async def get_trending(
        self,
        days: int = 7,
        sort_by: str = "downloads",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending packages.
        
        Args:
            days: Time window for trending calculation (not used yet, placeholder)
            sort_by: Sort by 'downloads' or 'stars'
            limit: Number of packages to return
            
        Returns:
            List of trending packages with stats
        """
        try:
            # Get all published packages
            from services.mcp_store.domain.value_objects.package_status import PackageStatus
            
            packages = await self.package_repo.list_packages(
                status=PackageStatus.PUBLISHED,
                is_public=True,
                sort_by="download_count" if sort_by == "downloads" else "star_count",
                sort_order="desc",
                limit=limit,
            )
            
            trending = []
            for pkg in packages:
                trending.append({
                    "package_id": pkg.package_id,
                    "name": pkg.name,
                    "description": pkg.description,
                    "owner_id": pkg.owner_id,
                    "download_count": pkg.download_count,
                    "star_count": pkg.star_count,
                    "tags": pkg.tags,
                    "categories": pkg.categories,
                    "created_at": pkg.created_at.isoformat(),
                })
            
            logger.info(f"Retrieved {len(trending)} trending packages (sort_by={sort_by})")
            return trending
        except Exception as e:
            logger.error(f"Failed to get trending packages: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to get trending packages: {e}") from e
    
    async def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most popular tags across all packages.
        
        Args:
            limit: Number of tags to return
            
        Returns:
            List of tags with usage counts
        """
        try:
            from services.mcp_store.domain.value_objects.package_status import PackageStatus
            
            # Get all published public packages
            packages = await self.package_repo.list_packages(
                status=PackageStatus.PUBLISHED,
                is_public=True,
                limit=1000,  # Get a large sample
            )
            
            # Count tag occurrences
            tag_counter = Counter()
            for pkg in packages:
                for tag in pkg.tags:
                    tag_counter[tag] += 1
            
            # Get top tags
            popular_tags = [
                {"tag": tag, "count": count}
                for tag, count in tag_counter.most_common(limit)
            ]
            
            logger.info(f"Retrieved {len(popular_tags)} popular tags")
            return popular_tags
        except Exception as e:
            logger.error(f"Failed to get popular tags: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to get popular tags: {e}") from e
    
    async def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular categories across all packages.
        
        Args:
            limit: Number of categories to return
            
        Returns:
            List of categories with usage counts
        """
        try:
            from services.mcp_store.domain.value_objects.package_status import PackageStatus
            
            # Get all published public packages
            packages = await self.package_repo.list_packages(
                status=PackageStatus.PUBLISHED,
                is_public=True,
                limit=1000,  # Get a large sample
            )
            
            # Count category occurrences
            category_counter = Counter()
            for pkg in packages:
                for category in pkg.categories:
                    category_counter[category] += 1
            
            # Get top categories
            popular_categories = [
                {"category": category, "count": count}
                for category, count in category_counter.most_common(limit)
            ]
            
            logger.info(f"Retrieved {len(popular_categories)} popular categories")
            return popular_categories
        except Exception as e:
            logger.error(f"Failed to get popular categories: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to get popular categories: {e}") from e
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """
        Get overall marketplace statistics.
        
        Returns:
            Marketplace stats (total packages, downloads, etc.)
        """
        try:
            from services.mcp_store.domain.value_objects.package_status import PackageStatus
            
            # Get all packages
            all_packages = await self.package_repo.list_packages(limit=10000)
            published_packages = await self.package_repo.list_packages(
                status=PackageStatus.PUBLISHED,
                limit=10000
            )
            public_packages = await self.package_repo.list_packages(
                status=PackageStatus.PUBLISHED,
                is_public=True,
                limit=10000
            )
            
            # Calculate totals
            total_downloads = sum(pkg.download_count for pkg in all_packages)
            total_stars = sum(pkg.star_count for pkg in all_packages)
            
            stats = {
                "total_packages": len(all_packages),
                "published_packages": len(published_packages),
                "public_packages": len(public_packages),
                "total_downloads": total_downloads,
                "total_stars": total_stars,
                "average_downloads_per_package": total_downloads / len(all_packages) if all_packages else 0,
                "average_stars_per_package": total_stars / len(all_packages) if all_packages else 0,
            }
            
            logger.info(f"Retrieved marketplace stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get marketplace stats: {e}", exc_info=True)
            raise MarketplaceError(f"Failed to get marketplace stats: {e}") from e
