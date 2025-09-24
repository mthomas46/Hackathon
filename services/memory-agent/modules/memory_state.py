"""Memory State Module

This module contains the global memory state for the Memory Agent service.
Separated from main module to eliminate circular dependencies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemoryItem:
    """Memory item entity for the memory agent service."""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None

# Global memory state - centralized for all modules
_memory: List[MemoryItem] = []
