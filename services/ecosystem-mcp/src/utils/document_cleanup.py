"""
Document Cleanup Utility

Uses intelligent filtering rules to identify and remove low-value documents
that are already in the database and ChromaDB.

Targets:
- Logs, configs, build artifacts (should have been filtered)
- Old versions (keep only latest)
- Duplicates with low value
- Test files (optional)

Features:
- Dry-run mode (safe preview)
- Category-based cleanup
- Statistics and reporting
- Backup before delete (optional)
"""

import logging
import asyncio
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..storage import get_database
from ..storage.db_models import DocumentModel, EmbeddingModel
from ..storage.chromadb_client import get_chroma_client
from .intelligent_file_filter import (
    get_intelligent_filter,
    FilePriority,
    FileCategory
)

logger = logging.getLogger(__name__)


class DocumentCleanupService:
    """
    Clean up low-value documents using intelligent filtering rules.
    """
    
    def __init__(self):
        """Initialize cleanup service."""
        self.file_filter = get_intelligent_filter()
        self.stats = {
            "total_documents": 0,
            "analyzed": 0,
            "marked_for_deletion": 0,
            "deleted": 0,
            "embeddings_deleted": 0,
            "by_category": {},
            "by_priority": {},
            "space_freed_mb": 0
        }
    
    async def analyze_documents(
        self,
        include_latest: bool = False,
        min_priority: Optional[FilePriority] = FilePriority.LOW
    ) -> Dict[str, any]:
        """
        Analyze all documents and identify cleanup candidates.
        
        Args:
            include_latest: If True, analyze latest versions too (default: False, only old versions)
            min_priority: Minimum priority to keep (default: LOW, skip everything below)
        
        Returns:
            Analysis results with statistics
        """
        logger.info("🔍 Analyzing documents for cleanup...")
        
        async with get_database().session() as session:
            # Build query
            query = select(DocumentModel)
            
            if not include_latest:
                # Only analyze non-latest versions (old versions)
                query = query.where(DocumentModel.is_latest == False)
            
            result = await session.execute(query)
            documents = result.scalars().all()
            
            self.stats["total_documents"] = len(documents)
            logger.info(f"📊 Found {len(documents)} documents to analyze")
            
            cleanup_candidates = []
            keep_documents = []
            
            for doc in documents:
                # Classify document using intelligent filter
                file_path = Path(doc.file_path)
                priority, category, reason = self.file_filter.classify_file(file_path)
                
                # Track statistics
                self.stats["analyzed"] += 1
                self.stats["by_category"][category.value] = \
                    self.stats["by_category"].get(category.value, 0) + 1
                self.stats["by_priority"][priority.name] = \
                    self.stats["by_priority"].get(priority.name, 0) + 1
                
                # Decide if should be deleted
                should_delete = False
                delete_reason = None
                
                if priority == FilePriority.SKIP:
                    should_delete = True
                    delete_reason = f"Low-value category: {reason}"
                elif min_priority and priority.value < min_priority.value:
                    should_delete = True
                    delete_reason = f"Below minimum priority ({min_priority.name})"
                
                if should_delete:
                    cleanup_candidates.append({
                        "id": doc.id,
                        "file_path": doc.file_path,
                        "priority": priority.name,
                        "category": category.value,
                        "reason": delete_reason,
                        "is_latest": doc.is_latest,
                        "created_at": doc.created_at,
                        "has_embedding": doc.embedding_id is not None,
                        "service_name": doc.service_name
                    })
                    self.stats["marked_for_deletion"] += 1
                else:
                    keep_documents.append({
                        "id": doc.id,
                        "file_path": doc.file_path,
                        "priority": priority.name,
                        "category": category.value
                    })
            
            logger.info(
                f"✅ Analysis complete: "
                f"{len(cleanup_candidates)} marked for deletion, "
                f"{len(keep_documents)} to keep"
            )
            
            return {
                "total_analyzed": self.stats["analyzed"],
                "cleanup_candidates": cleanup_candidates,
                "keep_documents": keep_documents,
                "statistics": self.stats
            }
    
    async def cleanup_documents(
        self,
        dry_run: bool = True,
        include_latest: bool = False,
        categories_to_remove: Optional[List[str]] = None,
        min_priority: Optional[FilePriority] = FilePriority.LOW
    ) -> Dict[str, any]:
        """
        Clean up low-value documents.
        
        Args:
            dry_run: If True, only show what would be deleted (default: True)
            include_latest: If True, can delete latest versions (default: False)
            categories_to_remove: Specific categories to remove (default: all SKIP priority)
            min_priority: Minimum priority to keep (default: LOW)
        
        Returns:
            Cleanup results
        """
        logger.info(
            f"🧹 Starting document cleanup "
            f"(dry_run={dry_run}, include_latest={include_latest})"
        )
        
        # First, analyze
        analysis = await self.analyze_documents(
            include_latest=include_latest,
            min_priority=min_priority
        )
        
        cleanup_candidates = analysis["cleanup_candidates"]
        
        # Filter by categories if specified
        if categories_to_remove:
            cleanup_candidates = [
                c for c in cleanup_candidates
                if c["category"] in categories_to_remove
            ]
            logger.info(f"🎯 Filtered to {len(cleanup_candidates)} candidates in specified categories")
        
        if dry_run:
            logger.info("📋 DRY RUN - No documents will be deleted")
            return {
                "dry_run": True,
                "would_delete": len(cleanup_candidates),
                "candidates": cleanup_candidates[:50],  # Show first 50
                "statistics": self.stats,
                "space_would_be_freed_mb": self._estimate_space(cleanup_candidates)
            }
        
        # Actually delete
        logger.warning(f"⚠️  DELETING {len(cleanup_candidates)} documents...")
        
        deleted_count = 0
        embeddings_deleted = 0
        
        async with get_database().session() as session:
            chroma = get_chroma_client()
            
            for candidate in cleanup_candidates:
                try:
                    doc_id = candidate["id"]
                    
                    # Delete from ChromaDB first
                    if candidate["has_embedding"]:
                        try:
                            await chroma.delete_embeddings([str(doc_id)])
                            embeddings_deleted += 1
                            logger.debug(f"🗑️  Deleted embedding for {candidate['file_path']}")
                        except Exception as e:
                            logger.warning(f"Failed to delete embedding: {e}")
                    
                    # Delete from PostgreSQL
                    await session.execute(
                        delete(DocumentModel).where(DocumentModel.id == doc_id)
                    )
                    deleted_count += 1
                    
                    if deleted_count % 100 == 0:
                        await session.commit()
                        logger.info(f"💾 Committed {deleted_count} deletions...")
                
                except Exception as e:
                    logger.error(f"Failed to delete document {candidate['file_path']}: {e}")
            
            # Final commit
            await session.commit()
        
        self.stats["deleted"] = deleted_count
        self.stats["embeddings_deleted"] = embeddings_deleted
        
        logger.info(
            f"✅ Cleanup complete: "
            f"Deleted {deleted_count} documents, "
            f"{embeddings_deleted} embeddings"
        )
        
        return {
            "dry_run": False,
            "deleted": deleted_count,
            "embeddings_deleted": embeddings_deleted,
            "candidates": cleanup_candidates,
            "statistics": self.stats
        }
    
    async def cleanup_by_category(
        self,
        categories: List[str],
        dry_run: bool = True
    ) -> Dict[str, any]:
        """
        Clean up documents in specific categories.
        
        Args:
            categories: List of category names to remove
                       (e.g., ["temporary", "configuration", "build_artifact"])
            dry_run: Preview mode
        
        Returns:
            Cleanup results
        """
        logger.info(f"🧹 Cleaning up categories: {categories}")
        
        return await self.cleanup_documents(
            dry_run=dry_run,
            include_latest=True,  # Categories can include latest
            categories_to_remove=categories,
            min_priority=None  # Don't use priority filter, use categories
        )
    
    async def cleanup_old_versions(
        self,
        dry_run: bool = True,
        older_than_days: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Clean up old document versions (keep only latest).
        
        Args:
            dry_run: Preview mode
            older_than_days: Only delete versions older than N days (optional)
        
        Returns:
            Cleanup results
        """
        logger.info("🧹 Cleaning up old versions...")
        
        async with get_database().session() as session:
            # Query non-latest versions
            query = select(DocumentModel).where(DocumentModel.is_latest == False)
            
            if older_than_days:
                cutoff = datetime.utcnow() - timedelta(days=older_than_days)
                query = query.where(DocumentModel.created_at < cutoff)
            
            result = await session.execute(query)
            old_versions = result.scalars().all()
            
            logger.info(f"📊 Found {len(old_versions)} old versions")
            
            if dry_run:
                return {
                    "dry_run": True,
                    "would_delete": len(old_versions),
                    "versions": [
                        {
                            "id": str(v.id),
                            "file_path": v.file_path,
                            "created_at": str(v.created_at),
                            "service_name": v.service_name
                        }
                        for v in old_versions[:50]
                    ]
                }
            
            # Delete
            deleted = 0
            embeddings_deleted = 0
            chroma = get_chroma_client()
            
            for version in old_versions:
                try:
                    # Delete embedding if exists
                    if version.embedding_id:
                        try:
                            await chroma.delete_embeddings([str(version.id)])
                            embeddings_deleted += 1
                        except:
                            pass
                    
                    # Delete document
                    await session.execute(
                        delete(DocumentModel).where(DocumentModel.id == version.id)
                    )
                    deleted += 1
                    
                    if deleted % 100 == 0:
                        await session.commit()
                
                except Exception as e:
                    logger.error(f"Failed to delete version: {e}")
            
            await session.commit()
            
            logger.info(f"✅ Deleted {deleted} old versions, {embeddings_deleted} embeddings")
            
            return {
                "dry_run": False,
                "deleted": deleted,
                "embeddings_deleted": embeddings_deleted
            }
    
    async def get_cleanup_report(self) -> Dict[str, any]:
        """
        Generate a report of what can be cleaned up.
        
        Returns:
            Detailed cleanup report
        """
        logger.info("📊 Generating cleanup report...")
        
        async with get_database().session() as session:
            # Total documents
            total_result = await session.execute(
                select(DocumentModel)
            )
            total_docs = len(total_result.scalars().all())
            
            # Latest vs old
            latest_result = await session.execute(
                select(DocumentModel).where(DocumentModel.is_latest == True)
            )
            latest_count = len(latest_result.scalars().all())
            old_count = total_docs - latest_count
            
            # Analyze all documents
            analysis = await self.analyze_documents(include_latest=True)
            
            # Build report
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_documents": total_docs,
                "latest_versions": latest_count,
                "old_versions": old_count,
                "analysis": {
                    "by_priority": analysis["statistics"]["by_priority"],
                    "by_category": analysis["statistics"]["by_category"],
                    "cleanup_candidates": len(analysis["cleanup_candidates"])
                },
                "recommendations": []
            }
            
            # Generate recommendations
            skip_count = analysis["statistics"]["by_priority"].get("SKIP", 0)
            if skip_count > 0:
                report["recommendations"].append({
                    "action": "cleanup_low_value",
                    "count": skip_count,
                    "description": f"Remove {skip_count} low-value documents (logs, configs, build artifacts)",
                    "command": "cleanup_by_priority(min_priority='LOW')"
                })
            
            if old_count > 0:
                report["recommendations"].append({
                    "action": "cleanup_old_versions",
                    "count": old_count,
                    "description": f"Remove {old_count} old document versions (keep only latest)",
                    "command": "cleanup_old_versions()"
                })
            
            config_count = analysis["statistics"]["by_category"].get("configuration", 0)
            if config_count > 0:
                report["recommendations"].append({
                    "action": "cleanup_configs",
                    "count": config_count,
                    "description": f"Remove {config_count} configuration files (low RAG value)",
                    "command": "cleanup_by_category(['configuration'])"
                })
            
            return report
    
    def _estimate_space(self, candidates: List[Dict]) -> float:
        """
        Estimate space that would be freed (rough estimate).
        
        Args:
            candidates: List of cleanup candidates
        
        Returns:
            Estimated MB freed
        """
        # Rough estimate: 50KB per document + 3KB per embedding
        doc_size_kb = 50
        embedding_size_kb = 3
        
        total_kb = 0
        for candidate in candidates:
            total_kb += doc_size_kb
            if candidate.get("has_embedding"):
                total_kb += embedding_size_kb
        
        return round(total_kb / 1024, 2)  # Convert to MB


# ============================================================
# Convenience Functions
# ============================================================

async def cleanup_low_value_documents(dry_run: bool = True) -> Dict:
    """
    Clean up low-value documents (logs, configs, build artifacts).
    
    Args:
        dry_run: If True, only preview (default: True)
    
    Returns:
        Cleanup results
    """
    service = DocumentCleanupService()
    return await service.cleanup_documents(
        dry_run=dry_run,
        include_latest=True,
        min_priority=FilePriority.LOW
    )


async def cleanup_old_versions_only(dry_run: bool = True) -> Dict:
    """
    Clean up old document versions (keep latest only).
    
    Args:
        dry_run: If True, only preview (default: True)
    
    Returns:
        Cleanup results
    """
    service = DocumentCleanupService()
    return await service.cleanup_old_versions(dry_run=dry_run)


async def get_cleanup_recommendations() -> Dict:
    """
    Get recommendations for what can be cleaned up.
    
    Returns:
        Cleanup report with recommendations
    """
    service = DocumentCleanupService()
    return await service.get_cleanup_report()

