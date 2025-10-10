"""Repository Routes.

Cross-repository analysis, connectivity analysis, and connector configuration.
"""
from fastapi import APIRouter

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import (
    CrossRepositoryAnalysisRequest,
    RepositoryConnectivityRequest,
    RepositoryConnectorConfigRequest
)

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["Cross-Repository Analysis"])


@router.post("/repositories/analyze")
async def analyze_cross_repository_endpoint(req: CrossRepositoryAnalysisRequest):
    """Analyze documentation across multiple repositories.

    Performs comprehensive cross-repository analysis to identify patterns,
    inconsistencies, redundancies, and opportunities for documentation
    improvement across an organization's entire repository ecosystem.

    Args:
        req: Cross-repository analysis request with repository list

    Returns:
        Comprehensive analysis results across all repositories
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_cross_repository_analysis(req)

        # Log successful analysis
        repository_count = result.repository_count
        overall_score = result.overall_score
        recommendations_count = len(result.recommendations)
        fire_and_forget(
            "info",
            "Cross-repository analysis completed",
            SERVICE_NAME,
            {
                "repository_count": repository_count,
                "overall_score": overall_score,
                "recommendations_count": recommendations_count,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Cross-repository analysis completed for {repository_count} repositories",
            {
                "repository_count": repository_count,
                "repositories_analyzed": result.repositories_analyzed,
                "analysis_types": result.analysis_types,
                "consistency_analysis": result.consistency_analysis,
                "coverage_analysis": result.coverage_analysis,
                "quality_analysis": result.quality_analysis,
                "redundancy_analysis": result.redundancy_analysis,
                "dependency_analysis": result.dependency_analysis,
                "overall_score": overall_score,
                "recommendations": result.recommendations,
                "processing_time": result.processing_time,
                "analysis_timestamp": result.analysis_timestamp
            },
            repository_count=repository_count,
            overall_score=overall_score,
            recommendations_count=recommendations_count,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Cross-repository analysis failed",
            SERVICE_NAME,
            {"repository_count": len(req.repositories), "error": str(e)}
        )

        return create_error_response(
            f"Cross-repository analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/repositories/connectivity")
async def analyze_repository_connectivity_endpoint(req: RepositoryConnectivityRequest):
    """Analyze connectivity and dependencies between repositories.

    Examines how repositories are connected through documentation references,
    shared dependencies, and integration points to understand the
    organizational documentation ecosystem.

    Args:
        req: Repository connectivity analysis request

    Returns:
        Connectivity analysis results with cross-references and integration points
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_repository_connectivity(req)

        # Log successful analysis
        repository_count = result.repository_count
        connectivity_score = result.connectivity_score
        cross_references_count = len(result.cross_references)
        fire_and_forget(
            "info",
            "Repository connectivity analysis completed",
            SERVICE_NAME,
            {
                "repository_count": repository_count,
                "connectivity_score": connectivity_score,
                "cross_references_count": cross_references_count,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Repository connectivity analysis completed for {repository_count} repositories",
            {
                "repository_count": repository_count,
                "cross_references": result.cross_references,
                "shared_dependencies": result.shared_dependencies,
                "integration_points": result.integration_points,
                "connectivity_score": connectivity_score,
                "processing_time": result.processing_time
            },
            repository_count=repository_count,
            connectivity_score=connectivity_score,
            cross_references_count=cross_references_count,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Repository connectivity analysis failed",
            SERVICE_NAME,
            {"repository_count": len(req.repositories), "error": str(e)}
        )

        return create_error_response(
            f"Repository connectivity analysis failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/repositories/connectors/config")
async def configure_repository_connector_endpoint(req: RepositoryConnectorConfigRequest):
    """Configure repository connectors for external systems.

    Sets up and configures connectors for GitHub, GitLab, Bitbucket,
    Azure DevOps, and other repository hosting platforms to enable
    seamless integration with external documentation sources.

    Args:
        req: Repository connector configuration request

    Returns:
        Configuration result with supported features and rate limits
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_repository_connector_config(req)

        # Log configuration
        configured = result.configured
        connector_type = result.connector_type
        features_count = len(result.supported_features)
        fire_and_forget(
            "info",
            "Repository connector configuration updated",
            SERVICE_NAME,
            {
                "connector_type": connector_type,
                "configured": configured,
                "supported_features_count": features_count
            }
        )

        return create_success_response(
            f"Repository connector {connector_type} {'configured' if configured else 'configuration failed'}",
            {
                "connector_type": connector_type,
                "configured": configured,
                "supported_features": result.supported_features,
                "rate_limits": result.rate_limits
            },
            connector_type=connector_type,
            configured=configured,
            supported_features_count=features_count
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Repository connector configuration failed",
            SERVICE_NAME,
            {"connector_type": req.connector_type, "error": str(e)}
        )

        return create_error_response(
            f"Repository connector configuration failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.get("/repositories/connectors")
async def get_supported_connectors_endpoint():
    """Get list of supported repository connectors.

    Returns information about all supported repository hosting platforms
    and their capabilities for cross-repository analysis integration.

    Returns:
        List of supported connectors with capabilities
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_supported_connectors()

        # Log request
        total_supported = result.total_supported
        fire_and_forget(
            "info",
            "Supported connectors retrieved",
            SERVICE_NAME,
            {"total_supported": total_supported}
        )

        return create_success_response(
            f"Retrieved {total_supported} supported repository connectors",
            {
                "connectors": result.connectors,
                "total_supported": total_supported
            },
            total_supported=total_supported
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Supported connectors retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Supported connectors retrieval failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.get("/repositories/frameworks")
async def get_analysis_frameworks_endpoint():
    """Get available cross-repository analysis frameworks.

    Returns information about all available analysis frameworks for
    cross-repository documentation analysis and their capabilities.

    Returns:
        List of available analysis frameworks
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_analysis_frameworks()

        # Log request
        total_frameworks = result.total_frameworks
        fire_and_forget(
            "info",
            "Analysis frameworks retrieved",
            SERVICE_NAME,
            {"total_frameworks": total_frameworks}
        )

        return create_success_response(
            f"Retrieved {total_frameworks} analysis frameworks",
            {
                "frameworks": result.frameworks,
                "total_frameworks": total_frameworks
            },
            total_frameworks=total_frameworks
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Analysis frameworks retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Analysis frameworks retrieval failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )

