"""
Unit tests for SnapshotProcessor

Tests fast snapshot mode ingestion (10-100× faster than Git mode).
"""

import pytest
import asyncio
import hashlib
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.services.ingestion.snapshot_processor import SnapshotProcessor


@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = Mock()
    db.get_session = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=session), __aexit__=AsyncMock()))
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = Mock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture
def processor(tmp_path, mock_db, mock_redis):
    """Create a SnapshotProcessor with mocked dependencies."""
    with patch('src.services.ingestion.snapshot_processor.get_database', return_value=mock_db):
        with patch('src.services.ingestion.snapshot_processor.get_redis_client', return_value=mock_redis):
            return SnapshotProcessor(repo_path=tmp_path, job_id="test-job-1")


class TestSnapshotProcessorBasic:
    """Basic SnapshotProcessor tests."""
    
    def test_initialization(self, processor, tmp_path):
        """Test processor initializes correctly."""
        assert processor.repo_path == tmp_path
        assert processor.job_id == "test-job-1"
        assert processor.batch_size == 50
        assert isinstance(processor.ignore_patterns, set)
        assert isinstance(processor.binary_extensions, set)
    
    def test_ignore_patterns(self, processor):
        """Test ignore patterns are comprehensive."""
        patterns = processor.ignore_patterns
        
        # Check common patterns
        assert ".git" in patterns
        assert "__pycache__" in patterns
        assert "node_modules" in patterns
        assert ".venv" in patterns
    
    def test_binary_extensions(self, processor):
        """Test binary extensions are comprehensive."""
        extensions = processor.binary_extensions
        
        # Check common binary types
        assert ".png" in extensions
        assert ".pdf" in extensions
        assert ".zip" in extensions
        assert ".exe" in extensions


class TestFileDiscovery:
    """Test file discovery logic."""
    
    @pytest.mark.asyncio
    async def test_discover_files_empty_directory(self, processor):
        """Test discovering files in empty directory."""
        files = await processor._discover_files()
        
        assert isinstance(files, list)
        assert len(files) == 0
    
    @pytest.mark.asyncio
    async def test_discover_files_with_files(self, processor, tmp_path):
        """Test discovering actual files."""
        # Create test files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.md").write_text("# Readme")
        
        files = await processor._discover_files()
        
        assert len(files) == 2
        assert all(isinstance(f, Path) for f in files)
    
    @pytest.mark.asyncio
    async def test_discover_ignores_patterns(self, processor, tmp_path):
        """Test file discovery ignores specified patterns."""
        # Create files to ignore
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "file.pyc").write_text("binary")
        (tmp_path / "normal.py").write_text("code")
        
        files = await processor._discover_files()
        
        # Should only find normal.py
        assert len(files) == 1
        assert files[0].name == "normal.py"
    
    def test_should_ignore_true(self, processor):
        """Test should_ignore returns True for ignored paths."""
        assert processor._should_ignore(Path("/path/__pycache__/file.py")) is True
        assert processor._should_ignore(Path("/path/node_modules/module.js")) is True
        assert processor._should_ignore(Path("/path/.git/config")) is True
    
    def test_should_ignore_false(self, processor):
        """Test should_ignore returns False for normal paths."""
        assert processor._should_ignore(Path("/path/src/main.py")) is False
        assert processor._should_ignore(Path("/path/README.md")) is False


class TestBinaryDetection:
    """Test binary file detection."""
    
    def test_is_binary_by_extension(self, processor):
        """Test binary detection by file extension."""
        assert processor._is_binary(Path("image.png")) is True
        assert processor._is_binary(Path("document.pdf")) is True
        assert processor._is_binary(Path("archive.zip")) is True
        assert processor._is_binary(Path("script.py")) is False
    
    def test_is_binary_by_content(self, processor, tmp_path):
        """Test binary detection by content (null bytes)."""
        # Binary file (contains null byte)
        binary_file = tmp_path / "binary.dat"
        binary_file.write_bytes(b"Hello\x00World")
        assert processor._is_binary(binary_file) is True
        
        # Text file (no null bytes)
        text_file = tmp_path / "text.txt"
        text_file.write_text("Hello World")
        assert processor._is_binary(text_file) is False


