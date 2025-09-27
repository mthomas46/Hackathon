"""Source Agent REST API."""

from fastapi import APIRouter

# Import dependencies (these would normally come from dependency injection)
from ...application.use_cases.fetch_document_use_case import FetchDocumentUseCase
from ...domain.services.intelligent_ingestion import IntelligentIngestionService
from ...domain.services.fetch_handler import FetchHandler

# Create dependencies
_fetch_handler = FetchHandler()
_intelligent_ingestion_service = IntelligentIngestionService()
_fetch_document_use_case = FetchDocumentUseCase(_fetch_handler, _intelligent_ingestion_service)

# Import and create routers
from .routes.documents import create_document_router

# Create API router
api_router = APIRouter()
api_router.include_router(create_document_router(_fetch_document_use_case))

__all__ = ["api_router"]
