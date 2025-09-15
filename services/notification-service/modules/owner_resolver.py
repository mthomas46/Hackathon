"""Owner resolution and caching for notification service.

Provides efficient mapping of owner names to notification targets with
configurable caching to reduce resolution overhead.
"""
import os
import json
import time
from typing import Dict, Any, Optional


class OwnerResolver:
    """Manages owner-to-target resolution with TTL-based caching.

    This class handles the mapping of owner names/handles to their
    notification targets (email, webhook URLs, etc.) with automatic
    caching and fallback heuristics for unknown owners.
    """

    def __init__(self, cache_ttl: float = 300.0):
        """Initialize the owner resolver with cache settings.

        Args:
            cache_ttl: Time-to-live for cached resolutions in seconds (default: 300)
        """
        self._resolution_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl_seconds = cache_ttl

    def resolve_owners(self, owners: list[str]) -> Dict[str, Dict[str, str]]:
        """Resolve multiple owner names to their notification targets.

        Processes a list of owner identifiers and returns their corresponding
        notification targets. Uses caching for performance and applies
        fallback heuristics for unknown owners.

        Args:
            owners: List of owner names to resolve

        Returns:
            Dictionary mapping owner names to their target information
        """
        resolved_targets: Dict[str, Dict[str, str]] = {}

        for owner_name in owners or []:
            # Check cache first for performance
            cached_resolution = self._resolution_cache.get(owner_name)
            if cached_resolution and self._is_cache_entry_valid(cached_resolution):
                # Return cached result without internal timestamp field
                resolved_targets[owner_name] = {
                    key: value
                    for key, value in cached_resolution.items()
                    if key != "_ts"
                }
                continue

            # Resolve owner information from mapping or heuristics
            target_info = self._resolve_single_owner(owner_name)

            # Cache the resolution result with timestamp
            self._resolution_cache[owner_name] = {
                **target_info,
                "_ts": time.time()
            }

            resolved_targets[owner_name] = target_info

        return resolved_targets

    def _is_cache_entry_valid(self, cached_entry: Dict[str, Any]) -> bool:
        """Check if a cached resolution entry is still valid based on TTL.

        Args:
            cached_entry: Cached entry with timestamp

        Returns:
            True if the entry is within TTL, False if expired
        """
        cache_timestamp = cached_entry.get("_ts", 0)
        elapsed_seconds = time.time() - cache_timestamp
        return elapsed_seconds <= self._cache_ttl_seconds

    def _resolve_single_owner(self, owner: str) -> Dict[str, str]:
        """Resolve a single owner name to notification target information.

        Args:
            owner: Owner name to resolve

        Returns:
            Dictionary with target information (e.g., {"email": "user@domain.com"})
        """
        # Load owner mapping from configuration sources
        owner_mapping = self._load_owner_mapping()

        # Get direct mapping if available
        target_info = owner_mapping.get(owner, {})

        # Apply heuristics if no direct mapping found
        if not target_info:
            target_info = self._apply_resolution_heuristics(owner)

        return target_info

    def _load_owner_mapping(self) -> Dict[str, Dict[str, str]]:
        """Load owner-to-target mapping from configuration sources.

        Attempts to load owner mappings from environment variables or files.
        Supports both JSON environment variables and external configuration files.

        Returns:
            Dictionary mapping owner names to their target configurations
        """
        mapping_data: Dict[str, Dict[str, str]] = {}

        # Try environment variable first for containerized deployments
        json_config = os.environ.get("NOTIFY_OWNER_MAP_JSON")
        if json_config:
            try:
                mapping_data = json.loads(json_config)
            except json.JSONDecodeError:
                # Log error but continue with empty mapping
                mapping_data = {}

        # Try file-based configuration if no env var
        else:
            config_file_path = os.environ.get("NOTIFY_OWNER_MAP_FILE")
            if config_file_path and os.path.exists(config_file_path):
                try:
                    with open(config_file_path, "r", encoding="utf-8") as config_file:
                        mapping_data = json.load(config_file)
                except (json.JSONDecodeError, IOError):
                    # Log error but continue with empty mapping
                    mapping_data = {}

        return mapping_data

    def _apply_resolution_heuristics(self, owner: str) -> Dict[str, str]:
        """Apply intelligent heuristics to resolve owners without explicit mappings.

        Uses pattern matching to infer notification targets from owner names:
        - URLs are treated as webhook endpoints
        - Email-like strings are treated as email addresses
        - Other strings are treated as generic handles

        Args:
            owner: Owner identifier to analyze

        Returns:
            Dictionary with inferred target information
        """
        if owner.startswith(("http://", "https://")):
            return {"webhook": owner}
        elif "@" in owner and "." in owner:
            return {"email": owner}
        else:
            return {"handle": owner}

    def clear_cache(self) -> None:
        """Clear all cached owner resolutions.

        Forces fresh resolution of all owners on next request.
        Useful for testing or when configuration changes.
        """
        self._resolution_cache.clear()


# Global instance
owner_resolver = OwnerResolver()
