"""Database migration utilities."""

from .add_performance_indexes import (
    add_performance_indexes,
    remove_performance_indexes,
    analyze_index_usage
)

# Note: add_discovery_and_sub_jobs is imported lazily to avoid circular dependencies
# Import it directly when needed: from ...storage.migrations import add_discovery_and_sub_jobs

__all__ = [
    "add_performance_indexes",
    "remove_performance_indexes",
    "analyze_index_usage"
]

