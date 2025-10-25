"""
Ingestion services for document processing.

This package contains the ingestion worker and related services
for processing documents from Git repositories.
"""

# 🎯 USING ORIGINAL WORKER with 3 critical fixes applied:
# Fix #1: State validation before processing
# Fix #2: Invalid message handling  
# Fix #3: Orphaned job handling
from .ingestion_worker import IngestionWorker, get_ingestion_worker
from .job_processor import JobProcessor
from .ingestion_service import IngestionService, get_ingestion_service

__all__ = [
    "IngestionWorker",
    "JobProcessor",
    "IngestionService",
    "get_ingestion_worker",
    "get_ingestion_service",
]

