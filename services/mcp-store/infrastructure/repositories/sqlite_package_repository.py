"""SQLite implementation of PackageRepository."""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.repositories.package_repository import (
    PackageRepository,
    EntityNotFoundError,
    DuplicateEntityError,
    RepositoryError,
)
from services.mcp_store.domain.value_objects.package_status import PackageStatus
from services.mcp_store.infrastructure.database.models import PackageModel, VersionModel

logger = logging.getLogger(__name__)


class SqlitePackageRepository(PackageRepository):
    """SQLite implementation of PackageRepository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.info("SQLite Package repository initialized")
    
    async def save(self, package: MCPPackage) -> None:
        """Save a new package."""
        try:
            # Check for duplicate
            existing = await self.session.execute(
                select(PackageModel).where(PackageModel.package_id == package.package_id)
            )
            if existing.scalar_one_or_none():
                raise DuplicateEntityError(f"Package already exists: {package.package_id}")
            
            # Convert to model
            model = self._to_model(package)
            
            self.session.add(model)
            await self.session.commit()
            
            logger.info(f"Package saved: {package.package_id}")
        except DuplicateEntityError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to save package: {e}")
            raise RepositoryError(f"Failed to save package: {e}") from e
    
    async def get_by_id(self, package_id: str) -> Optional[MCPPackage]:
        """Retrieve a package by ID."""
        try:
            result = await self.session.execute(
                select(PackageModel)
                .options(selectinload(PackageModel.versions))
                .where(PackageModel.package_id == package_id)
            )
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_entity(model)
        except Exception as e:
            logger.error(f"Failed to get package by ID: {e}")
            raise RepositoryError(f"Failed to get package: {e}") from e
    
    async def get_by_name(self, name: str) -> Optional[MCPPackage]:
        """Retrieve a package by name."""
        try:
            result = await self.session.execute(
                select(PackageModel)
                .options(selectinload(PackageModel.versions))
                .where(PackageModel.name == name)
            )
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_entity(model)
        except Exception as e:
            logger.error(f"Failed to get package by name: {e}")
            raise RepositoryError(f"Failed to get package: {e}") from e
    
    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        include_private: bool = False
    ) -> List[MCPPackage]:
        """List all packages."""
        try:
            query = select(PackageModel).options(selectinload(PackageModel.versions))
            
            if not include_private:
                query = query.where(PackageModel.is_public == True)
            
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to list packages: {e}")
            raise RepositoryError(f"Failed to list packages: {e}") from e
    
    async def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[MCPPackage]:
        """Search packages by query, tags, and categories."""
        try:
            stmt = select(PackageModel).options(selectinload(PackageModel.versions))
            
            # Build search conditions
            conditions = []
            
            # Text search (name, display_name, description)
            if query:
                search_pattern = f"%{query}%"
                conditions.append(
                    or_(
                        PackageModel.name.ilike(search_pattern),
                        PackageModel.display_name.ilike(search_pattern),
                        PackageModel.description.ilike(search_pattern)
                    )
                )
            
            # Tag filter (SQLite JSON search - simplified)
            if tags:
                for tag in tags:
                    # Use LIKE for JSON array search in SQLite
                    conditions.append(
                        func.json_extract(PackageModel.tags, '$').like(f'%"{tag}"%')
                    )
            
            # Category filter (SQLite JSON search - simplified)
            if categories:
                for category in categories:
                    # Use LIKE for JSON array search in SQLite
                    conditions.append(
                        func.json_extract(PackageModel.categories, '$').like(f'%"{category}"%')
                    )
            
            # Apply conditions
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Only public packages in search
            stmt = stmt.where(PackageModel.is_public == True)
            
            # Order by popularity (downloads + stars)
            stmt = stmt.order_by(
                (PackageModel.total_downloads + PackageModel.star_count * 10).desc()
            )
            
            stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to search packages: {e}")
            raise RepositoryError(f"Failed to search packages: {e}") from e
    
    async def get_by_owner(self, owner_id: str, limit: int = 100) -> List[MCPPackage]:
        """Get packages by owner."""
        try:
            result = await self.session.execute(
                select(PackageModel)
                .options(selectinload(PackageModel.versions))
                .where(PackageModel.owner_id == owner_id)
                .limit(limit)
            )
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to get packages by owner: {e}")
            raise RepositoryError(f"Failed to get packages by owner: {e}") from e
    
    async def get_popular(self, limit: int = 20) -> List[MCPPackage]:
        """Get most popular packages."""
        try:
            result = await self.session.execute(
                select(PackageModel)
                .options(selectinload(PackageModel.versions))
                .where(PackageModel.is_public == True)
                .order_by(
                    (PackageModel.total_downloads + PackageModel.star_count * 10).desc()
                )
                .limit(limit)
            )
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to get popular packages: {e}")
            raise RepositoryError(f"Failed to get popular packages: {e}") from e
    
    async def get_recent(self, limit: int = 20) -> List[MCPPackage]:
        """Get recently published packages."""
        try:
            result = await self.session.execute(
                select(PackageModel)
                .options(selectinload(PackageModel.versions))
                .where(
                    and_(
                        PackageModel.is_public == True,
                        PackageModel.published_at.isnot(None)
                    )
                )
                .order_by(PackageModel.published_at.desc())
                .limit(limit)
            )
            models = result.scalars().all()
            
            return [self._to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Failed to get recent packages: {e}")
            raise RepositoryError(f"Failed to get recent packages: {e}") from e
    
    async def update(self, package: MCPPackage) -> None:
        """Update an existing package."""
        try:
            # Get existing model
            result = await self.session.execute(
                select(PackageModel).where(PackageModel.package_id == package.package_id)
            )
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFoundError(f"Package not found: {package.package_id}")
            
            # Update fields
            self._update_model_from_entity(model, package)
            
            await self.session.commit()
            
            logger.info(f"Package updated: {package.package_id}")
        except EntityNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update package: {e}")
            raise RepositoryError(f"Failed to update package: {e}") from e
    
    async def delete(self, package_id: str) -> None:
        """Delete a package."""
        try:
            result = await self.session.execute(
                select(PackageModel).where(PackageModel.package_id == package_id)
            )
            model = result.scalar_one_or_none()
            
            if not model:
                raise EntityNotFoundError(f"Package not found: {package_id}")
            
            await self.session.delete(model)
            await self.session.commit()
            
            logger.info(f"Package deleted: {package_id}")
        except EntityNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete package: {e}")
            raise RepositoryError(f"Failed to delete package: {e}") from e
    
    async def exists(self, package_id: str) -> bool:
        """Check if a package exists."""
        try:
            result = await self.session.execute(
                select(func.count()).select_from(PackageModel).where(PackageModel.package_id == package_id)
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check package existence: {e}")
            raise RepositoryError(f"Failed to check package existence: {e}") from e
    
    async def count(self, include_private: bool = False) -> int:
        """Get total number of packages."""
        try:
            query = select(func.count()).select_from(PackageModel)
            
            if not include_private:
                query = query.where(PackageModel.is_public == True)
            
            result = await self.session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to count packages: {e}")
            raise RepositoryError(f"Failed to count packages: {e}") from e
    
    def _to_model(self, package: MCPPackage) -> PackageModel:
        """Convert domain entity to SQLAlchemy model."""
        model = PackageModel(
            package_id=package.package_id,
            name=package.name,
            display_name=package.display_name,
            description=package.description,
            author=package.author,
            author_email=package.author_email,
            homepage_url=package.homepage_url,
            repository_url=package.repository_url,
            documentation_url=package.documentation_url,
            license=package.license,
            status=package.status.value,
            latest_version=package.latest_version,
            tags=package.tags,
            categories=package.categories,
            total_downloads=package.total_downloads,
            download_count_30d=package.download_count_30d,
            star_count=package.star_count,
            created_at=package.created_at,
            updated_at=package.updated_at,
            published_at=package.published_at,
            owner_id=package.owner_id,
            is_public=package.is_public,
            allowed_users=package.allowed_users,
            embedding_count=package.embedding_count,
            document_count=package.document_count,
            entity_count=package.entity_count,
            relationship_count=package.relationship_count,
            metadata=package.metadata,
        )
        
        # Add versions
        for version in package.versions:
            version_model = VersionModel(
                version=version.version,
                package_id=version.package_id,
                storage_path=version.storage_path,
                file_size_bytes=version.file_size_bytes,
                checksum=version.checksum,
                changelog=version.changelog,
                release_notes=version.release_notes,
                is_prerelease=version.is_prerelease,
                is_yanked=version.is_yanked,
                yank_reason=version.yank_reason,
                created_at=version.created_at,
                published_at=version.published_at,
                yanked_at=version.yanked_at,
                download_count=version.download_count,
                dependencies=version.dependencies,
                min_python_version=version.min_python_version,
                max_python_version=version.max_python_version,
                metadata=version.metadata,
            )
            model.versions.append(version_model)
        
        return model
    
    def _to_entity(self, model: PackageModel) -> MCPPackage:
        """Convert SQLAlchemy model to domain entity."""
        # Convert versions
        versions = []
        for version_model in model.versions:
            version = MCPVersion(
                version=version_model.version,
                package_id=version_model.package_id,
                storage_path=version_model.storage_path,
                file_size_bytes=version_model.file_size_bytes,
                checksum=version_model.checksum,
                changelog=version_model.changelog,
                release_notes=version_model.release_notes,
                is_prerelease=version_model.is_prerelease,
                is_yanked=version_model.is_yanked,
                yank_reason=version_model.yank_reason,
                created_at=version_model.created_at,
                published_at=version_model.published_at,
                yanked_at=version_model.yanked_at,
                download_count=version_model.download_count,
                dependencies=version_model.dependencies or {},
                min_python_version=version_model.min_python_version,
                max_python_version=version_model.max_python_version,
                metadata=version_model.metadata or {},
            )
            versions.append(version)
        
        # Convert package
        package = MCPPackage(
            package_id=model.package_id,
            name=model.name,
            display_name=model.display_name,
            description=model.description,
            author=model.author,
            author_email=model.author_email,
            homepage_url=model.homepage_url,
            repository_url=model.repository_url,
            documentation_url=model.documentation_url,
            license=model.license,
            status=PackageStatus(model.status),
            versions=versions,
            latest_version=model.latest_version,
            tags=model.tags or [],
            categories=model.categories or [],
            total_downloads=model.total_downloads,
            download_count_30d=model.download_count_30d,
            star_count=model.star_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            published_at=model.published_at,
            owner_id=model.owner_id,
            is_public=model.is_public,
            allowed_users=model.allowed_users or [],
            embedding_count=model.embedding_count,
            document_count=model.document_count,
            entity_count=model.entity_count,
            relationship_count=model.relationship_count,
            metadata=model.metadata or {},
        )
        
        return package
    
    def _update_model_from_entity(self, model: PackageModel, package: MCPPackage) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.display_name = package.display_name
        model.description = package.description
        model.author = package.author
        model.author_email = package.author_email
        model.homepage_url = package.homepage_url
        model.repository_url = package.repository_url
        model.documentation_url = package.documentation_url
        model.license = package.license
        model.status = package.status.value
        model.latest_version = package.latest_version
        model.tags = package.tags
        model.categories = package.categories
        model.total_downloads = package.total_downloads
        model.download_count_30d = package.download_count_30d
        model.star_count = package.star_count
        model.updated_at = package.updated_at
        model.published_at = package.published_at
        model.is_public = package.is_public
        model.allowed_users = package.allowed_users
        model.embedding_count = package.embedding_count
        model.document_count = package.document_count
        model.entity_count = package.entity_count
        model.relationship_count = package.relationship_count
        model.metadata = package.metadata
        
        # Update versions (simplified - in production, handle adds/updates/deletes)
        # For now, clear and re-add
        model.versions.clear()
        for version in package.versions:
            version_model = VersionModel(
                version=version.version,
                package_id=version.package_id,
                storage_path=version.storage_path,
                file_size_bytes=version.file_size_bytes,
                checksum=version.checksum,
                changelog=version.changelog,
                release_notes=version.release_notes,
                is_prerelease=version.is_prerelease,
                is_yanked=version.is_yanked,
                yank_reason=version.yank_reason,
                created_at=version.created_at,
                published_at=version.published_at,
                yanked_at=version.yanked_at,
                download_count=version.download_count,
                dependencies=version.dependencies,
                min_python_version=version.min_python_version,
                max_python_version=version.max_python_version,
                metadata=version.metadata,
            )
            model.versions.append(version_model)
