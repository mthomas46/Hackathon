"""Configuration management for GitHub MCP service.

Handles environment variable parsing and configuration settings.
"""
import os
from typing import Optional, Set


class Config:
    """Configuration management for GitHub MCP."""

    @staticmethod
    def parse_toolsets_from_env() -> Optional[Set[str]]:
        """Parse toolsets from environment variable."""
        env = os.environ.get("GITHUB_TOOLSETS", "").strip()
        if not env:
            return None
        parts = [p.strip() for p in env.split(",") if p.strip()]
        return set(parts) if parts else None

    @staticmethod
    def is_dynamic_enabled() -> bool:
        """Check if dynamic toolsets are enabled."""
        return os.environ.get("GITHUB_DYNAMIC_TOOLSETS", "0") in ("1", "true", "TRUE")

    @staticmethod
    def is_read_only() -> bool:
        """Check if service is in read-only mode."""
        return os.environ.get("GITHUB_READ_ONLY", "0") in ("1", "true", "TRUE")

    @staticmethod
    def is_mock_default() -> bool:
        """Check if mock mode is the default."""
        return os.environ.get("GITHUB_MOCK", "1") == "1"

    @staticmethod
    def get_github_host() -> Optional[str]:
        """Get GitHub host from environment."""
        return os.environ.get("GITHUB_HOST")

    @staticmethod
    def has_github_token() -> bool:
        """Check if GitHub personal access token is present."""
        return bool(os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN"))

    @staticmethod
    def should_use_official_mcp() -> bool:
        """Check if should proxy to official GitHub MCP server."""
        return os.environ.get("USE_OFFICIAL_GH_MCP", "0") in ("1", "true", "TRUE")

    @staticmethod
    def get_official_mcp_base_url() -> str:
        """Get base URL for official GitHub MCP server."""
        return os.environ.get("OFFICIAL_GH_MCP_BASE_URL", "http://github-mcp-server:8060")


# Create singleton instance
config = Config()
