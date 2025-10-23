"""
Functional tests for temporal versioning with content-addressable storage.

These tests validate the hybrid versioning approach that combines
content-based hashing with temporal ordering for snapshot mode ingestion.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any
import hashlib

from src.models.document import DocumentModel, IngestionMode
from src.repositories.document_repository import DocumentRepository
from src.services.versioning.content_addressable_storage import ContentAddressableStorage
from src.services.versioning.temporal_version_manager import TemporalVersionManager
from tests.utils.test_helpers import create_test_document


pytestmark = pytest.mark.functional


@pytest.fixture
async def doc_repo(clean_database):
    """Document repository with test database."""
    return DocumentRepository(clean_database)


@pytest.fixture
async def cas_storage(clean_database):
    """Content-addressable storage with test database."""
    return ContentAddressableStorage(clean_database)


@pytest.fixture
async def version_manager(clean_database, cas_storage):
    """Temporal version manager with test database."""
    return TemporalVersionManager(clean_database, cas_storage)


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


class TestContentAddressableStorage:
    """Test content-addressable storage functionality."""

    async def test_store_content_with_hash(
        self,
        cas_storage,
        test_session_id
    ):
        """Test storing content with computed hash."""
        content = "# Test Document\n\nThis is test content."
        content_hash = compute_content_hash(content)

        # Store content
        stored = await cas_storage.store_content(
            content=content,
            file_path="test.md",
            test_session_id=test_session_id
        )

        assert stored is not None
        assert stored.content_hash == content_hash
        assert stored.normalized_content == content

    async def test_duplicate_content_same_hash(
        self,
        cas_storage,
        test_session_id
    ):
        """Test that duplicate content produces same hash."""
        content = "# Test Document\n\nDuplicate content."

        # Store same content twice
        doc1 = await cas_storage.store_content(
            content=content,
            file_path="test1.md",
            test_session_id=test_session_id
        )

        doc2 = await cas_storage.store_content(
            content=content,
            file_path="test2.md",
            test_session_id=test_session_id
        )

        # Should have same content hash
        assert doc1.content_hash == doc2.content_hash

    async def test_different_content_different_hash(
        self,
        cas_storage,
        test_session_id
    ):
        """Test that different content produces different hashes."""
        content1 = "# Document 1"
        content2 = "# Document 2"

        doc1 = await cas_storage.store_content(
            content=content1,
            file_path="doc1.md",
            test_session_id=test_session_id
        )

        doc2 = await cas_storage.store_content(
            content=content2,
            file_path="doc2.md",
            test_session_id=test_session_id
        )

        assert doc1.content_hash != doc2.content_hash

    async def test_retrieve_by_content_hash(
        self,
        cas_storage,
        test_session_id
    ):
        """Test retrieving content by hash."""
        content = "# Test Document"
        content_hash = compute_content_hash(content)

        # Store content
        await cas_storage.store_content(
            content=content,
            file_path="test.md",
            test_session_id=test_session_id
        )

        # Retrieve by hash
        retrieved = await cas_storage.get_by_content_hash(content_hash)

        assert retrieved is not None
        assert retrieved.normalized_content == content


class TestTemporalOrdering:
    """Test temporal ordering of documents."""

    async def test_temporal_version_increments(
        self,
        version_manager,
        test_session_id
    ):
        """Test that temporal versions increment."""
        file_path = "test.md"

        # Create multiple versions
        v1 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 1",
            test_session_id=test_session_id
        )

        v2 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 2",
            test_session_id=test_session_id
        )

        v3 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 3",
            test_session_id=test_session_id
        )

        # Versions should increment
        assert v2.version > v1.version
        assert v3.version > v2.version

    async def test_temporal_ordering_preserved(
        self,
        version_manager,
        test_session_id
    ):
        """Test that temporal ordering is preserved."""
        file_path = "test.md"

        # Create versions with delays
        v1 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 1",
            test_session_id=test_session_id
        )

        # Small delay
        await asyncio.sleep(0.1)

        v2 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 2",
            test_session_id=test_session_id
        )

        # Retrieve versions
        versions = await version_manager.get_versions(file_path)

        # Should be ordered by created_at
        assert versions[0].created_at < versions[1].created_at

    async def test_get_latest_version(
        self,
        version_manager,
        test_session_id
    ):
        """Test retrieving the latest version."""
        file_path = "test.md"

        # Create multiple versions
        for i in range(3):
            await version_manager.create_version(
                file_path=file_path,
                content=f"# Version {i+1}",
                test_session_id=test_session_id
            )

        # Get latest
        latest = await version_manager.get_latest_version(file_path)

        assert latest is not None
        assert latest.normalized_content == "# Version 3"


class TestHybridVersioning:
    """Test hybrid versioning (content hash + temporal ordering)."""

    async def test_same_content_different_timestamps(
        self,
        version_manager,
        test_session_id
    ):
        """Test that same content gets same hash but different timestamps."""
        content = "# Test Document"
        file_path = "test.md"

        # Create version 1
        v1 = await version_manager.create_version(
            file_path=file_path,
            content=content,
            test_session_id=test_session_id
        )

        # Wait a bit
        await asyncio.sleep(0.1)

        # Create version 2 with same content
        v2 = await version_manager.create_version(
            file_path=file_path,
            content=content,
            test_session_id=test_session_id
        )

        # Same content hash
        assert v1.content_hash == v2.content_hash

        # Different timestamps
        assert v2.created_at > v1.created_at

        # Different versions
        assert v2.version > v1.version

    async def test_content_deduplication(
        self,
        version_manager,
        cas_storage,
        test_session_id
    ):
        """Test that content is deduplicated."""
        content = "# Shared Content"

        # Create multiple documents with same content
        doc1 = await version_manager.create_version(
            file_path="doc1.md",
            content=content,
            test_session_id=test_session_id
        )

        doc2 = await version_manager.create_version(
            file_path="doc2.md",
            content=content,
            test_session_id=test_session_id
        )

        doc3 = await version_manager.create_version(
            file_path="doc3.md",
            content=content,
            test_session_id=test_session_id
        )

        # All should have same content hash
        assert doc1.content_hash == doc2.content_hash == doc3.content_hash

        # But different document IDs
        assert doc1.id != doc2.id != doc3.id

    async def test_version_history_reconstruction(
        self,
        version_manager,
        test_session_id
    ):
        """Test reconstructing version history."""
        file_path = "evolving.md"

        # Create version history
        contents = [
            "# Version 1\n\nInitial content",
            "# Version 2\n\nAdded features",
            "# Version 3\n\nBug fixes",
            "# Version 4\n\nPerformance improvements"
        ]

        for content in contents:
            await version_manager.create_version(
                file_path=file_path,
                content=content,
                test_session_id=test_session_id
            )

        # Get full history
        history = await version_manager.get_version_history(file_path)

        assert len(history) == 4
        # Should be ordered chronologically
        for i in range(len(history) - 1):
            assert history[i].created_at < history[i+1].created_at


class TestSnapshotModeIntegration:
    """Test integration with snapshot mode ingestion."""

    async def test_snapshot_ingestion_creates_versions(
        self,
        version_manager,
        test_session_id
    ):
        """Test that snapshot ingestion creates versions."""
        # Simulate snapshot ingestion
        files = [
            ("file1.py", "def hello(): pass"),
            ("file2.py", "def world(): pass"),
            ("file3.py", "def test(): pass")
        ]

        versions = []
        for file_path, content in files:
            version = await version_manager.create_version(
                file_path=file_path,
                content=content,
                ingestion_mode=IngestionMode.SNAPSHOT,
                test_session_id=test_session_id
            )
            versions.append(version)

        # All should be marked as snapshot mode
        assert all(v.ingestion_mode == IngestionMode.SNAPSHOT for v in versions)

    async def test_snapshot_without_git_history(
        self,
        version_manager,
        test_session_id
    ):
        """Test snapshot mode without git history."""
        file_path = "snapshot.md"
        content = "# Snapshot Content"

        # Create snapshot version (no commit info)
        version = await version_manager.create_version(
            file_path=file_path,
            content=content,
            ingestion_mode=IngestionMode.SNAPSHOT,
            commit_sha=None,  # No git info
            test_session_id=test_session_id
        )

        assert version.ingestion_mode == IngestionMode.SNAPSHOT
        assert version.commit_sha is None
        assert version.content_hash is not None  # Content hash exists

    async def test_hybrid_mode_with_git_info(
        self,
        version_manager,
        test_session_id
    ):
        """Test hybrid mode with git information."""
        file_path = "hybrid.md"
        content = "# Hybrid Content"
        commit_sha = "abc123"

        # Create version with git info
        version = await version_manager.create_version(
            file_path=file_path,
            content=content,
            ingestion_mode=IngestionMode.GIT_HISTORY,
            commit_sha=commit_sha,
            test_session_id=test_session_id
        )

        assert version.ingestion_mode == IngestionMode.GIT_HISTORY
        assert version.commit_sha == commit_sha
        assert version.content_hash is not None


class TestVersionComparison:
    """Test comparing versions."""

    async def test_compare_versions_by_content(
        self,
        version_manager,
        test_session_id
    ):
        """Test comparing versions by content."""
        file_path = "test.md"

        # Create two versions
        v1 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 1\n\nOriginal content",
            test_session_id=test_session_id
        )

        v2 = await version_manager.create_version(
            file_path=file_path,
            content="# Version 2\n\nModified content",
            test_session_id=test_session_id
        )

        # Compare versions
        diff = await version_manager.compare_versions(v1.id, v2.id)

        assert diff is not None
        assert "additions" in diff or "deletions" in diff

    async def test_detect_content_changes(
        self,
        version_manager,
        test_session_id
    ):
        """Test detecting content changes."""
        file_path = "test.md"
        content1 = "# Original"
        content2 = "# Modified"

        v1 = await version_manager.create_version(
            file_path=file_path,
            content=content1,
            test_session_id=test_session_id
        )

        v2 = await version_manager.create_version(
            file_path=file_path,
            content=content2,
            test_session_id=test_session_id
        )

        # Detect changes
        has_changes = await version_manager.has_content_changed(v1.id, v2.id)

        assert has_changes is True

    async def test_no_changes_same_content(
        self,
        version_manager,
        test_session_id
    ):
        """Test detecting no changes for same content."""
        file_path = "test.md"
        content = "# Same Content"

        v1 = await version_manager.create_version(
            file_path=file_path,
            content=content,
            test_session_id=test_session_id
        )

        v2 = await version_manager.create_version(
            file_path=file_path,
            content=content,
            test_session_id=test_session_id
        )

        # Should have same content hash
        assert v1.content_hash == v2.content_hash

        # No content changes
        has_changes = await version_manager.has_content_changed(v1.id, v2.id)
        assert has_changes is False


class TestVersionCleanup:
    """Test version cleanup and maintenance."""

    async def test_cleanup_old_versions(
        self,
        version_manager,
        test_session_id
    ):
        """Test cleaning up old versions."""
        file_path = "test.md"

        # Create old version
        old_version = await version_manager.create_version(
            file_path=file_path,
            content="# Old Version",
            test_session_id=test_session_id
        )

        # Manually set created_at to 91 days ago
        await version_manager.update_version_timestamp(
            old_version.id,
            datetime.utcnow() - timedelta(days=91)
        )

        # Create recent version
        recent_version = await version_manager.create_version(
            file_path=file_path,
            content="# Recent Version",
            test_session_id=test_session_id
        )

        # Cleanup versions older than 90 days
        deleted_count = await version_manager.cleanup_old_versions(days=90)

        assert deleted_count >= 1

        # Old version should be deleted
        old_retrieved = await version_manager.get_version(old_version.id)
        assert old_retrieved is None

        # Recent version should still exist
        recent_retrieved = await version_manager.get_version(recent_version.id)
        assert recent_retrieved is not None

    async def test_keep_minimum_versions(
        self,
        version_manager,
        test_session_id
    ):
        """Test keeping minimum number of versions."""
        file_path = "test.md"

        # Create multiple old versions
        for i in range(5):
            version = await version_manager.create_version(
                file_path=file_path,
                content=f"# Version {i+1}",
                test_session_id=test_session_id
            )

            # Make them old
            await version_manager.update_version_timestamp(
                version.id,
                datetime.utcnow() - timedelta(days=100)
            )

        # Cleanup but keep minimum 2 versions
        await version_manager.cleanup_old_versions(days=90, keep_minimum=2)

        # Should have at least 2 versions remaining
        remaining = await version_manager.get_versions(file_path)
        assert len(remaining) >= 2


class TestVersionMetadata:
    """Test version metadata."""

    async def test_store_version_metadata(
        self,
        version_manager,
        test_session_id
    ):
        """Test storing metadata with versions."""
        version = await version_manager.create_version(
            file_path="test.md",
            content="# Test",
            metadata={
                "author": "test_user",
                "tags": ["test", "functional"],
                "size_bytes": 100
            },
            test_session_id=test_session_id
        )

        assert version.metadata["author"] == "test_user"
        assert "test" in version.metadata["tags"]

    async def test_query_by_metadata(
        self,
        version_manager,
        test_session_id
    ):
        """Test querying versions by metadata."""
        # Create versions with different metadata
        await version_manager.create_version(
            file_path="test1.md",
            content="# Test 1",
            metadata={"category": "api"},
            test_session_id=test_session_id
        )

        await version_manager.create_version(
            file_path="test2.md",
            content="# Test 2",
            metadata={"category": "architecture"},
            test_session_id=test_session_id
        )

        # Query by metadata
        api_versions = await version_manager.query_by_metadata(
            {"category": "api"}
        )

        assert len(api_versions) >= 1
        assert all(v.metadata.get("category") == "api" for v in api_versions)

