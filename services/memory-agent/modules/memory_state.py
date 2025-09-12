"""Memory State Module

This module contains the global memory state for the Memory Agent service.
Separated from main module to eliminate circular dependencies.
"""

from typing import List
from services.shared.models import MemoryItem

# Global memory state - centralized for all modules
_memory: List[MemoryItem] = []
