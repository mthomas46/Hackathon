"""
Document version manager.

Manages document versions linked to git commits.
"""

import hashlib
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ..models import DocumentVersion, VersionDiff
from ..storage import get_database
from ..storage.db_models import DocumentVersionModel, DocumentModel
from ..services.git import get_git_service

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class VersionManager:
    """
    Manages document versions and their git history.
    
    Links documents to git commits and provides version comparison.
    """
    
    def __init__(self):
        """Initialize version manager."""
        self.git_service = get_git_service()
        self.db = get_database()
        
        logger.info("Version manager initialized")
    
    async def create_version(
        self,
        document_id: UUID,
        content: str,
        git_commit_sha: str,
        commit_message: str,
        commit_date: datetime
    ) -> DocumentVersion:
        """
        Create a new version of a document.
        
        Args:
            document_id: Document UUID
            content: Document content at this version
            git_commit_sha: Git commit SHA
            commit_message: Commit message
            commit_date: Commit timestamp
        
        Returns:
            Created DocumentVersion
        """
        async with self.db.session() as session:
            # Get current version number
            current_version = await self._get_latest_version_number(session, document_id)
            next_version = (current_version + 1) if current_version else 1
            
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if content actually changed
            if current_version:
                last_version = await self._get_version_by_number(
                    session,
                    document_id,
                    current_version
                )
                if last_version and last_version.content_hash == content_hash:
                    logger.info(f"Content unchanged for document {document_id}, skipping version")
                    return DocumentVersion(
                        id=last_version.id,
                        document_id=document_id,
                        version_number=last_version.version_number,
                        git_commit_sha=last_version.git_commit_sha,
                        commit_message=last_version.commit_message,
                        commit_date=last_version.commit_date,
                        content=last_version.content,
                        content_hash=last_version.content_hash,
                        embedding_id=last_version.embedding_id
                    )
            
            # Create new version
            version = DocumentVersionModel(
                document_id=document_id,
                version_number=next_version,
                git_commit_sha=git_commit_sha,
                commit_message=commit_message,
                commit_date=commit_date,
                content=content,
                content_hash=content_hash
            )
            
            session.add(version)
            await session.commit()
            await session.refresh(version)
            
            logger.info(f"Created version {next_version} for document {document_id}")
            
            return DocumentVersion(
                id=version.id,
                document_id=document_id,
                version_number=version.version_number,
                git_commit_sha=version.git_commit_sha,
                commit_message=version.commit_message,
                commit_date=version.commit_date,
                content=version.content,
                content_hash=version.content_hash,
                embedding_id=version.embedding_id
            )
    
    async def get_version_at_commit(
        self,
        document_id: UUID,
        commit_sha: str
    ) -> Optional[DocumentVersion]:
        """
        Get document version at specific commit.
        
        If version doesn't exist in database, retrieves from git.
        
        Args:
            document_id: Document UUID
            commit_sha: Git commit SHA
        
        Returns:
            DocumentVersion or None if not found
        """
        async with self.db.session() as session:
            # Try to get from database
            result = await session.execute(
                select(DocumentVersionModel).where(
                    and_(
                        DocumentVersionModel.document_id == document_id,
                        DocumentVersionModel.git_commit_sha == commit_sha
                    )
                )
            )
            version = result.scalar_one_or_none()
            
            if version:
                return self._model_to_pydantic(version)
            
            # Not in database, get from git
            doc_result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
            doc = doc_result.scalar_one_or_none()
            
            if not doc:
                logger.error(f"Document {document_id} not found")
                return None
            
            # Get file content from git
            content = await self.git_service.get_file_at_commit(
                doc.file_path,
                commit_sha
            )
            
            if not content:
                logger.warning(f"File {doc.file_path} not found at commit {commit_sha}")
                return None
            
            # Get commit metadata
            commit = await self.git_service.get_commit_metadata(commit_sha)
            
            if not commit:
                return None
            
            # Create version on-demand
            return await self.create_version(
                document_id=document_id,
                content=content,
                git_commit_sha=commit_sha,
                commit_message=commit.message,
                commit_date=commit.date
            )
    
    async def get_version_by_number(
        self,
        document_id: UUID,
        version_number: int
    ) -> Optional[DocumentVersion]:
        """
        Get version by number.
        
        Args:
            document_id: Document UUID
            version_number: Version number
        
        Returns:
            DocumentVersion or None if not found
        """
        async with self.db.session() as session:
            version = await self._get_version_by_number(session, document_id, version_number)
            return self._model_to_pydantic(version) if version else None
    
    async def get_all_versions(
        self,
        document_id: UUID
    ) -> List[DocumentVersion]:
        """
        Get all versions for a document.
        
        Args:
            document_id: Document UUID
        
        Returns:
            List of versions ordered by version number
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(DocumentVersionModel)
                .where(DocumentVersionModel.document_id == document_id)
                .order_by(DocumentVersionModel.version_number)
            )
            versions = result.scalars().all()
            
            return [self._model_to_pydantic(v) for v in versions]
    
    async def compare_versions(
        self,
        document_id: UUID,
        from_version: int,
        to_version: int
    ) -> VersionDiff:
        """
        Compare two versions of a document.
        
        Args:
            document_id: Document UUID
            from_version: Starting version number
            to_version: Ending version number
        
        Returns:
            VersionDiff with comparison details
        """
        async with self.db.session() as session:
            v1 = await self._get_version_by_number(session, document_id, from_version)
            v2 = await self._get_version_by_number(session, document_id, to_version)
            
            if not v1 or not v2:
                from ...utils.exceptions import ValidationError
                raise ValidationError("Version not found")
            
            # Generate unified diff
            import difflib
            diff = difflib.unified_diff(
                v1.content.splitlines(keepends=True),
                v2.content.splitlines(keepends=True),
                fromfile=f"v{from_version}",
                tofile=f"v{to_version}",
                lineterm=""
            )
            
            diff_str = "".join(diff)
            
            # Count changes
            lines_added = diff_str.count('\n+')
            lines_removed = diff_str.count('\n-')
            
            # Generate summary
            summary = f"Changed {lines_added + lines_removed} lines: +{lines_added} -{lines_removed}"
            
            return VersionDiff(
                document_id=document_id,
                from_version=from_version,
                to_version=to_version,
                diff=diff_str,
                summary=summary,
                lines_added=lines_added,
                lines_removed=lines_removed,
                from_commit_sha=v1.git_commit_sha,
                to_commit_sha=v2.git_commit_sha
            )
    
    async def _get_latest_version_number(
        self,
        session: AsyncSession,
        document_id: UUID
    ) -> Optional[int]:
        """Get the latest version number for a document."""
        from sqlalchemy import func
        
        result = await session.execute(
            select(func.max(DocumentVersionModel.version_number))
            .where(DocumentVersionModel.document_id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_version_by_number(
        self,
        session: AsyncSession,
        document_id: UUID,
        version_number: int
    ) -> Optional[DocumentVersionModel]:
        """Get version by number."""
        result = await session.execute(
            select(DocumentVersionModel).where(
                and_(
                    DocumentVersionModel.document_id == document_id,
                    DocumentVersionModel.version_number == version_number
                )
            )
        )
        return result.scalar_one_or_none()
    
    def _model_to_pydantic(self, model: DocumentVersionModel) -> DocumentVersion:
        """Convert SQLAlchemy model to Pydantic."""
        return DocumentVersion(
            id=model.id,
            document_id=model.document_id,
            version_number=model.version_number,
            git_commit_sha=model.git_commit_sha,
            commit_message=model.commit_message,
            commit_date=model.commit_date,
            content=model.content,
            content_hash=model.content_hash,
            embedding_id=model.embedding_id
        )


# Global instance
_version_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """Get global version manager instance."""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager

