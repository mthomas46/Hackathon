"""Ingestion Application Queries"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetIngestionStatusQuery:
    """Query to get ingestion status."""
    ingestion_id: str


@dataclass
class ListIngestionsQuery:
    """Query to list ingestions."""
    status_filter: Optional[str] = None
    source_type_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0
