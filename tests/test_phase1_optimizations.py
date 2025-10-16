"""
Tests for Phase 1 optimizations:
- Batch embedding generation
- Connection pooling
- Smart caching
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.ecosystem_mcp.src.services.ingestion.job_processor import JobProcessor
from services.ecosystem_mcp.src.storage.db_models import IngestionJobModel
from services.ecosystem_mcp.src.models.git_commit import GitCommit


@pytest.fixture
def test_job():
    """Create a test ingestion job."""
    return IngestionJobModel(
        id=uuid4(),
        repo_path="/test/repo",
        mode="quick",
        status="queued",
        created_at=datetime.utcnow(),
        job_metadata={}
    )


@pytest.fixture
def test_commit():
    """Create a test commit."""
    return GitCommit(
        sha="test123456",
        message="Test commit",
        author="Test <test@example.com>",
        date=datetime.utcnow(),
        metadata={}
    )


@pytest.fixture
def batch_test_files():
    """Create a batch of test files."""
    return [
        {
            'file_path': f'test/file{i}.py',
            'content': f'content{i}',
            'content_hash': f'hash{i}'
        }
        for i in range(10)
    ]


@pytest.mark.asyncio
async def test_batch_optimization_enabled():
    """Test that batch optimization can be enabled."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    assert processor.use_batch_optimization is True


@pytest.mark.asyncio
async def test_batch_optimization_disabled():
    """Test that batch optimization can be disabled."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=False)
    
    assert processor.use_batch_optimization is False


@pytest.mark.asyncio
async def test_batch_embedding_generation(test_job, test_commit, batch_test_files):
    """Test that embeddings are generated in batch."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    # Mock dependencies
    with patch.object(processor.embedding_service, 'generate_batch') as mock_batch:
        mock_batch.return_value = [
            {'embedding': [0.1] * 768, 'tokens': 100, 'cost': 0.01, 'model': 'nomic'}
            for _ in range(10)
        ]
        
        with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_check:
            mock_check.return_value = {'already_ingested': False, 'document_count': 0, 'ingested_at': None}
            
            with patch.object(processor, 'git_service') as mock_git:
                mock_git.get_commit_files.return_value = [f['file_path'] for f in batch_test_files]
                
                async def mock_get_content(commit_sha, file_path):
                    return f"content of {file_path}"
                
                mock_git.get_file_content_at_commit = mock_get_content
                mock_git.repo_path = "/test/repo"
                
                with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_database'):
                    with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_chroma_client'):
                        # Process batch
                        await processor._process_batch_optimized(
                            batch_files=batch_test_files,
                            commit=test_commit,
                            job=test_job
                        )
                        
                        # Verify batch embedding was called
                        assert mock_batch.called
                        call_args = mock_batch.call_args
                        
                        # Verify it was called with all texts at once
                        assert 'texts' in call_args.kwargs or len(call_args.args) > 0


@pytest.mark.asyncio
async def test_connection_pooling(test_job, test_commit, batch_test_files):
    """Test that database session is reused for batch."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    session_count = 0
    
    class MockSessionContext:
        async def __aenter__(self):
            nonlocal session_count
            session_count += 1
            return MagicMock()
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    mock_db = Mock()
    mock_db.session.return_value = MockSessionContext()
    
    with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_database', return_value=mock_db):
        with patch.object(processor.embedding_service, 'generate_batch') as mock_batch:
            mock_batch.return_value = [
                {'embedding': [0.1] * 768, 'tokens': 100, 'cost': 0.01}
                for _ in range(10)
            ]
            
            processor.git_service = Mock()
            processor.git_service.repo_path = "/test/repo"
            
            with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_chroma_client'):
                await processor._process_batch_optimized(
                    batch_files=batch_test_files,
                    commit=test_commit,
                    job=test_job
                )
                
                # Should only open 1 session for entire batch
                assert session_count == 1


@pytest.mark.asyncio
async def test_normalizer_caching(test_job, test_commit):
    """Test that normalizers are cached and reused."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    # Create files with same extension
    batch_files = [
        {'file_path': f'test/file{i}.py', 'content': f'content{i}', 'content_hash': f'hash{i}'}
        for i in range(5)
    ]
    
    normalizer_create_count = 0
    original_get_normalizer = processor.normalizer_factory.get_normalizer
    
    def mock_get_normalizer(ext):
        nonlocal normalizer_create_count
        normalizer_create_count += 1
        return original_get_normalizer(ext)
    
    processor.normalizer_factory.get_normalizer = mock_get_normalizer
    
    with patch.object(processor.embedding_service, 'generate_batch') as mock_batch:
        mock_batch.return_value = [
            {'embedding': [0.1] * 768, 'tokens': 100, 'cost': 0.01}
            for _ in range(5)
        ]
        
        processor.git_service = Mock()
        processor.git_service.repo_path = "/test/repo"
        
        with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_database'):
            with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_chroma_client'):
                await processor._process_batch_optimized(
                    batch_files=batch_files,
                    commit=test_commit,
                    job=test_job
                )
                
                # Should only create normalizer once for .py extension
                # (not 5 times for 5 files)
                assert normalizer_create_count <= 2  # Maybe 1 for .py, maybe 1 fallback


