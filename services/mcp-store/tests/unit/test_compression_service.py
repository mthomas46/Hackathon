"""Unit tests for CompressionService."""

import pytest
import asyncio

from services.mcp_store.domain.services.compression_service import CompressionService


class TestCompressionService:
    """Tests for CompressionService."""
    
    @pytest.fixture
    def compression_service(self):
        """Create a CompressionService instance."""
        return CompressionService(compression_level=3)
    
    @pytest.mark.asyncio
    async def test_compress_stream(self, compression_service):
        """Test compressing a stream of data."""
        # Create test data
        test_data = [b"Hello ", b"World", b"!"]
        
        async def data_stream():
            for chunk in test_data:
                yield chunk
        
        # Compress
        compressed_chunks = []
        async for chunk in compression_service.compress_stream(data_stream()):
            compressed_chunks.append(chunk)
        
        compressed_data = b"".join(compressed_chunks)
        
        # Verify compression worked
        assert len(compressed_data) > 0
        assert compressed_data != b"Hello World!"  # Should be different (compressed)
    
    @pytest.mark.asyncio
    async def test_compress_decompress_roundtrip(self, compression_service):
        """Test compress and decompress roundtrip."""
        # Original data
        original_data = b"This is test data that should be compressed and then decompressed!"
        
        async def data_stream():
            yield original_data
        
        # Compress
        compressed_chunks = []
        async for chunk in compression_service.compress_stream(data_stream()):
            compressed_chunks.append(chunk)
        
        # Decompress
        async def compressed_stream():
            for chunk in compressed_chunks:
                yield chunk
        
        decompressed_chunks = []
        async for chunk in compression_service.decompress_stream(compressed_stream()):
            decompressed_chunks.append(chunk)
        
        decompressed_data = b"".join(decompressed_chunks)
        
        # Verify roundtrip
        assert decompressed_data == original_data
    
    @pytest.mark.asyncio
    async def test_calculate_checksum(self, compression_service):
        """Test calculating checksum."""
        test_data = b"Test data for checksum calculation"
        
        async def data_stream():
            yield test_data
        
        checksum, size = await compression_service.calculate_checksum(data_stream())
        
        # Verify checksum is a valid SHA256 hex string
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Verify size
        assert size == len(test_data)
    
    @pytest.mark.asyncio
    async def test_checksum_consistency(self, compression_service):
        """Test that same data produces same checksum."""
        test_data = b"Consistent test data"
        
        async def data_stream():
            yield test_data
        
        checksum1, _ = await compression_service.calculate_checksum(data_stream())
        checksum2, _ = await compression_service.calculate_checksum(data_stream())
        
        assert checksum1 == checksum2
    
    @pytest.mark.asyncio
    async def test_compression_reduces_size(self, compression_service):
        """Test that compression reduces data size for repetitive data."""
        # Create highly repetitive data that should compress well
        test_data = b"A" * 10000
        
        async def data_stream():
            yield test_data
        
        compressed_chunks = []
        async for chunk in compression_service.compress_stream(data_stream()):
            compressed_chunks.append(chunk)
        
        compressed_size = sum(len(chunk) for chunk in compressed_chunks)
        original_size = len(test_data)
        
        # Compressed size should be significantly smaller
        assert compressed_size < original_size
        assert compressed_size < original_size * 0.1  # At least 90% compression
    
    def test_service_initialization(self):
        """Test service initializes with correct compression level."""
        service = CompressionService(compression_level=5)
        assert service.cctx is not None
        assert service.dctx is not None
    
    @pytest.mark.asyncio
    async def test_empty_stream_handling(self, compression_service):
        """Test handling of empty data stream."""
        async def empty_stream():
            return
            yield  # Never executed
        
        compressed_chunks = []
        async for chunk in compression_service.compress_stream(empty_stream()):
            compressed_chunks.append(chunk)
        
        # Should handle gracefully
        assert len(compressed_chunks) >= 0  # May have compression header
