class MemoryCache(CacheBackend):
    """In-memory cache implementation with LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None) -> None:
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    await self.delete(key)
                    return None

                entry.access()
                self._hits += 1
                return entry.value
            else:
                self._misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache."""
        with self._lock:
            # Calculate TTL
            expires_at = None
            if ttl or self._default_ttl:
                ttl_seconds = ttl or self._default_ttl
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            entry.calculate_size()

            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self._max_size:
                await self._evict_lru()

            self._cache[key] = entry

    async def delete(self, key: str) -> None:
        """Delete value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    await self.delete(key)
                    return False
                return True
            return False

    async def clear(self) -> None:
        """Clear all memory cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        oldest_key = self._find_oldest_entry_key()
        if oldest_key:
            self._remove_entry(oldest_key)

    def _find_oldest_entry_key(self) -> Optional[str]:
        """Find the key of the oldest entry based on access time."""
        oldest_key = None
        oldest_time = datetime.now(timezone.utc)

        for key, entry in self._cache.items():
            entry_time = self._get_entry_comparison_time(entry)
            if entry_time and entry_time < oldest_time:
                oldest_time = entry_time
                oldest_key = key

        return oldest_key

    def _get_entry_comparison_time(self, entry) -> Optional[datetime]:
        """Get the time to use for comparing entry age."""
        if entry.last_accessed:
            return entry.last_accessed
        elif entry.created_at:
            return entry.created_at
        return None

    def _remove_entry(self, key: str) -> None:
        """Remove an entry from the cache and update eviction count."""
        del self._cache[key]
        self._evictions += 1

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        with self._lock:
            total_size = sum(entry.size_bytes for entry in self._cache.values())

            return {
                "entries": len(self._cache),
                "max_size": self._max_size,
                "total_size_bytes": total_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (
                    self._hits / (self._hits + self._misses)
                    if (self._hits + self._misses) > 0
                    else 0
                ),
                "evictions": self._evictions,
                "default_ttl": self._default_ttl,
            }


