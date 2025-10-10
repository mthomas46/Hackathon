"""
Document repository for Ecosystem MCP Service.

Provides document-specific database operations.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import DocumentModel
from .base import BaseRepository


class DocumentRepository(BaseRepository[DocumentModel]):
    """
    Document repository with domain-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize document repository."""
        super().__init__(DocumentModel, session)
    
    async def get_by_file_path(self, file_path: str) -> Optional[DocumentModel]:
        """
        Get latest document by file path.
        
        Args:
            file_path: File path
        
        Returns:
            Document model or None
        """
        result = await self.session.execute(
            select(self.model).where(
                and_(
                    self.model.file_path == file_path,
                    self.model.is_latest == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_service(
        self,
        service_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentModel]:
        """
        Get documents by service name.
        
        Args:
            service_name: Service name
            limit: Maximum documents
            offset: Offset for pagination
        
        Returns:
            List of documents
        """
        result = await self.session.execute(
            select(self.model)
            .where(
                and_(
                    self.model.service_name == service_name,
                    self.model.is_latest == True
                )
            )
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_content_hash(
        self,
        content_hash: str
    ) -> Optional[DocumentModel]:
        """
        Get document by content hash (for deduplication).
        
        Args:
            content_hash: SHA256 hash of content
        
        Returns:
            Document model or None
        """
        result = await self.session.execute(
            select(self.model).where(self.model.content_hash == content_hash)
        )
        return result.scalar_one_or_none()
    
    async def get_by_commit(
        self,
        git_commit_sha: str,
        limit: int = 100
    ) -> List[DocumentModel]:
        """
        Get all documents from a specific commit.
        
        Args:
            git_commit_sha: Git commit SHA
            limit: Maximum documents
        
        Returns:
            List of documents
        """
        result = await self.session.execute(
            select(self.model)
            .where(self.model.git_commit_sha == git_commit_sha)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_service(self, service_name: str) -> int:
        """
        Count documents for a service.
        
        Args:
            service_name: Service name
        
        Returns:
            Document count
        """
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model)
            .where(
                and_(
                    self.model.service_name == service_name,
                    self.model.is_latest == True
                )
            )
        )
        return result.scalar_one()
    
    async def mark_as_outdated(self, file_path: str) -> None:
        """
        Mark all versions of a file as not latest.
        
        Args:
            file_path: File path
        """
        from sqlalchemy import update
        await self.session.execute(
            update(self.model)
            .where(self.model.file_path == file_path)
            .values(is_latest=False)
        )
        await self.session.flush()

