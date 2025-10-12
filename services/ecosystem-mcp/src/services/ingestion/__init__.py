"""
Ingestion services for document processing.

This package contains the ingestion worker and related services
for processing documents from Git repositories.
"""

from .ingestion_worker import IngestionWorker
from .job_processor import JobProcessor

__all__ = [
    "IngestionWorker",
    "JobProcessor",
]

