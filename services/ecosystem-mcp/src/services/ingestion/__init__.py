"""
Ingestion services for document processing.

This package contains the ingestion worker and related services
for processing documents from Git repositories.
"""

from .ingestion_worker import IngestionWorker, get_ingestion_worker
from .job_processor import JobProcessor

__all__ = [
    "IngestionWorker",
    "JobProcessor",
    "get_ingestion_worker",
]

