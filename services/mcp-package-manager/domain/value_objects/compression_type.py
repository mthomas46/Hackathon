"""CompressionType Value Object."""

from enum import Enum


class CompressionType(Enum):
    """Compression types for packages."""
    
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"
    BZIP2 = "bzip2"
    
    def get_compression_level(self) -> int:
        """Get recommended compression level."""
        levels = {
            CompressionType.NONE: 0,
            CompressionType.GZIP: 6,
            CompressionType.ZSTD: 3,
            CompressionType.BZIP2: 9,
        }
        return levels.get(self, 0)

