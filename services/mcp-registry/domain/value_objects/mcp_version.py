"""MCP Version Value Object."""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class MCPVersion:
    """
    Semantic version for MCP instances.
    
    Follows semantic versioning: MAJOR.MINOR.PATCH
    """
    
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None  # e.g., "alpha", "beta", "rc.1"
    build_metadata: Optional[str] = None  # e.g., "20250106"
    
    def __post_init__(self):
        """Validate version numbers."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers must be non-negative")
    
    def __str__(self) -> str:
        """String representation of version."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        
        if self.prerelease:
            version += f"-{self.prerelease}"
        
        if self.build_metadata:
            version += f"+{self.build_metadata}"
        
        return version
    
    def __lt__(self, other: "MCPVersion") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, MCPVersion):
            return NotImplemented
        
        # Compare major.minor.patch
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # Prerelease versions are lower than release versions
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        
        # Both have prerelease or both don't
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        
        return False
    
    def __le__(self, other: "MCPVersion") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other: "MCPVersion") -> bool:
        """Greater than comparison."""
        return not self <= other
    
    def __ge__(self, other: "MCPVersion") -> bool:
        """Greater than or equal comparison."""
        return not self < other
    
    @classmethod
    def from_string(cls, version_string: str) -> "MCPVersion":
        """
        Parse version from string.
        
        Args:
            version_string: Version string (e.g., "1.2.3", "2.0.0-beta", "1.0.0+20250106")
        
        Returns:
            MCPVersion instance
        
        Raises:
            ValueError: If version string is invalid
        """
        # Regex for semantic versioning
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$'
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Invalid version string: {version_string}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build_metadata=build
        )
    
    def bump_major(self) -> "MCPVersion":
        """Create new version with bumped major number."""
        return MCPVersion(
            major=self.major + 1,
            minor=0,
            patch=0,
            prerelease=None,
            build_metadata=None
        )
    
    def bump_minor(self) -> "MCPVersion":
        """Create new version with bumped minor number."""
        return MCPVersion(
            major=self.major,
            minor=self.minor + 1,
            patch=0,
            prerelease=None,
            build_metadata=None
        )
    
    def bump_patch(self) -> "MCPVersion":
        """Create new version with bumped patch number."""
        return MCPVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch + 1,
            prerelease=None,
            build_metadata=None
        )
    
    def is_prerelease(self) -> bool:
        """Check if this is a prerelease version."""
        return self.prerelease is not None
    
    def is_compatible_with(self, other: "MCPVersion") -> bool:
        """
        Check if versions are compatible (same major version).
        
        Args:
            other: Version to compare
        
        Returns:
            True if compatible (major versions match)
        """
        return self.major == other.major

