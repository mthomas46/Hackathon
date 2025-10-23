"""
Version Comparator Service

Compares document versions:
- Compare two versions of a document
- Show diff, what changed, when, why
- Track content evolution
- Integration with git history
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
import difflib

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import DocumentModel, GitCommitModel
from ...storage.repositories import DocumentRepository
from ...storage import get_database

logger = logging.getLogger(__name__)


class VersionDiff:
    """Represents a difference between two versions."""
    
    def __init__(
        self,
        change_type: str,  # added, removed, modified
        line_number: int,
        old_content: Optional[str],
        new_content: Optional[str]
    ):
        self.change_type = change_type
        self.line_number = line_number
        self.old_content = old_content
        self.new_content = new_content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "line_number": self.line_number,
            "old_content": self.old_content,
            "new_content": self.new_content
        }


class VersionComparator:
    """
    Compare document versions.
    
    Features:
    - Side-by-side comparison
    - Unified diff
    - Change statistics
    - Semantic change detection
    - Git history integration
    """
    
    def __init__(self):
        """Initialize version comparator."""
        self.logger = logging.getLogger(__name__)
    
    async def compare_versions(
        self,
        document_id: UUID,
        version1_date: datetime,
        version2_date: datetime
    ) -> Dict[str, Any]:
        """
        Compare two versions of a document.
        
        Args:
            document_id: Document to compare
            version1_date: Date of first version
            version2_date: Date of second version
        
        Returns:
            Comparison results with diff and statistics
        """
        try:
            self.logger.info(
                f"⚖️ Comparing versions of document {document_id} "
                f"({version1_date.date()} vs {version2_date.date()})"
            )
            
            # Get document versions
            version1 = await self._get_document_version(document_id, version1_date)
            version2 = await self._get_document_version(document_id, version2_date)
            
            if not version1 or not version2:
                return {
                    "error": "Could not retrieve both versions",
                    "version1_found": version1 is not None,
                    "version2_found": version2 is not None
                }
            
            # Generate diff
            diff_result = self._generate_diff(
                version1["content"],
                version2["content"]
            )
            
            # Calculate statistics
            stats = self._calculate_change_stats(diff_result)
            
            # Detect semantic changes
            semantic_changes = self._detect_semantic_changes(diff_result)
            
            return {
                "document_id": str(document_id),
                "version1": {
                    "date": version1["date"].isoformat(),
                    "commit": version1.get("commit")
                },
                "version2": {
                    "date": version2["date"].isoformat(),
                    "commit": version2.get("commit")
                },
                "diff": {
                    "unified": diff_result["unified"],
                    "changes": [d.to_dict() for d in diff_result["changes"]]
                },
                "statistics": stats,
                "semantic_changes": semantic_changes,
                "metadata": {
                    "compared_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compare versions: {e}", exc_info=True)
            raise
    
    async def _get_document_version(
        self,
        document_id: UUID,
        target_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get document content at a specific date."""
        # This is a simplified version
        # In production, you'd query git history or stored versions
        
        async with get_database().session() as session:
            doc_repo = DocumentRepository(session)
            doc = await doc_repo.get_by_id(document_id)
            
            if not doc:
                return None
            
            # For now, return current version (simplified)
            # In production, you'd use git history or version storage
            return {
                "date": doc.updated_at or doc.created_at,
                "content": doc.normalized_content or "",
                "commit": None
            }
    
    def _generate_diff(
        self,
        content1: str,
        content2: str
    ) -> Dict[str, Any]:
        """Generate diff between two content strings."""
        lines1 = content1.splitlines(keepends=True)
        lines2 = content2.splitlines(keepends=True)
        
        # Generate unified diff
        unified_diff = list(difflib.unified_diff(
            lines1,
            lines2,
            lineterm='',
            n=3  # context lines
        ))
        
        # Parse diff to extract changes
        changes = []
        line_num = 0
        
        for line in unified_diff:
            if line.startswith('+++') or line.startswith('---'):
                continue
            elif line.startswith('@@'):
                # Parse line numbers from @@ -l1,s1 +l2,s2 @@
                continue
            elif line.startswith('+'):
                changes.append(VersionDiff(
                    change_type="added",
                    line_number=line_num,
                    old_content=None,
                    new_content=line[1:].strip()
                ))
                line_num += 1
            elif line.startswith('-'):
                changes.append(VersionDiff(
                    change_type="removed",
                    line_number=line_num,
                    old_content=line[1:].strip(),
                    new_content=None
                ))
            else:
                line_num += 1
        
        return {
            "unified": '\n'.join(unified_diff),
            "changes": changes
        }
    
    def _calculate_change_stats(
        self,
        diff_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate change statistics."""
        changes = diff_result["changes"]
        
        added = [c for c in changes if c.change_type == "added"]
        removed = [c for c in changes if c.change_type == "removed"]
        modified = [c for c in changes if c.change_type == "modified"]
        
        total_changes = len(changes)
        
        return {
            "total_changes": total_changes,
            "lines_added": len(added),
            "lines_removed": len(removed),
            "lines_modified": len(modified),
            "change_percentage": self._calculate_change_percentage(
                diff_result["unified"]
            )
        }
    
    def _calculate_change_percentage(self, unified_diff: str) -> float:
        """Calculate percentage of content that changed."""
        if not unified_diff:
            return 0.0
        
        lines = unified_diff.splitlines()
        changed_lines = sum(1 for line in lines if line.startswith(('+', '-')))
        total_lines = len(lines)
        
        if total_lines == 0:
            return 0.0
        
        return round((changed_lines / total_lines) * 100, 2)
    
    def _detect_semantic_changes(
        self,
        diff_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect semantic changes (simplified)."""
        semantic_changes = []
        
        changes = diff_result["changes"]
        
        # Look for specific patterns that indicate semantic changes
        for change in changes:
            content = change.new_content if change.change_type == "added" else change.old_content
            
            if not content:
                continue
            
            # Detect API changes
            if "def " in content or "class " in content or "function " in content:
                semantic_changes.append({
                    "type": "api_change",
                    "change_type": change.change_type,
                    "description": f"API definition {change.change_type}",
                    "line": change.line_number
                })
            
            # Detect configuration changes
            elif any(keyword in content.lower() for keyword in ["config", "setting", "parameter"]):
                semantic_changes.append({
                    "type": "configuration_change",
                    "change_type": change.change_type,
                    "description": f"Configuration {change.change_type}",
                    "line": change.line_number
                })
            
            # Detect deprecation notices
            elif "deprecated" in content.lower() or "obsolete" in content.lower():
                semantic_changes.append({
                    "type": "deprecation",
                    "change_type": change.change_type,
                    "description": "Deprecation notice",
                    "line": change.line_number
                })
        
        return semantic_changes
    
    async def get_version_history(
        self,
        document_id: UUID,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get version history for a document.
        
        Args:
            document_id: Document to query
            limit: Maximum versions to return
        
        Returns:
            Version history
        """
        try:
            self.logger.info(f"📚 Getting version history for document {document_id}")
            
            async with get_database().session() as session:
                doc_repo = DocumentRepository(session)
                doc = await doc_repo.get_by_id(document_id)
                
                if not doc:
                    raise ValueError(f"Document not found: {document_id}")
                
                # This is a placeholder - in production, you'd:
                # 1. Query git history for this file
                # 2. Return list of commits with dates and messages
                
                return {
                    "document_id": str(document_id),
                    "file_path": doc.file_path,
                    "versions": [
                        {
                            "date": (doc.updated_at or doc.created_at).isoformat(),
                            "commit": None,
                            "message": "Current version",
                            "author": doc.service_name
                        }
                    ],
                    "note": "Full git history integration requires git repository access"
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get version history: {e}", exc_info=True)
            raise
    
    async def compare_with_previous(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Compare document with its previous version.
        
        Args:
            document_id: Document to compare
        
        Returns:
            Comparison with previous version
        """
        try:
            self.logger.info(f"⏮️ Comparing document {document_id} with previous version")
            
            # Get version history
            history = await self.get_version_history(document_id, limit=2)
            
            if len(history["versions"]) < 2:
                return {
                    "document_id": str(document_id),
                    "message": "No previous version available for comparison"
                }
            
            # Compare current with previous
            # This is simplified - in production, you'd use actual version data
            return {
                "document_id": str(document_id),
                "current_version": history["versions"][0],
                "previous_version": history["versions"][1],
                "note": "Comparison requires access to historical versions"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to compare with previous: {e}", exc_info=True)
            raise

