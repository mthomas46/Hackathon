"""ExportConfig Value Object."""

from dataclasses import dataclass
from .package_format import PackageFormat
from .compression_type import CompressionType


@dataclass(frozen=True)
class ExportConfig:
    """
    Export configuration value object.
    
    Immutable configuration for package export operations.
    """
    
    format: PackageFormat = PackageFormat.MCP_V1
    compression: CompressionType = CompressionType.GZIP
    include_metadata: bool = True
    include_dependencies: bool = True
    validate_before_export: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if not isinstance(self.format, PackageFormat):
            raise ValueError("format must be a PackageFormat enum")
        if not isinstance(self.compression, CompressionType):
            raise ValueError("compression must be a CompressionType enum")

