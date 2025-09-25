"""Cache Manager - Advanced caching strategies and implementations."""

import asyncio
import hashlib
import logging
import pickle  # nosec: Required for controlled cache serialization
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypeVar


from ..di.services import ICacheService, ILoggerService
from ..logging.logger import get_logger

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return (
            self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at
        )

    def access(self) -> None:
        """Record access to this entry."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    def calculate_size(self) -> int:
        """Calculate approximate size of the entry in bytes."""
        try:
            # Rough size calculation
            value_size = len(
                pickle.dumps(self.value)
            )  # nosec: Safe for size calculation only
            metadata_size = len(
                pickle.dumps(
                    {  # nosec: Safe for size calculation only
                        "key": self.key,
                        "created_at": self.created_at,
                        "expires_at": self.expires_at,
                        "access_count": self.access_count,
                        "last_accessed": self.last_accessed,
                        "tags": self.tags,
                    }
                )
            )
            return value_size + metadata_size
        except Exception as e:
            # Log the error but return default size estimate
            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to calculate cache entry size: {e}")
            return 1024  # Default size estimate


