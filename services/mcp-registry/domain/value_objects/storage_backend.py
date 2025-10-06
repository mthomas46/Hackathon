"""Storage Backend Value Object."""

from enum import Enum


class StorageBackend(str, Enum):
    """
    Available storage backends for MCP artifacts.
    
    Supports multiple storage options for flexibility.
    """
    
    LOCAL_FILESYSTEM = "local_filesystem"
    """Store MCPs on local filesystem."""
    
    S3_COMPATIBLE = "s3_compatible"
    """Store MCPs in S3 or S3-compatible storage (MinIO, etc.)."""
    
    REDIS = "redis"
    """Store small MCPs in Redis (for fast access)."""
    
    DISTRIBUTED_FS = "distributed_fs"
    """Store MCPs on distributed filesystem (NFS, etc.)."""
    
    @property
    def supports_versioning(self) -> bool:
        """Check if backend supports versioning natively."""
        return self in {
            StorageBackend.S3_COMPATIBLE,  # S3 has versioning
        }
    
    @property
    def supports_compression(self) -> bool:
        """Check if backend benefits from compression."""
        return self in {
            StorageBackend.LOCAL_FILESYSTEM,
            StorageBackend.DISTRIBUTED_FS,
            StorageBackend.REDIS,  # Redis benefits from compressed data
        }
    
    @property
    def is_cloud_storage(self) -> bool:
        """Check if backend is cloud-based."""
        return self == StorageBackend.S3_COMPATIBLE
    
    @property
    def requires_credentials(self) -> bool:
        """Check if backend requires authentication."""
        return self == StorageBackend.S3_COMPATIBLE

