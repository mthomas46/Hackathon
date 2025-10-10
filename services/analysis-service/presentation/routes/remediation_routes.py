"""Remediation Routes.

Automated documentation remediation and preview endpoints.
"""
from fastapi import APIRouter

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import AutomatedRemediationRequest, RemediationPreviewRequest

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["Remediation"])


@router.post("/remediate")
async def remediate_document_endpoint(req: AutomatedRemediationRequest):
    """Apply automated fixes to documentation issues.

    Intelligently identifies and fixes common documentation problems including
    formatting inconsistencies, grammar errors, terminology issues, and structural
    problems. Provides safety checks and rollback capabilities.

    Args:
        req: Remediation request with content and options

    Returns:
        Remediated content with backup and change report
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_automated_remediation(req)

        # Log successful remediation
        changes_applied = result.changes_applied
        safety_status = result.safety_status
        fire_and_forget(
            "info",
            "Automated remediation completed",
            SERVICE_NAME,
            {
                "changes_applied": changes_applied,
                "safety_status": safety_status,
                "content_length": len(result.original_content),
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Automated remediation completed with {changes_applied} changes",
            {
                "original_content": result.original_content,
                "remediated_content": result.remediated_content,
                "backup": result.backup,
                "report": result.report,
                "changes_applied": changes_applied,
                "safety_status": safety_status,
                "processing_time": result.processing_time,
                "remediation_timestamp": result.remediation_timestamp
            },
            changes_applied=changes_applied,
            safety_status=safety_status,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Automated remediation failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Automated remediation failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/remediate/preview")
async def preview_remediation_endpoint(req: RemediationPreviewRequest):
    """Preview automated remediation changes without applying them.

    Shows what fixes would be applied to documentation without making any actual
    changes, allowing users to review and approve modifications before execution.

    Args:
        req: Remediation preview request with content

    Returns:
        Preview of proposed fixes without applying them
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_remediation_preview(req)

        # Log successful preview
        fix_count = result.fix_count
        fire_and_forget(
            "info",
            "Remediation preview completed",
            SERVICE_NAME,
            {
                "preview_available": result.preview_available,
                "fix_count": fix_count,
                "content_length": len(req.content),
                "processing_time": result.estimated_processing_time
            }
        )

        return create_success_response(
            f"Remediation preview completed - {fix_count} fixes proposed",
            {
                "preview_available": result.preview_available,
                "proposed_fixes": result.proposed_fixes,
                "fix_count": fix_count,
                "estimated_processing_time": result.estimated_processing_time,
                "preview_timestamp": result.preview_timestamp
            },
            preview_available=result.preview_available,
            fix_count=fix_count,
            estimated_processing_time=result.estimated_processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Remediation preview failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Remediation preview failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )

