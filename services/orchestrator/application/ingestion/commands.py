"""Ingestion Application Commands"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class StartIngestionCommand:
    """Command to start document ingestion."""
    source_url: str
    source_type: str
    parameters: Dict[str, Any]


@dataclass
class CancelIngestionCommand:
    """Command to cancel document ingestion."""
    ingestion_id: str


@dataclass
class RetryIngestionCommand:
    """Command to retry failed ingestion."""
    ingestion_id: str
