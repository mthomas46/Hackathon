"""Package Status Value Object."""

from enum import Enum


class PackageStatus(Enum):
    """Status of an MCP package."""
    
    DRAFT = "draft"              # Package is being prepared
    PUBLISHED = "published"      # Package is available
    DEPRECATED = "deprecated"    # Package is outdated
    ARCHIVED = "archived"        # Package is no longer available
    PRIVATE = "private"          # Package is private (not in marketplace)
