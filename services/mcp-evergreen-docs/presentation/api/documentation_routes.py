"""Documentation API Routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...application.services.documentation_service import DocumentationService
from ...domain.entities.documentation import Documentation

router = APIRouter(prefix="/api/v1/documentation", tags=["documentation"])

# Dependency injection placeholder
# In production, this would use proper DI container
async def get_documentation_service() -> DocumentationService:
    """Get documentation service instance."""
    # This is a placeholder - would be properly implemented with DI
    raise NotImplementedError("Service dependency injection not configured")


@router.post("/", response_model=dict)
async def create_documentation(
    title: str,
    file_path: str,
    content: str,
    format: str = "markdown",
    service: DocumentationService = Depends(get_documentation_service),
):
    """Create new documentation."""
    doc = await service.create_documentation(
        title=title,
        file_path=file_path,
        content=content,
        format=format,
    )
    return doc.to_dict()


@router.get("/{doc_id}", response_model=dict)
async def get_documentation(
    doc_id: str,
    service: DocumentationService = Depends(get_documentation_service),
):
    """Get documentation by ID."""
    doc = await service.get_documentation(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")
    return doc.to_dict()


@router.put("/{doc_id}", response_model=dict)
async def update_documentation(
    doc_id: str,
    content: str = None,
    title: str = None,
    service: DocumentationService = Depends(get_documentation_service),
):
    """Update documentation."""
    try:
        doc = await service.update_documentation(
            doc_id=doc_id,
            content=content,
            title=title,
        )
        return doc.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{doc_id}")
async def delete_documentation(
    doc_id: str,
    service: DocumentationService = Depends(get_documentation_service),
):
    """Delete documentation."""
    await service.delete_documentation(doc_id)
    return {"status": "deleted"}


@router.get("/", response_model=List[dict])
async def list_documentation(
    service: DocumentationService = Depends(get_documentation_service),
):
    """List all documentation."""
    docs = await service.list_documentation()
    return [doc.to_dict() for doc in docs]


@router.get("/tags/{tags}", response_model=List[dict])
async def find_by_tags(
    tags: str,
    service: DocumentationService = Depends(get_documentation_service),
):
    """Find documentation by tags (comma-separated)."""
    tag_list = [t.strip() for t in tags.split(",")]
    docs = await service.find_by_tags(tag_list)
    return [doc.to_dict() for doc in docs]


@router.get("/outdated/list", response_model=List[dict])
async def find_outdated(
    service: DocumentationService = Depends(get_documentation_service),
):
    """Find outdated documentation."""
    docs = await service.find_outdated()
    return [doc.to_dict() for doc in docs]