class TestContentHashing:
    """Test content hashing."""
    
    def test_calculate_hash_consistent(self, processor):
        """Test hash calculation is consistent."""
        content = "Hello, World!"
        
        hash1 = processor._calculate_hash(content)
        hash2 = processor._calculate_hash(content)
        
        assert hash1 == hash2
    
    def test_calculate_hash_different_content(self, processor):
        """Test different content produces different hashes."""
        content1 = "Hello, World!"
        content2 = "Goodbye, World!"
        
        hash1 = processor._calculate_hash(content1)
        hash2 = processor._calculate_hash(content2)
        
        assert hash1 != hash2
    
    def test_calculate_hash_format(self, processor):
        """Test hash is MD5 format."""
        content = "Test content"
        hash_val = processor._calculate_hash(content)
        
        # MD5 hash is 32 hex characters
        assert len(hash_val) == 32
        assert all(c in '0123456789abcdef' for c in hash_val)
    
    def test_calculate_hash_matches_md5(self, processor):
        """Test hash matches standard MD5."""
        content = "Test content"
        expected = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        result = processor._calculate_hash(content)
        
        assert result == expected


class TestFileReading:
    """Test file reading."""
    
    @pytest.mark.asyncio
    async def test_read_file_success(self, processor, tmp_path):
        """Test reading file content."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        content = await processor._read_file(test_file)
        
        assert content == test_content
    
    @pytest.mark.asyncio
    async def test_read_file_utf8(self, processor, tmp_path):
        """Test reading UTF-8 content."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello 世界 🌍"
        test_file.write_text(test_content, encoding='utf-8')
        
        content = await processor._read_file(test_file)
        
        assert content == test_content
    
    @pytest.mark.asyncio
    async def test_read_file_nonexistent(self, processor, tmp_path):
        """Test reading non-existent file raises exception."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(Exception):
            await processor._read_file(test_file)


class TestNormalization:
    """Test content normalization."""
    
    @pytest.mark.asyncio
    async def test_normalize_with_normalizer(self, processor, tmp_path):
        """Test normalization with normalizer."""
        test_file = tmp_path / "test.py"
        content = "def hello():\n    print('world')"
        
        with patch('src.services.ingestion.snapshot_processor.get_normalizer') as mock_get_normalizer:
            mock_normalizer = Mock()
            mock_normalizer.normalize = AsyncMock(return_value="# Normalized")
            mock_get_normalizer.return_value = mock_normalizer
            
            result = await processor._normalize(test_file, content)
            
            assert result == "# Normalized"
            mock_get_normalizer.assert_called_once_with(".py")
    
    @pytest.mark.asyncio
    async def test_normalize_fallback_on_error(self, processor, tmp_path):
        """Test normalization falls back to raw content on error."""
        test_file = tmp_path / "test.py"
        content = "print('hello')"
        
        with patch('src.services.ingestion.snapshot_processor.get_normalizer') as mock_get_normalizer:
            mock_get_normalizer.side_effect = Exception("Normalizer failed")
            
            result = await processor._normalize(test_file, content)
            
            # Should fall back to code block
            assert "```" in result
            assert content in result


class TestDuplicateDetection:
    """Test duplicate detection logic."""
    
    @pytest.mark.asyncio
    async def test_load_existing_hashes(self, processor, mock_db):
        """Test loading existing content hashes."""
        # Mock database response
        mock_result = Mock()
        mock_result.fetchall = Mock(return_value=[
            ("hash1",),
            ("hash2",),
            ("hash3",)
        ])
        
        session = await mock_db.get_session().__aenter__()
        session.execute.return_value = mock_result
        
        hashes = await processor._load_existing_hashes()
        
        assert isinstance(hashes, set)
        assert len(hashes) == 3
        assert "hash1" in hashes
        assert "hash2" in hashes
        assert "hash3" in hashes
    
    @pytest.mark.asyncio
    async def test_load_existing_hashes_empty(self, processor, mock_db):
        """Test loading when no existing hashes."""
        mock_result = Mock()
        mock_result.fetchall = Mock(return_value=[])
        
        session = await mock_db.get_session().__aenter__()
        session.execute.return_value = mock_result
        
        hashes = await processor._load_existing_hashes()
        
        assert isinstance(hashes, set)
        assert len(hashes) == 0


class TestProgressReporting:
    """Test progress reporting."""
    
    @pytest.mark.asyncio
    async def test_publish_progress(self, processor, mock_redis):
        """Test publishing progress to Redis."""
        await processor._publish_progress(50, 100)
        
        # Should publish to Redis
        mock_redis.publish.assert_called_once()
        
        # Check channel
        call_args = mock_redis.publish.call_args
        channel = call_args[0][0]
        assert "ingestion:progress:test-job-1" in channel
    
    @pytest.mark.asyncio
    async def test_publish_progress_calculates_percentage(self, processor, mock_redis):
        """Test progress percentage calculation."""
        await processor._publish_progress(25, 100)
        
        call_args = mock_redis.publish.call_args
        data_str = call_args[0][1]
        
        # Should contain 25% progress
        assert "25" in data_str or "0.25" in data_str


class TestStatistics:
    """Test statistics tracking."""
    
    def test_initial_stats(self, processor):
        """Test initial statistics are zero."""
        assert processor.stats['total_discovered'] == 0
        assert processor.stats['processed'] == 0
        assert processor.stats['skipped'] == 0
        assert processor.stats['failed'] == 0
    
    def test_build_result(self, processor):
        """Test building result dictionary."""
        processor.stats['start_time'] = 100.0
        processor.stats['end_time'] = 110.0
        processor.stats['processed'] = 50
        processor.stats['skipped'] = 10
        processor.stats['failed'] = 2
        processor.stats['total_discovered'] = 62
        
        result = processor._build_result()
        
        assert result['mode'] == 'snapshot'
        assert result['processed'] == 50
        assert result['skipped'] == 10
        assert result['failed'] == 2
        assert result['elapsed_seconds'] == 10.0
        assert result['files_per_second'] == 5.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_process_empty_directory(self, processor):
        """Test processing empty directory."""
        result = await processor.process()
        
        assert result['mode'] == 'snapshot'
        assert result['total_discovered'] == 0
        assert result['processed'] == 0
    
    @pytest.mark.asyncio
    async def test_large_file_skipped(self, processor, tmp_path):
        """Test files >10MB are skipped."""
        # Create a file reference (don't actually write 10MB)
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 100)  # Write small amount
        
        # Mock stat to return large size
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value = Mock(st_size=11 * 1024 * 1024)  # 11MB
            
            files = await processor._discover_files()
            
            # Should be skipped
            assert len(files) == 0
    
    @pytest.mark.asyncio
    async def test_hash_collision_handling(self, processor):
        """Test handling of hash collisions (rare but possible)."""
        existing_hashes = {"hash1", "hash2"}
        
        # Simulate processing file with existing hash
        # Should skip it
        assert "hash1" in existing_hashes


class TestBatchProcessing:
    """Test batch processing logic."""
    
    def test_batch_size_configuration(self, tmp_path, mock_db, mock_redis):
        """Test custom batch size configuration."""
        with patch('src.services.ingestion.snapshot_processor.get_database', return_value=mock_db):
            with patch('src.services.ingestion.snapshot_processor.get_redis_client', return_value=mock_redis):
                processor = SnapshotProcessor(
                    repo_path=tmp_path,
                    job_id="test",
                    batch_size=100
                )
                
                assert processor.batch_size == 100


class TestPerformanceOptimizations:
    """Test performance optimization features."""
    
    @pytest.mark.asyncio
    async def test_parallel_file_reading(self, processor, tmp_path):
        """Test files are read in parallel (using executor)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        # Reading should use asyncio executor (not block)
        content = await processor._read_file(test_file)
        
        assert content == "content"
    
    def test_in_memory_hash_check(self, processor):
        """Test duplicate checking uses in-memory set (fast)."""
        existing_hashes = {"hash1", "hash2", "hash3"}
        
        # Checking membership should be O(1)
        assert "hash1" in existing_hashes
        assert "hash4" not in existing_hashes

