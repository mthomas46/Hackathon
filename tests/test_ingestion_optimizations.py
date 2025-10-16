"""
Tests for ingestion optimizations (commit-level and batch duplicate checking).
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.ecosystem_mcp.src.services.ingestion.commit_optimizer import CommitOptimizer, get_commit_optimizer
from services.ecosystem_mcp.src.storage.db_models import DocumentModel, GitCommitModel
from services.ecosystem_mcp.src.storage import get_database


@pytest.fixture
async def setup_test_data():
    """Set up test data in database."""
    db = get_database()
    
    async with db.session() as session:
        # Create a test commit
        test_commit = GitCommitModel(
            sha="abc123def456",
            message="Test commit",
            author="Test Author",
            author_email="test@example.com",
            date=datetime.utcnow(),
            commit_metadata={}
        )
        session.add(test_commit)
        await session.flush()
        
        # Create test documents
        docs = []
        for i in range(5):
            doc = DocumentModel(
                id=uuid4(),
                service_name="test-service",
                file_path=f"test/file{i}.py",
                original_format="py",
                original_content=f"content{i}",
                normalized_content=f"normalized{i}",
                content_hash=f"hash{i}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                git_commit_sha="abc123def456",
                is_latest=True,
                doc_metadata={}
            )
            session.add(doc)
            docs.append(doc)
        
        await session.commit()
        
        yield {
            "commit_sha": "abc123def456",
            "document_count": 5,
            "hashes": [f"hash{i}" for i in range(5)]
        }
        
        # Cleanup
        for doc in docs:
            await session.delete(doc)
        await session.delete(test_commit)
        await session.commit()


@pytest.mark.asyncio
async def test_commit_already_ingested(setup_test_data):
    """Test checking if a commit is already ingested."""
    optimizer = get_commit_optimizer()
    test_data = await setup_test_data
    
    # Check for ingested commit
    result = await optimizer.check_commit_already_ingested(test_data["commit_sha"])
    
    assert result["already_ingested"] is True
    assert result["document_count"] == test_data["document_count"]
    assert result["ingested_at"] is not None


@pytest.mark.asyncio
async def test_commit_not_ingested():
    """Test checking for a non-existent commit."""
    optimizer = get_commit_optimizer()
    
    # Check for non-existent commit
    result = await optimizer.check_commit_already_ingested("nonexistent123")
    
    assert result["already_ingested"] is False
    assert result["document_count"] == 0
    assert result["ingested_at"] is None


@pytest.mark.asyncio
async def test_batch_check_content_hashes(setup_test_data):
    """Test batch checking content hashes."""
    optimizer = get_commit_optimizer()
    test_data = await setup_test_data
    
    # Check existing hashes
    test_hashes = test_data["hashes"] + ["newhas h1", "newhash2"]
    existing = await optimizer.batch_check_content_hashes(test_hashes)
    
    # Should find all existing hashes
    for hash_val in test_data["hashes"]:
        assert hash_val in existing
    
    # Should not find new hashes
    assert "newhash1" not in existing
    assert "newhash2" not in existing


@pytest.mark.asyncio
async def test_batch_check_empty_list():
    """Test batch checking with empty list."""
    optimizer = get_commit_optimizer()
    
    existing = await optimizer.batch_check_content_hashes([])
    
    assert len(existing) == 0


@pytest.mark.asyncio
async def test_single_hash_check(setup_test_data):
    """Test checking a single content hash."""
    optimizer = get_commit_optimizer()
    test_data = await setup_test_data
    
    # Check existing hash
    exists = await optimizer.check_content_hash_exists(test_data["hashes"][0])
    assert exists is True
    
    # Check non-existent hash
    exists = await optimizer.check_content_hash_exists("nonexistenthash")
    assert exists is False


@pytest.mark.asyncio
async def test_get_commit_statistics(setup_test_data):
    """Test getting commit statistics."""
    optimizer = get_commit_optimizer()
    await setup_test_data
    
    stats = await optimizer.get_commit_statistics()
    
    assert stats["unique_commits"] >= 1
    assert stats["total_documents"] >= 5
    assert stats["last_ingestion"] is not None


@pytest.mark.asyncio
async def test_optimize_file_list():
    """Test optimizing a file list with batch checking."""
    optimizer = get_commit_optimizer()
    
    # Create test file list
    files = [
        {"file_path": "test1.py", "content": "content1", "content_hash": "newhash1"},
        {"file_path": "test2.py", "content": "content2", "content_hash": "newhash2"},
        {"file_path": "test3.py", "content": "content3", "content_hash": "newhash3"},
    ]
    
    result = await optimizer.optimize_file_list(files, "testcommit123")
    
    # All should be new (not duplicates)
    assert len(result["files_to_process"]) == 3
    assert len(result["files_to_skip"]) == 0
    assert result["duplicate_percentage"] == 0.0
    assert result["optimization_time_ms"] > 0


@pytest.mark.asyncio
async def test_optimize_file_list_with_duplicates(setup_test_data):
    """Test optimizing a file list that includes duplicates."""
    optimizer = get_commit_optimizer()
    test_data = await setup_test_data
    
    # Mix of new and existing hashes
    files = [
        {"file_path": "new1.py", "content": "new1", "content_hash": "newhash1"},
        {"file_path": "dup1.py", "content": "dup1", "content_hash": test_data["hashes"][0]},
        {"file_path": "new2.py", "content": "new2", "content_hash": "newhash2"},
        {"file_path": "dup2.py", "content": "dup2", "content_hash": test_data["hashes"][1]},
    ]
    
    result = await optimizer.optimize_file_list(files, "testcommit123")
    
    # Should separate new from duplicates
    assert len(result["files_to_process"]) == 2
    assert len(result["files_to_skip"]) == 2
    assert result["duplicate_percentage"] == 50.0
    
    # Verify correct files in each list
    process_hashes = {f["content_hash"] for f in result["files_to_process"]}
    skip_hashes = {f["content_hash"] for f in result["files_to_skip"]}
    
    assert "newhash1" in process_hashes
    assert "newhash2" in process_hashes
    assert test_data["hashes"][0] in skip_hashes
    assert test_data["hashes"][1] in skip_hashes


@pytest.mark.asyncio
async def test_global_instance():
    """Test that get_commit_optimizer returns same instance."""
    optimizer1 = get_commit_optimizer()
    optimizer2 = get_commit_optimizer()
    
    assert optimizer1 is optimizer2


@pytest.mark.asyncio
async def test_batch_size_configuration():
    """Test that batch size is configurable."""
    optimizer = CommitOptimizer()
    
    assert optimizer.batch_size == 100
    
    # Can be changed
    optimizer.batch_size = 50
    assert optimizer.batch_size == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