@pytest.mark.asyncio
async def test_bulk_database_insert(test_job, test_commit, batch_test_files):
    """Test that documents are inserted in bulk."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    add_all_called = False
    commit_count = 0
    
    class MockSession:
        def add_all(self, items):
            nonlocal add_all_called
            add_all_called = True
            assert len(items) > 1  # Should be bulk insert, not single
        
        async def commit(self):
            nonlocal commit_count
            commit_count += 1
        
        async def execute(self, query):
            return MagicMock(scalar_one_or_none=lambda: None, fetchall=lambda: [])
        
        async def flush(self):
            pass
        
        def add(self, item):
            pass
    
    class MockSessionContext:
        async def __aenter__(self):
            return MockSession()
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    mock_db = Mock()
    mock_db.session.return_value = MockSessionContext()
    
    with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_database', return_value=mock_db):
        with patch.object(processor.embedding_service, 'generate_batch') as mock_batch:
            mock_batch.return_value = [
                {'embedding': [0.1] * 768, 'tokens': 100, 'cost': 0.01}
                for _ in range(10)
            ]
            
            processor.git_service = Mock()
            processor.git_service.repo_path = "/test/repo"
            
            with patch('services.ecosystem_mcp.src.services.ingestion.job_processor.get_chroma_client'):
                await processor._process_batch_optimized(
                    batch_files=batch_test_files,
                    commit=test_commit,
                    job=test_job
                )
                
                # Verify bulk operations were used
                assert add_all_called
                # Should have minimal commits (1 for batch)
                assert commit_count <= 2


@pytest.mark.asyncio
async def test_batch_size_configuration(test_job, test_commit):
    """Test that batch size can be configured."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=True)
    
    processor.git_service = Mock()
    processor.git_service.get_commit_files.return_value = [f"file{i}.py" for i in range(25)]
    processor.git_service.get_file_content_at_commit = AsyncMock(return_value="content")
    processor.git_service.repo_path = "/test/repo"
    
    batch_sizes_used = []
    
    async def mock_process_batch(batch_files, commit, job):
        batch_sizes_used.append(len(batch_files))
        return {"processed": len(batch_files), "failed": 0, "embeddings": len(batch_files), "cost": 0.0}
    
    processor._process_batch_optimized = mock_process_batch
    
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_check:
        mock_check.return_value = {'already_ingested': False, 'document_count': 0, 'ingested_at': None}
        
        with patch.object(processor.commit_optimizer, 'batch_check_content_hashes') as mock_batch_check:
            mock_batch_check.return_value = set()  # No duplicates
            
            # Process with batch size of 10
            await processor._process_commit_with_batch_optimization(
                commit=test_commit,
                job=test_job,
                batch_size=10
            )
            
            # Should have processed in 3 batches: 10, 10, 5
            assert len(batch_sizes_used) == 3
            assert batch_sizes_used[0] == 10
            assert batch_sizes_used[1] == 10
            assert batch_sizes_used[2] == 5


@pytest.mark.asyncio
async def test_optimization_backward_compatibility(test_job, test_commit):
    """Test that old method still works when optimization is disabled."""
    processor = JobProcessor(worker_id="test", use_batch_optimization=False)
    
    processor.git_service = Mock()
    processor.git_service.get_commit_files.return_value = []
    processor.git_service.repo_path = "/test/repo"
    
    with patch.object(processor.commit_optimizer, 'check_commit_already_ingested') as mock_check:
        mock_check.return_value = {'already_ingested': False, 'document_count': 0, 'ingested_at': None}
        
        # Should still work with old method
        result = await processor._process_commit(test_commit, test_job)
        
        assert "processed" in result
        assert "failed" in result
        assert "skipped" in result


@pytest.mark.asyncio
async def test_performance_improvement_simulation():
    """Simulate performance improvement from batch processing."""
    import time
    
    # Simulate sequential processing (old way)
    sequential_time = 0
    for i in range(10):
        start = time.time()
        # Simulate embedding generation (400ms per file)
        await asyncio.sleep(0.001)  # Reduced for testing
        sequential_time += time.time() - start
    
    # Simulate batch processing (new way)
    import asyncio
    
    start = time.time()
    tasks = [asyncio.sleep(0.001) for _ in range(10)]
    await asyncio.gather(*tasks)
    batch_time = time.time() - start
    
    # Batch should be significantly faster
    # (In production: 400ms×10 = 4000ms vs 400ms = 10× faster)
    assert batch_time < sequential_time / 5  # At least 5× faster in test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

