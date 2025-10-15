"""
Temporal Content Versioning System

Hybrid versioning approach combining:
- Content-addressable storage (SHA256) for deduplication
- Temporal ordering for timeline queries
- "As of" date queries
- Change tracking

Key Components:
- TemporalContentVersioner: Create and manage versions
- TimelineQueryEngine: Query documents across time
- ContentDeduplicator: Handle deduplicated storage
"""

from .temporal_content_versioner import TemporalContentVersioner, DocumentVersion
from .timeline_query_engine import (
    TimelineQueryEngine,
    TimelineEvent,
    DocumentSnapshot,
    DocumentChange
)
from .content_deduplicator import ContentDeduplicator

__all__ = [
    'TemporalContentVersioner',
    'DocumentVersion',
    'TimelineQueryEngine',
    'TimelineEvent',
    'DocumentSnapshot',
    'DocumentChange',
    'ContentDeduplicator',
]

