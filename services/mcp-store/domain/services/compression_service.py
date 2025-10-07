"""Compression Service - Domain Layer.

Handles compression/decompression of .mcp package files using Zstandard.
"""

import zstandard as zstd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CompressionError(Exception):
    """Raised when compression/decompression fails."""
    pass


class CompressionService:
    """
    Service for compressing and decompressing MCP package files.
    
    Uses Zstandard compression for high compression ratios and fast decompression.
    """
    
    def __init__(self, compression_level: int = 3):
        """
        Initialize compression service.
        
        Args:
            compression_level: Compression level (1-22). Higher = better compression, slower.
                             3 is recommended for balanced performance.
        """
        self.compression_level = compression_level
        self.compressor = zstd.ZstdCompressor(level=compression_level)
        self.decompressor = zstd.ZstdDecompressor()
        logger.info(f"Compression service initialized (level={compression_level})")
    
    def compress(self, data: bytes) -> bytes:
        """
        Compress data.
        
        Args:
            data: Raw bytes to compress
            
        Returns:
            Compressed bytes
            
        Raises:
            CompressionError: If compression fails
        """
        try:
            compressed = self.compressor.compress(data)
            original_size = len(data)
            compressed_size = len(compressed)
            ratio = compressed_size / original_size if original_size > 0 else 0
            
            logger.info(
                f"Compressed {original_size:,} bytes → {compressed_size:,} bytes "
                f"({ratio:.1%} ratio, {(1-ratio)*100:.1f}% savings)"
            )
            
            return compressed
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise CompressionError(f"Failed to compress data: {e}") from e
    
    def decompress(self, compressed_data: bytes, max_output_size: Optional[int] = None) -> bytes:
        """
        Decompress data.
        
        Args:
            compressed_data: Compressed bytes
            max_output_size: Maximum allowed decompressed size (safety limit)
            
        Returns:
            Decompressed bytes
            
        Raises:
            CompressionError: If decompression fails
        """
        try:
            if max_output_size:
                decompressed = self.decompressor.decompress(
                    compressed_data,
                    max_output_size=max_output_size
                )
            else:
                decompressed = self.decompressor.decompress(compressed_data)
            
            compressed_size = len(compressed_data)
            decompressed_size = len(decompressed)
            
            logger.info(
                f"Decompressed {compressed_size:,} bytes → {decompressed_size:,} bytes"
            )
            
            return decompressed
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise CompressionError(f"Failed to decompress data: {e}") from e
    
    def compress_file(self, input_path: str, output_path: str) -> int:
        """
        Compress a file.
        
        Args:
            input_path: Path to input file
            output_path: Path to output compressed file
            
        Returns:
            Size of compressed file in bytes
            
        Raises:
            CompressionError: If compression fails
        """
        try:
            with open(input_path, 'rb') as input_file:
                data = input_file.read()
            
            compressed = self.compress(data)
            
            with open(output_path, 'wb') as output_file:
                output_file.write(compressed)
            
            return len(compressed)
        except CompressionError:
            raise
        except Exception as e:
            logger.error(f"File compression failed: {e}")
            raise CompressionError(f"Failed to compress file: {e}") from e
    
    def decompress_file(
        self,
        input_path: str,
        output_path: str,
        max_output_size: Optional[int] = None
    ) -> int:
        """
        Decompress a file.
        
        Args:
            input_path: Path to compressed file
            output_path: Path to output decompressed file
            max_output_size: Maximum allowed decompressed size (safety limit)
            
        Returns:
            Size of decompressed file in bytes
            
        Raises:
            CompressionError: If decompression fails
        """
        try:
            with open(input_path, 'rb') as input_file:
                compressed_data = input_file.read()
            
            decompressed = self.decompress(compressed_data, max_output_size)
            
            with open(output_path, 'wb') as output_file:
                output_file.write(decompressed)
            
            return len(decompressed)
        except CompressionError:
            raise
        except Exception as e:
            logger.error(f"File decompression failed: {e}")
            raise CompressionError(f"Failed to decompress file: {e}") from e
    
    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """
        Calculate compression ratio.
        
        Args:
            original_size: Original size in bytes
            compressed_size: Compressed size in bytes
            
        Returns:
            Compression ratio (0-1). Lower is better.
        """
        if original_size == 0:
            return 0.0
        return compressed_size / original_size
    
    def get_space_saved(self, original_size: int, compressed_size: int) -> int:
        """
        Calculate space saved by compression.
        
        Args:
            original_size: Original size in bytes
            compressed_size: Compressed size in bytes
            
        Returns:
            Bytes saved
        """
        return max(0, original_size - compressed_size)
