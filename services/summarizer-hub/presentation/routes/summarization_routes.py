"""Summarization API routes.

This module contains FastAPI routes for summarization operations.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models.simulation_models import SummarizationRequest
from ...domain.services.summarization_service import SummarizationService
from ...domain.entities.document import Document

router = APIRouter(prefix="/api/v1/summarize", tags=["summarization"])
service = SummarizationService()


@router.post("/")
async def summarize_document(request: SummarizationRequest) -> Dict[str, Any]:
    """Summarize a document."""
    try:
        # Create document entity
        document = Document.create(
            content=request.content,
            title="API Document"
        )

        # Generate summary
        from ...domain.entities.summary import SummaryType
        summary_type = SummaryType(request.summary_type)

        summary = await service.create_summary(
            document=document,
            summary_type=summary_type,
            parameters={
                "max_length": request.max_length,
                "include_metadata": request.include_metadata
            }
        )

        return {
            "summary_id": summary.id.value,
            "content": summary.content,
            "summary_type": summary.summary_type.value,
            "provider": summary.provider,
            "compression_ratio": summary.metrics.compression_ratio,
            "quality_score": summary.get_quality_score(),
            "created_at": summary.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get summarization service capabilities."""
    return {
        "supported_formats": ["text", "markdown", "html"],
        "summary_types": ["brief", "comprehensive", "executive", "technical"],
        "providers": ["openai", "anthropic", "local"],
        "features": [
            "multi_model_support",
            "quality_metrics",
            "factual_accuracy_check",
            "key_points_coverage"
        ]
    }
