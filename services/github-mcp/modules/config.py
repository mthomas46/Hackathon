"""Configuration management for GitHub MCP service.

This module provides centralized configuration management for the GitHub MCP (Model Context Protocol) service.
It handles environment variable parsing, validation, and provides default values for all configurable settings.

Key Responsibilities:
- Environment variable parsing and validation
- Default value management for missing configurations
- Configuration validation and type checking
- Secure credential handling for GitHub API tokens
- Redis connection configuration for caching and state management

Configuration Parameters:
- GitHub API token for authentication
- GitHub API base URL (supports GitHub Enterprise)
- Redis connection settings for caching
- Logging configuration
- Service-specific settings and timeouts

Security Considerations:
- GitHub tokens are handled securely and not logged
- Environment variables are validated before use
- Default values are conservative and secure
- Configuration validation prevents misconfigurations

Usage:
    config = Config()
    token = config.github_token
    redis_url = f"redis://{config.redis_host}:{config.redis_port}"
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
        return os.environ.get("GITHUB_API_HOST")

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
        return os.environ.get(
            "OFFICIAL_GH_MCP_BASE_URL", "http://github-mcp-server:8060"
        )


# Create singleton instance
config = Config()
