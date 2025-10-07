"""Validation API Routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...application.services.validation_service import ValidationService
from ...application.services.documentation_service import DocumentationService

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


async def get_validation_service() -> ValidationService:
    """Get validation service instance."""
    raise NotImplementedError("Service dependency injection not configured")


async def get_documentation_service() -> DocumentationService:
    """Get documentation service instance."""
    raise NotImplementedError("Service dependency injection not configured")


@router.post("/validate/{doc_id}", response_model=dict)
async def validate_documentation(
    doc_id: str,
    validation_service: ValidationService = Depends(get_validation_service),
    doc_service: DocumentationService = Depends(get_documentation_service),
):
    """Validate documentation."""
    doc = await doc_service.get_documentation(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    
    result = await validation_service.validate_documentation(doc)
    return result.to_dict()


@router.get("/{doc_id}/latest", response_model=dict)
async def get_latest_validation(
    doc_id: str,
    service: ValidationService = Depends(get_validation_service),
):
    """Get latest validation result for documentation."""
    result = await service.get_latest_validation(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="No validation results found")
    return result.to_dict()

