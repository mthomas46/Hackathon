"""
Git service for retrieving file history and commit information.

Integrates with local git repository to track document versions.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import git

from ...models.git_commit import GitCommit, GitCommitMetadata, FileChange
from ...config import settings

logger = logging.getLogger(__name__)


class GitService:
    """
    Git integration service.
    
    Provides access to git history for document versioning.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize git service.
        
        Args:
            repo_path: Path to git repository (uses settings if None)
        """
        self.repo_path = Path(repo_path or str(settings.git_repo_path))
        
        try:
            self.repo = git.Repo(self.repo_path)
            logger.info(f"Git service initialized: {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {self.repo_path}")
            from ...utils.exceptions import ValidationError
            raise ValidationError(f"Not a git repository: {self.repo_path}")
    
    async def get_file_history(
        self,
        file_path: str,
        max_commits: int = 100
    ) -> List[GitCommit]:
        """
        Get commit history for a specific file.
        
        Uses --follow to track file through renames.
        
        Args:
            file_path: Relative path to file
            max_commits: Maximum number of commits to retrieve
        
        Returns:
            List of GitCommit objects in reverse chronological order
        """
        return await asyncio.to_thread(
            self._get_file_history_sync,
            file_path,
            max_commits
        )
    
    def _get_file_history_sync(
        self,
        file_path: str,
        max_commits: int
    ) -> List[GitCommit]:
        """Synchronous implementation of get_file_history."""
        commits = []
        
        try:
            # Get commits that modified this file
            # Using --follow to track renames
            for commit in self.repo.iter_commits(
                paths=file_path,
                max_count=max_commits
            ):
                git_commit = self._commit_to_model(commit, file_path)
                commits.append(git_commit)
        except git.GitCommandError as e:
            logger.error(f"Git error getting history for {file_path}: {e}")
        
        return commits
    
    async def get_file_content_at_commit(
        self,
        commit_sha: str,
        file_path: str
    ) -> Optional[str]:
        """
        Get file content at specific commit.
        
        Alias for get_file_at_commit with swapped parameter order.
        
        Args:
            commit_sha: Git commit SHA
            file_path: Relative path to file
        
        Returns:
            File content or None if not found
        """
        return await self.get_file_at_commit(file_path, commit_sha)
    
    async def get_file_at_commit(
        self,
        file_path: str,
        commit_sha: str
    ) -> Optional[str]:
        """
        Get file content at specific commit.
        
        Args:
            file_path: Relative path to file
            commit_sha: Git commit SHA
        
        Returns:
            File content or None if not found
        """
        return await asyncio.to_thread(
            self._get_file_at_commit_sync,
            file_path,
            commit_sha
        )
    
    def _get_file_at_commit_sync(
        self,
        file_path: str,
        commit_sha: str
    ) -> Optional[str]:
        """Synchronous implementation of get_file_at_commit."""
        try:
            commit = self.repo.commit(commit_sha)
            
            # Get file content from commit
            try:
                content = (commit.tree / file_path).data_stream.read()
                return content.decode('utf-8')
            except KeyError:
                # File doesn't exist at this commit
                logger.warning(f"File {file_path} not found at commit {commit_sha}")
                return None
        except git.BadName:
            logger.error(f"Invalid commit SHA: {commit_sha}")
            return None
    
    async def get_commit_metadata(
        self,
        commit_sha: str
    ) -> Optional[GitCommit]:
        """
        Get detailed metadata for a commit.
        
        Args:
            commit_sha: Git commit SHA
        
        Returns:
            GitCommit object or None if not found
        """
        return await asyncio.to_thread(
            self._get_commit_metadata_sync,
            commit_sha
        )
    
    def _get_commit_metadata_sync(
        self,
        commit_sha: str
    ) -> Optional[GitCommit]:
        """Synchronous implementation of get_commit_metadata."""
        try:
            commit = self.repo.commit(commit_sha)
            return self._commit_to_model(commit)
        except git.BadName:
            logger.error(f"Invalid commit SHA: {commit_sha}")
            return None
    
    async def get_all_commits(
        self,
        max_count: Optional[int] = None
    ) -> List[GitCommit]:
        """
        Get all commits in repository.
        
        Args:
            max_count: Maximum number of commits (None = all)
        
        Returns:
            List of commits in reverse chronological order
        """
        return await asyncio.to_thread(
            self._get_all_commits_sync,
            max_count
        )
    
    async def get_recent_commits(
        self,
        limit: int = 10
    ) -> List[GitCommit]:
        """
        Get recent commits in repository.
        
        Alias for get_all_commits with a limit.
        
        Args:
            limit: Maximum number of commits to return
        
        Returns:
            List of recent commits in reverse chronological order
        """
        return await self.get_all_commits(max_count=limit)
    
    def _get_all_commits_sync(
        self,
        max_count: Optional[int]
    ) -> List[GitCommit]:
        """Synchronous implementation of get_all_commits."""
        commits = []
        
        for commit in self.repo.iter_commits(max_count=max_count):
            git_commit = self._commit_to_model(commit)
            commits.append(git_commit)
        
        return commits
    
    async def get_commit_files(
        self,
        commit_sha: str
    ) -> List[str]:
        """
        Get list of all files at a specific commit.
        
        Alias for get_files_at_commit.
        
        Args:
            commit_sha: Git commit SHA
        
        Returns:
            List of file paths
        """
        return await self.get_files_at_commit(commit_sha)
    
    async def get_files_at_commit(
        self,
        commit_sha: str
    ) -> List[str]:
        """
        Get list of all files at a specific commit.
        
        Args:
            commit_sha: Git commit SHA
        
        Returns:
            List of file paths
        """
        return await asyncio.to_thread(
            self._get_files_at_commit_sync,
            commit_sha
        )
    
    def _get_files_at_commit_sync(
        self,
        commit_sha: str
    ) -> List[str]:
        """Synchronous implementation of get_files_at_commit."""
        try:
            commit = self.repo.commit(commit_sha)
            files = []
            
            for item in commit.tree.traverse():
                if item.type == 'blob':  # File (not directory)
                    files.append(item.path)
            
            return files
        except git.BadName:
            logger.error(f"Invalid commit SHA: {commit_sha}")
            return []
    
    def _commit_to_model(
        self,
        commit: git.Commit,
        file_path: Optional[str] = None
    ) -> GitCommit:
        """
        Convert git.Commit to GitCommit model.
        
        Args:
            commit: GitPython commit object
            file_path: Optional specific file path for stats
        
        Returns:
            GitCommit model
        """
        # Get commit stats
        stats = self._get_commit_stats(commit, file_path)
        
        # Get file changes
        file_changes = self._get_file_changes(commit)
        
        metadata = GitCommitMetadata(
            files_changed=stats['files_changed'],
            insertions=stats['insertions'],
            deletions=stats['deletions'],
            file_changes=file_changes
        )
        
        return GitCommit(
            sha=commit.hexsha,
            author=commit.author.name,
            author_email=commit.author.email,
            date=datetime.fromtimestamp(commit.committed_date),
            message=commit.message.strip(),
            metadata=metadata
        )
    
    def _get_commit_stats(
        self,
        commit: git.Commit,
        file_path: Optional[str] = None
    ) -> Dict[str, int]:
        """Get commit statistics."""
        try:
            if commit.parents:
                parent = commit.parents[0]
                diff = parent.diff(commit)
                
                if file_path:
                    # Filter for specific file
                    diff = [d for d in diff if d.a_path == file_path or d.b_path == file_path]
                
                files_changed = len(diff)
                insertions = sum(d.diff.decode('utf-8', errors='ignore').count('\n+') 
                               for d in diff if d.diff)
                deletions = sum(d.diff.decode('utf-8', errors='ignore').count('\n-') 
                              for d in diff if d.diff)
            else:
                # First commit
                files_changed = len(list(commit.tree.traverse()))
                insertions = 0
                deletions = 0
            
            return {
                'files_changed': files_changed,
                'insertions': insertions,
                'deletions': deletions
            }
        except Exception as e:
            logger.warning(f"Failed to get stats for commit {commit.hexsha}: {e}")
            return {'files_changed': 0, 'insertions': 0, 'deletions': 0}
    
    def _get_file_changes(
        self,
        commit: git.Commit
    ) -> List[FileChange]:
        """Get detailed file changes for commit."""
        changes = []
        
        try:
            if commit.parents:
                parent = commit.parents[0]
                diff = parent.diff(commit)
                
                for d in diff:
                    change_type = 'M'  # Modified
                    if d.new_file:
                        change_type = 'A'  # Added
                    elif d.deleted_file:
                        change_type = 'D'  # Deleted
                    elif d.renamed_file:
                        change_type = 'R'  # Renamed
                    
                    changes.append(FileChange(
                        path=d.b_path or d.a_path,
                        change_type=change_type,
                        insertions=0,  # Would need line-by-line parsing
                        deletions=0,
                        old_path=d.a_path if d.renamed_file else None
                    ))
        except Exception as e:
            logger.warning(f"Failed to get file changes for commit {commit.hexsha}: {e}")
        
        return changes[:50]  # Limit to avoid huge lists
    
    async def get_latest_commit_for_file(
        self,
        file_path: str
    ) -> Optional[GitCommit]:
        """
        Get the latest commit that modified a file.
        
        Args:
            file_path: Relative path to file
        
        Returns:
            GitCommit or None if not found
        """
        history = await self.get_file_history(file_path, max_commits=1)
        return history[0] if history else None


# Global instance
_git_service: Optional[GitService] = None


def get_git_service() -> GitService:
    """Get global git service instance."""
    global _git_service
    if _git_service is None:
        _git_service = GitService()
    return _git_service

