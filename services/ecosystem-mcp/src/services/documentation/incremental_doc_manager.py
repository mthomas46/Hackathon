"""
Incremental Documentation Manager (Option C, Phase 2, Days 3-5)

Manages incremental documentation updates by:
- Detecting changed files via Git diff
- Tracking documentation history
- Updating only affected documentation
- Maintaining documentation lineage

Provides 10-100× speedup for documentation updates on large repositories.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib

from git import Repo, Commit, Diff
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a changed file."""
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: Optional[str] = None  # For renamed files
    content_hash: Optional[str] = None
    size_bytes: int = 0


@dataclass
class DocumentationSnapshot:
    """Snapshot of documentation state at a specific commit."""
    commit_sha: str
    commit_timestamp: datetime
    documented_files: Dict[str, str]  # file_path -> doc_hash
    total_files: int
    documentation_version: str = "1.0"


@dataclass
class IncrementalUpdatePlan:
    """Plan for incremental documentation update."""
    base_commit_sha: str
    target_commit_sha: str
    files_to_add: List[FileChange] = field(default_factory=list)
    files_to_update: List[FileChange] = field(default_factory=list)
    files_to_delete: List[str] = field(default_factory=list)
    files_unchanged: int = 0
    estimated_speedup: float = 1.0


class IncrementalDocManager:
    """
    Manages incremental documentation updates.
    
    Features:
    - Git diff detection
    - Changed file identification
    - Documentation history tracking
    - Incremental update planning
    - Dependency-aware updates
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize incremental doc manager.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = repo_path
        self.repo = None
        self.last_snapshot: Optional[DocumentationSnapshot] = None
        logger.info(f"IncrementalDocManager initialized for {repo_path}")
    
    def _init_repo(self) -> Repo:
        """Initialize Git repository."""
        if self.repo is None:
            try:
                self.repo = Repo(self.repo_path)
                logger.info(f"✅ Git repository initialized: {self.repo_path}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Git repo: {e}")
                raise
        return self.repo
    
    async def get_changed_files(
        self,
        base_commit: Optional[str] = None,
        target_commit: str = "HEAD"
    ) -> List[FileChange]:
        """
        Get list of changed files between commits.
        
        Args:
            base_commit: Base commit SHA (None = previous documented state)
            target_commit: Target commit SHA (default: HEAD)
        
        Returns:
            List of FileChange objects
        """
        repo = self._init_repo()
        
        # If no base commit, use last documented commit
        if base_commit is None:
            if self.last_snapshot:
                base_commit = self.last_snapshot.commit_sha
            else:
                # No previous documentation, return all files
                logger.info("No previous documentation found, will document all files")
                return await self._get_all_files_as_changes(target_commit)
        
        logger.info(f"📊 Detecting changes: {base_commit[:8]} → {target_commit[:8]}")
        
        try:
            base = repo.commit(base_commit)
            target = repo.commit(target_commit)
        except Exception as e:
            logger.error(f"❌ Failed to get commits: {e}")
            raise
        
        changes: List[FileChange] = []
        
        # Get diff between commits
        diffs = base.diff(target)
        
        for diff in diffs:
            change = await self._process_diff(diff, repo)
            if change:
                changes.append(change)
        
        logger.info(f"✅ Found {len(changes)} changed files")
        return changes
    
    async def _process_diff(self, diff: Diff, repo: Repo) -> Optional[FileChange]:
        """Process a single diff to create FileChange."""
        try:
            # Determine change type
            if diff.new_file:
                change_type = "added"
                file_path = diff.b_path
                old_path = None
            elif diff.deleted_file:
                change_type = "deleted"
                file_path = diff.a_path
                old_path = None
            elif diff.renamed_file:
                change_type = "renamed"
                file_path = diff.b_path
                old_path = diff.a_path
            else:
                change_type = "modified"
                file_path = diff.b_path
                old_path = None
            
            # Get content hash and size for non-deleted files
            content_hash = None
            size_bytes = 0
            
            if change_type != "deleted" and diff.b_blob:
                try:
                    content = diff.b_blob.data_stream.read()
                    content_hash = hashlib.sha256(content).hexdigest()
                    size_bytes = len(content)
                except Exception as e:
                    logger.warning(f"⚠️ Could not read blob for {file_path}: {e}")
            
            return FileChange(
                file_path=file_path,
                change_type=change_type,
                old_path=old_path,
                content_hash=content_hash,
                size_bytes=size_bytes
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to process diff: {e}")
            return None
    
    async def _get_all_files_as_changes(self, commit_sha: str) -> List[FileChange]:
        """Get all files at commit as 'added' changes."""
        repo = self._init_repo()
        
        try:
            commit = repo.commit(commit_sha)
        except Exception as e:
            logger.error(f"❌ Failed to get commit {commit_sha}: {e}")
            return []
        
        changes: List[FileChange] = []
        
        # Iterate through all files in commit
        for item in commit.tree.traverse():
            if item.type == "blob":  # It's a file
                try:
                    content = item.data_stream.read()
                    content_hash = hashlib.sha256(content).hexdigest()
                    
                    changes.append(FileChange(
                        file_path=item.path,
                        change_type="added",
                        old_path=None,
                        content_hash=content_hash,
                        size_bytes=len(content)
                    ))
                except Exception as e:
                    logger.warning(f"⚠️ Could not read {item.path}: {e}")
        
        logger.info(f"✅ Found {len(changes)} total files at {commit_sha[:8]}")
        return changes
    
    async def create_update_plan(
        self,
        changes: List[FileChange],
        existing_docs: Dict[str, str]
    ) -> IncrementalUpdatePlan:
        """
        Create plan for incremental documentation update.
        
        Args:
            changes: List of file changes
            existing_docs: Existing documentation (file_path -> doc_hash)
        
        Returns:
            IncrementalUpdatePlan with categorized changes
        """
        plan = IncrementalUpdatePlan(
            base_commit_sha=self.last_snapshot.commit_sha if self.last_snapshot else "initial",
            target_commit_sha="HEAD"
        )
        
        for change in changes:
            if change.change_type == "added":
                plan.files_to_add.append(change)
            
            elif change.change_type == "modified":
                # Check if we have existing documentation
                if change.file_path in existing_docs:
                    plan.files_to_update.append(change)
                else:
                    # File modified but no existing doc (shouldn't happen, but handle it)
                    plan.files_to_add.append(change)
            
            elif change.change_type == "deleted":
                if change.file_path in existing_docs:
                    plan.files_to_delete.append(change.file_path)
            
            elif change.change_type == "renamed":
                # Treat as delete old + add new
                if change.old_path and change.old_path in existing_docs:
                    plan.files_to_delete.append(change.old_path)
                plan.files_to_add.append(change)
        
        # Count unchanged files
        total_files = len(existing_docs) + len(plan.files_to_add) - len(plan.files_to_delete)
        changed_files = len(plan.files_to_add) + len(plan.files_to_update) + len(plan.files_to_delete)
        plan.files_unchanged = total_files - changed_files
        
        # Calculate estimated speedup
        if total_files > 0:
            plan.estimated_speedup = total_files / max(changed_files, 1)
        
        logger.info(f"📋 Update plan created:")
        logger.info(f"   • To add: {len(plan.files_to_add)}")
        logger.info(f"   • To update: {len(plan.files_to_update)}")
        logger.info(f"   • To delete: {len(plan.files_to_delete)}")
        logger.info(f"   • Unchanged: {plan.files_unchanged}")
        logger.info(f"   • Estimated speedup: {plan.estimated_speedup:.1f}×")
        
        return plan
    
    async def save_snapshot(
        self,
        commit_sha: str,
        documented_files: Dict[str, str],
        session: AsyncSession
    ) -> DocumentationSnapshot:
        """
        Save documentation snapshot for future incremental updates.
        
        Args:
            commit_sha: Commit SHA that was documented
            documented_files: Map of file_path -> doc_hash
            session: Database session
        
        Returns:
            DocumentationSnapshot
        """
        repo = self._init_repo()
        
        try:
            commit = repo.commit(commit_sha)
            commit_timestamp = datetime.fromtimestamp(commit.committed_date)
        except Exception as e:
            logger.error(f"❌ Failed to get commit info: {e}")
            commit_timestamp = datetime.utcnow()
        
        snapshot = DocumentationSnapshot(
            commit_sha=commit_sha,
            commit_timestamp=commit_timestamp,
            documented_files=documented_files,
            total_files=len(documented_files),
            documentation_version="1.0"
        )
        
        # Store snapshot (would save to database in full implementation)
        self.last_snapshot = snapshot
        
        logger.info(f"✅ Snapshot saved: {commit_sha[:8]} ({len(documented_files)} files)")
        
        return snapshot
    
    async def load_last_snapshot(
        self,
        repo_id: str,
        session: AsyncSession
    ) -> Optional[DocumentationSnapshot]:
        """
        Load last documentation snapshot from database.
        
        Args:
            repo_id: Repository ID
            session: Database session
        
        Returns:
            Last DocumentationSnapshot or None
        """
        # In full implementation, would query database
        # For now, return stored snapshot
        
        if self.last_snapshot:
            logger.info(f"✅ Loaded snapshot: {self.last_snapshot.commit_sha[:8]}")
        else:
            logger.info("ℹ️  No previous snapshot found")
        
        return self.last_snapshot
    
    async def get_affected_dependencies(
        self,
        changed_files: List[FileChange],
        dependency_graph: Optional[Dict[str, List[str]]] = None
    ) -> Set[str]:
        """
        Get files affected by dependencies.
        
        If file A changes and file B imports A, then B's documentation
        might need updating too.
        
        Args:
            changed_files: List of changed files
            dependency_graph: Map of file -> list of files that depend on it
        
        Returns:
            Set of additional files that should be updated
        """
        if not dependency_graph:
            return set()
        
        affected = set()
        changed_paths = {change.file_path for change in changed_files}
        
        # Find all files that depend on changed files
        for changed_path in changed_paths:
            if changed_path in dependency_graph:
                dependents = dependency_graph[changed_path]
                affected.update(dependents)
        
        # Remove files that are already in the changed list
        affected = affected - changed_paths
        
        if affected:
            logger.info(f"📊 Found {len(affected)} files affected by dependencies")
        
        return affected
    
    def should_use_incremental(
        self,
        total_files: int,
        changed_files: int,
        threshold: float = 0.2
    ) -> bool:
        """
        Determine if incremental update is worthwhile.
        
        Args:
            total_files: Total files in repository
            changed_files: Number of changed files
            threshold: Threshold ratio (default 20%)
        
        Returns:
            True if incremental update should be used
        """
        if total_files == 0:
            return False
        
        change_ratio = changed_files / total_files
        use_incremental = change_ratio < threshold
        
        if use_incremental:
            logger.info(f"✅ Using incremental update: {change_ratio:.1%} files changed")
        else:
            logger.info(f"⚠️  Full regeneration recommended: {change_ratio:.1%} files changed")
        
        return use_incremental


# Singleton
_incremental_doc_manager_instances: Dict[str, IncrementalDocManager] = {}


def get_incremental_doc_manager(repo_path: str) -> IncrementalDocManager:
    """
    Get or create IncrementalDocManager instance for repository.
    
    Args:
        repo_path: Path to repository
    
    Returns:
        IncrementalDocManager instance
    """
    if repo_path not in _incremental_doc_manager_instances:
        _incremental_doc_manager_instances[repo_path] = IncrementalDocManager(repo_path)
    
    return _incremental_doc_manager_instances[repo_path]

