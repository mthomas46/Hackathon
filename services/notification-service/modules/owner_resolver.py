"""Owner resolution and caching for notification service."""

import os
import json
import time
from typing import Dict, Any, Optional


class OwnerResolver:
    """Manages owner-to-target resolution with caching."""

    def __init__(self, cache_ttl: float = 300.0):
        self._resolve_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = cache_ttl

    def resolve_owners(self, owners: list[str]) -> Dict[str, Dict[str, str]]:
        """Resolve owners to their target information with caching."""
        result: Dict[str, Dict[str, str]] = {}

        for owner in owners or []:
            # Check cache first
            cached = self._resolve_cache.get(owner)
            if cached and self._is_cache_valid(cached):
                # Return cached result without _ts field
                result[owner] = {k: v for k, v in cached.items() if k != "_ts"}
                continue

            # Resolve owner information
            owner_info = self._resolve_owner(owner)

            # Cache the result
            self._resolve_cache[owner] = {**owner_info, "_ts": time.time()}

            result[owner] = owner_info

        return result

    def _is_cache_valid(self, cached_entry: Dict[str, Any]) -> bool:
        """Check if cached entry is still valid."""
        cache_time = cached_entry.get("_ts", 0)
        return (time.time() - cache_time) <= self._cache_ttl

    def _resolve_owner(self, owner: str) -> Dict[str, str]:
        """Resolve a single owner to target information."""
        # Load owner mapping from configuration
        owner_map = self._load_owner_map()

        # Get mapping if available
        owner_info = owner_map.get(owner, {})

        # Apply heuristics if no mapping found
        if not owner_info:
            owner_info = self._apply_resolution_heuristics(owner)

        return owner_info

    def _load_owner_map(self) -> Dict[str, Dict[str, str]]:
        """Load owner-to-target mapping from environment or file."""
        data: Dict[str, Dict[str, str]] = {}

        # Try environment variable first
        env_json = os.environ.get("NOTIFY_OWNER_MAP_JSON")
        if env_json:
            try:
                data = json.loads(env_json)
            except Exception:
                data = {}

        # Try file if no env var
        else:
            file_path = os.environ.get("NOTIFY_OWNER_MAP_FILE")
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "r") as fh:
                        data = json.load(fh)
                except Exception:
                    data = {}

        return data

    def _apply_resolution_heuristics(self, owner: str) -> Dict[str, str]:
        """Apply heuristics to resolve owner when no mapping exists."""
        if owner.startswith(("http://", "https://")):
            return {"webhook": owner}
        elif "@" in owner:
            return {"email": owner}
        else:
            return {"handle": owner}

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._resolve_cache.clear()


# Global instance
owner_resolver = OwnerResolver()
