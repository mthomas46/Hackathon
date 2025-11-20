"""
Template Management API Routes

Provides CRUD operations for documentation templates.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ...services.templates.template_manager import get_template_manager, TemplateValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


# Pydantic Models

class TemplateCreateRequest(BaseModel):
    """Request model for creating a template."""
    name: str = Field(..., description="Unique template name")
    category: str = Field(..., description="Template category")
    structure: Dict[str, Any] = Field(..., description="Template structure (sections, formatting, etc.)")
    description: Optional[str] = Field(None, description="Template description")
    target_framework: Optional[str] = Field(None, description="Target framework (e.g., 'scala_play', 'java_spring')")
    target_audience: Optional[str] = Field(None, description="Target audience (e.g., 'developers', 'operators')")
    render_options: Optional[Dict[str, Any]] = Field(None, description="Rendering options")
    is_public: bool = Field(False, description="Whether template is publicly accessible")


class TemplateUpdateRequest(BaseModel):
    """Request model for updating a template."""
    description: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    render_options: Optional[Dict[str, Any]] = None
    target_framework: Optional[str] = None
    target_audience: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Response model for template."""
    id: str
    name: str
    category: str
    version: int
    description: Optional[str]
    target_framework: Optional[str]
    target_audience: Optional[str]
    usage_count: int
    is_system_template: bool
    is_public: bool = False  # Default to False if not provided


class TemplateDetailResponse(TemplateResponse):
    """Detailed response model including structure."""
    structure: Dict[str, Any]
    render_options: Dict[str, Any]


# API Endpoints

@router.post(
    "/",
    response_model=Dict[str, str],
    summary="Create new template",
    description="Create a new user-supplied documentation template"
)
async def create_template(
    request: TemplateCreateRequest,
    created_by: str = Query("user", description="Creator username")
):
    """
    Create a new documentation template.
    
    The template structure will be validated before creation.
    """
    try:
        template_manager = get_template_manager()
        
        template_id = await template_manager.create_template(
            name=request.name,
            category=request.category,
            structure=request.structure,
            description=request.description,
            target_framework=request.target_framework,
            target_audience=request.target_audience,
            render_options=request.render_options,
            is_system_template=False,
            is_public=request.is_public,
            created_by=created_by
        )
        
        logger.info(f"Template '{request.name}' created by {created_by} (ID: {template_id})")
        
        return {
            "id": str(template_id),
            "message": f"Template '{request.name}' created successfully"
        }
        
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=f"Template validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/",
    response_model=List[TemplateResponse],
    summary="List templates",
    description="List all available templates with optional filtering"
)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    framework: Optional[str] = Query(None, description="Filter by target framework"),
    user_only: bool = Query(False, description="Only show user-created templates")
):
    """
    List available documentation templates.
    
    Can be filtered by category, framework, or limited to user-created templates only.
    """
    try:
        template_manager = get_template_manager()
        
        templates = await template_manager.list_templates(
            category=category,
            framework=framework,
            user_only=user_only
        )
        
        return templates
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{template_name}",
    response_model=TemplateDetailResponse,
    summary="Get template",
    description="Get detailed template information including structure"
)
async def get_template(
    template_name: str,
    category: Optional[str] = Query(None, description="Template category")
):
    """
    Get detailed information about a specific template.
    
    Includes the full template structure, sections, and validation rules.
    """
    try:
        template_manager = get_template_manager()
        
        template = await template_manager.load_template(
            template_name=template_name,
            category=category
        )
        
        return template
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommend/{category}",
    response_model=TemplateDetailResponse,
    summary="Get recommended template",
    description="Get the most suitable template based on criteria"
)
async def get_recommended_template(
    category: str,
    framework: Optional[str] = Query(None, description="Target framework"),
    audience: Optional[str] = Query(None, description="Target audience")
):
    """
    Get recommended template for given criteria.
    
    Returns the most popular/suitable template matching the criteria.
    """
    try:
        template_manager = get_template_manager()
        
        template = await template_manager.get_recommended_template(
            category=category,
            framework=framework,
            audience=audience
        )
        
        return template
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get recommended template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{template_id}",
    response_model=Dict[str, str],
    summary="Update template",
    description="Update template fields (system templates cannot be modified)"
)
async def update_template(
    template_id: UUID,
    request: TemplateUpdateRequest
):
    """
    Update an existing template.
    
    Only user-created templates can be updated. System templates are read-only.
    """
    try:
        template_manager = get_template_manager()
        
        # Filter out None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        await template_manager.update_template(template_id, **updates)
        
        logger.info(f"Template {template_id} updated")
        
        return {
            "id": str(template_id),
            "message": "Template updated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{template_id}",
    response_model=Dict[str, str],
    summary="Delete template",
    description="Soft delete a template (sets is_active=false)"
)
async def delete_template(
    template_id: UUID
):
    """
    Delete (deactivate) a template.
    
    This is a soft delete - the template is marked as inactive but not removed from database.
    """
    try:
        template_manager = get_template_manager()
        
        await template_manager.delete_template(template_id)
        
        logger.info(f"Template {template_id} deleted")
        
        return {
            "id": str(template_id),
            "message": "Template deleted successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{template_id}/validate",
    response_model=Dict[str, Any],
    summary="Validate template structure",
    description="Validate a template structure without saving it"
)
async def validate_template_structure(
    structure: Dict[str, Any] = Body(..., description="Template structure to validate")
):
    """
    Validate template structure.
    
    Useful for checking if a template is valid before creating/updating.
    """
    try:
        template_manager = get_template_manager()
        
        # Validation happens in _validate_template_structure
        template_manager._validate_template_structure(structure)
        
        return {
            "valid": True,
            "message": "Template structure is valid"
        }
        
    except TemplateValidationError as e:
        return {
            "valid": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/categories/list",
    response_model=List[str],
    summary="List template categories",
    description="Get list of all available template categories"
)
async def list_categories():
    """
    List all available template categories.
    """
    return [
        "api_reference",
        "runbook",
        "architecture",
        "component",
        "user_guide",
        "deployment",
        "troubleshooting",
        "security"
    ]

