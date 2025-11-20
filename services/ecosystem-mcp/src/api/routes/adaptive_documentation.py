"""
Adaptive Documentation Generation API

Provides endpoints for generating documentation using adaptive features:
- Template-based generation
- Context discovery
- Prompt tracking
- Citation management
- Full transparency
"""

import logging
from typing import Dict, Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
from ...services.adaptive.transparency_logger import get_transparency_logger
from ...services.adaptive.citation_manager import get_citation_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documentation/adaptive", tags=["Adaptive Documentation"])


# Pydantic Models

class AdaptiveGenerationRequest(BaseModel):
    """Request model for adaptive documentation generation."""
    service_name: str = Field(..., description="Service to document")
    template_name: str = Field(..., description="Template name to use")
    category: str = Field(..., description="Template category")
    include_citations: bool = Field(True, description="Include source citations")
    citation_style: str = Field("endnotes", description="Citation style (endnotes, footnotes, inline)")
    transparency_mode: str = Field("normal", description="Transparency level (normal, verbose, minimal)")
    include_optional_sections: bool = Field(False, description="Include optional template sections")


class AdaptiveGenerationResponse(BaseModel):
    """Response model for adaptive documentation generation."""
    run_id: str
    service_name: str
    template_name: str
    content: str
    metadata: Dict[str, Any]
    transparency_report_url: str
    citations: list


# API Endpoints

@router.post(
    "/generate",
    response_model=AdaptiveGenerationResponse,
    summary="Generate adaptive documentation",
    description="Generate documentation using templates with full adaptive features"
)
async def generate_adaptive_documentation(
    request: AdaptiveGenerationRequest
):
    """
    Generate adaptive documentation.
    
    This endpoint orchestrates the complete adaptive documentation flow:
    1. Discovers repository context
    2. Loads and validates template
    3. Generates sections with context-aware prompts
    4. Tracks prompt effectiveness
    5. Adds source citations
    6. Logs all actions for transparency
    
    The generated documentation includes:
    - Template-structured content
    - Source citations
    - Generation metadata
    - Links to transparency logs
    """
    try:
        orchestrator = get_adaptive_orchestrator()
        
        result = await orchestrator.generate_adaptive_documentation(
            service_name=request.service_name,
            template_name=request.template_name,
            category=request.category,
            config={
                "include_citations": request.include_citations,
                "citation_style": request.citation_style,
                "transparency_mode": request.transparency_mode,
                "include_optional_sections": request.include_optional_sections
            }
        )
        
        logger.info(
            f"Adaptive documentation generated for {request.service_name} "
            f"using template {request.template_name}"
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate adaptive documentation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/transparency/{run_id}",
    response_model=Dict[str, Any],
    summary="Get transparency report",
    description="Get complete transparency report for a documentation run"
)
async def get_transparency_report(
    run_id: UUID,
    format: str = Query("json", description="Report format (json, markdown)")
):
    """
    Get transparency report for a documentation generation run.
    
    Returns complete audit trail including:
    - All actions performed
    - Prompts used
    - Sources queried
    - Validations performed
    - Timing information
    """
    try:
        transparency_logger = get_transparency_logger()
        
        if format == "markdown":
            report = await transparency_logger.format_transparency_report(run_id)
            return {
                "run_id": str(run_id),
                "format": "markdown",
                "content": report
            }
        else:
            log_entries = await transparency_logger.get_run_log(run_id)
            statistics = await transparency_logger.get_phase_statistics(run_id)
            
            return {
                "run_id": str(run_id),
                "format": "json",
                "log_entries": log_entries,
                "statistics": statistics
            }
            
    except Exception as e:
        logger.error(f"Failed to get transparency report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/transparency/{run_id}/failed",
    response_model=Dict[str, Any],
    summary="Get failed actions",
    description="Get all failed actions for a documentation run"
)
async def get_failed_actions(run_id: UUID):
    """
    Get all failed actions for a documentation run.
    
    Useful for debugging generation issues.
    """
    try:
        transparency_logger = get_transparency_logger()
        
        failed_actions = await transparency_logger.get_failed_actions(run_id)
        
        return {
            "run_id": str(run_id),
            "failed_count": len(failed_actions),
            "failed_actions": failed_actions
        }
        
    except Exception as e:
        logger.error(f"Failed to get failed actions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/citations/{artifact_id}",
    response_model=Dict[str, Any],
    summary="Get citations for artifact",
    description="Get all source citations for a generated documentation artifact"
)
async def get_artifact_citations(
    artifact_id: UUID,
    section: Optional[str] = Query(None, description="Filter by section")
):
    """
    Get citations for a documentation artifact.
    
    Returns all source documents that were used to generate the artifact,
    grouped by section with relevance scores.
    """
    try:
        citation_manager = get_citation_manager()
        
        citations = await citation_manager.get_citations_for_artifact(
            artifact_id=artifact_id,
            section_name=section
        )
        
        statistics = await citation_manager.get_citation_statistics(artifact_id)
        
        return {
            "artifact_id": str(artifact_id),
            "citations": citations,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Failed to get citations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/citations/{artifact_id}/verify",
    response_model=Dict[str, Any],
    summary="Verify citations",
    description="Verify citation quality and completeness"
)
async def verify_citations(
    artifact_id: UUID,
    min_relevance: float = Query(0.5, description="Minimum acceptable relevance score")
):
    """
    Verify citation quality for an artifact.
    
    Checks for:
    - Missing citations
    - Low relevance scores
    - Section coverage
    - Excerpt availability
    """
    try:
        citation_manager = get_citation_manager()
        
        verification = await citation_manager.verify_citations(
            artifact_id=artifact_id,
            min_relevance=min_relevance
        )
        
        return verification
        
    except Exception as e:
        logger.error(f"Failed to verify citations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/preview/{service_name}",
    response_model=Dict[str, Any],
    summary="Preview generation context",
    description="Preview what context would be used for documentation generation"
)
async def preview_generation_context(
    service_name: str,
    template_name: str,
    category: str
):
    """
    Preview context that would be used for documentation generation.
    
    Useful for understanding what information is available before generating.
    
    Returns:
    - Discovered repository context
    - Template structure
    - Framework-specific guidance
    - Available concepts and keywords
    """
    try:
        from ...services.adaptive.discovery_service import get_discovery_service
        from ...services.templates.template_manager import get_template_manager
        
        discovery = get_discovery_service()
        template_mgr = get_template_manager()
        
        # Discover context
        context = await discovery.discover_repository_context(service_name)
        guidance = await discovery.get_framework_specific_guidance(service_name)
        
        # Load template
        template = await template_mgr.load_template(template_name, category)
        
        return {
            "service_name": service_name,
            "template_name": template_name,
            "context": {
                "frameworks": context.get("frameworks", []),
                "languages": context.get("languages", {}),
                "architecture": context.get("architecture_type"),
                "concepts": context.get("concepts", []),
                "keywords": context.get("keywords", []),
                "framework_guidance": guidance
            },
            "template": {
                "name": template["name"],
                "category": template["category"],
                "sections": [
                    {
                        "name": s["name"],
                        "required": s["required"],
                        "subsections": s.get("subsections", [])
                    }
                    for s in template["structure"]["sections"]
                ]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to preview context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

