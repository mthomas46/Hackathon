"""
Configuration validation endpoints.

Provides API for validating configuration registry and detecting mismatches.
✅ PHASE 4: Observability - Real-time configuration health monitoring
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class ValidationResult(BaseModel):
    """Individual validation result."""
    check_name: str
    passed: bool
    severity: str  # "critical", "high", "medium", "low"
    message: str
    details: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None
    timestamp: str


class ValidationSummary(BaseModel):
    """Overall validation summary."""
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    critical_failures: int
    overall_status: str  # "healthy", "degraded", "critical"
    results: List[ValidationResult]


class ConfigDiff(BaseModel):
    """Configuration difference between registry and runtime."""
    category: str
    field: str
    registry_value: Any
    runtime_value: Any
    severity: str
    recommendation: str


# ============================================================================
# Validation Endpoints
# ============================================================================

@router.get(
    "/config/validate",
    summary="Run all configuration validations",
    description="Comprehensive validation of configuration registry against runtime state",
    response_model=ValidationSummary
)
async def validate_all_config(
    fail_fast: bool = Query(False, description="Stop at first critical failure")
):
    """
    Run all configuration validations.
    
    Validates:
    - Redis streams and consumer groups
    - Database connections and schema
    - ChromaDB collections
    - Service ports and networking
    - Configuration consistency
    
    Args:
        fail_fast: Stop at first critical failure
    
    Returns:
        Comprehensive validation summary with all results
    """
    try:
        from ...validation import ConfigValidator
        
        logger.info("Running comprehensive configuration validation...")
        validator = ConfigValidator()
        results = await validator.validate_all(fail_fast=fail_fast)
        
        # Convert to response model
        validation_results = []
        for result in results.results:
            validation_results.append(ValidationResult(
                check_name=result.check_name,
                passed=result.passed,
                severity=result.severity,
                message=result.message,
                details=result.details,
                remediation=result.remediation,
                timestamp=result.timestamp
            ))
        
        summary = results.summary()
        critical_failures = len(results.get_critical_failures())
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "critical"
        elif summary["failed"] > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        response = ValidationSummary(
            timestamp=datetime.now().isoformat(),
            total_checks=summary["total_checks"],
            passed=summary["passed"],
            failed=summary["failed"],
            warnings=summary["warnings"],
            critical_failures=critical_failures,
            overall_status=overall_status,
            results=validation_results
        )
        
        logger.info(
            f"Validation complete: {response.overall_status} "
            f"({response.passed}/{response.total_checks} passed)"
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation system error: {str(e)}"
        )


@router.get(
    "/config/validate/redis",
    summary="Validate Redis configuration",
    description="Validate Redis streams, consumer groups, and connectivity"
)
async def validate_redis_config():
    """
    Validate Redis configuration.
    
    Checks:
    - Redis connectivity
    - Stream existence
    - Consumer group configuration
    - Stream naming consistency
    
    Returns:
        Redis-specific validation results
    """
    try:
        from ...validation import ConfigValidator
        
        logger.info("Validating Redis configuration...")
        validator = ConfigValidator()
        
        # Run Redis-specific validations
        redis_conn = await validator.validate_redis_connection()
        redis_streams = await validator.validate_redis_streams()
        consumer_groups = await validator.validate_redis_consumer_groups()
        
        results = [redis_conn, redis_streams, consumer_groups]
        
        # Filter out None results
        results = [r for r in results if r is not None]
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "category": "Redis",
            "total_checks": len(results),
            "passed": passed,
            "failed": failed,
            "status": "healthy" if failed == 0 else "degraded",
            "checks": [
                {
                    "name": r.check_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "remediation": r.remediation
                }
                for r in results
            ]
        })
    
    except Exception as e:
        logger.error(f"Redis validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Redis validation error: {str(e)}"
        )


@router.get(
    "/config/validate/database",
    summary="Validate database configuration",
    description="Validate PostgreSQL connectivity and schema"
)
async def validate_database_config():
    """
    Validate database configuration.
    
    Checks:
    - Database connectivity
    - Table existence
    - Schema validation
    - Index configuration
    
    Returns:
        Database-specific validation results
    """
    try:
        from ...validation import ConfigValidator
        
        logger.info("Validating database configuration...")
        validator = ConfigValidator()
        
        # Run database-specific validations
        db_conn = await validator.validate_database_connection()
        db_names = await validator.validate_database_names()
        db_schema = await validator.validate_database_schema()
        
        results = [db_conn, db_names, db_schema]
        
        # Filter out None results
        results = [r for r in results if r is not None]
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "category": "Database",
            "total_checks": len(results),
            "passed": passed,
            "failed": failed,
            "status": "healthy" if failed == 0 else "degraded",
            "checks": [
                {
                    "name": r.check_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "remediation": r.remediation
                }
                for r in results
            ]
        })
    
    except Exception as e:
        logger.error(f"Database validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database validation error: {str(e)}"
        )


@router.get(
    "/config/validate/chromadb",
    summary="Validate ChromaDB configuration",
    description="Validate ChromaDB connectivity and collections"
)
async def validate_chromadb_config():
    """
    Validate ChromaDB configuration.
    
    Checks:
    - ChromaDB connectivity
    - Collection existence
    - Collection configuration
    
    Returns:
        ChromaDB-specific validation results
    """
    try:
        from ...validation import ConfigValidator
        
        logger.info("Validating ChromaDB configuration...")
        validator = ConfigValidator()
        
        # Run ChromaDB-specific validation
        chroma_result = await validator.validate_chromadb_collection()
        
        if chroma_result is None:
            return JSONResponse(content={
                "timestamp": datetime.now().isoformat(),
                "category": "ChromaDB",
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "status": "unknown",
                "checks": []
            })
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "category": "ChromaDB",
            "total_checks": 1,
            "passed": 1 if chroma_result.passed else 0,
            "failed": 0 if chroma_result.passed else 1,
            "status": "healthy" if chroma_result.passed else "degraded",
            "checks": [
                {
                    "name": chroma_result.check_name,
                    "passed": chroma_result.passed,
                    "severity": chroma_result.severity,
                    "message": chroma_result.message,
                    "remediation": chroma_result.remediation
                }
            ]
        })
    
    except Exception as e:
        logger.error(f"ChromaDB validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ChromaDB validation error: {str(e)}"
        )


@router.get(
    "/config/validate/services",
    summary="Validate service configuration",
    description="Validate service ports and networking"
)
async def validate_services_config():
    """
    Validate service configuration.
    
    Checks:
    - Port availability
    - Service connectivity
    - Network configuration
    
    Returns:
        Service-specific validation results
    """
    try:
        from ...validation import ConfigValidator
        
        logger.info("Validating service configuration...")
        validator = ConfigValidator()
        
        # Run service-specific validations
        ports_result = await validator.validate_service_ports()
        network_result = await validator.validate_network_connectivity()
        
        results = [ports_result, network_result]
        
        # Filter out None results
        results = [r for r in results if r is not None]
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "category": "Services",
            "total_checks": len(results),
            "passed": passed,
            "failed": failed,
            "status": "healthy" if failed == 0 else "degraded",
            "checks": [
                {
                    "name": r.check_name,
                    "passed": r.passed,
                    "severity": r.severity,
                    "message": r.message,
                    "remediation": r.remediation
                }
                for r in results
            ]
        })
    
    except Exception as e:
        logger.error(f"Service validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Service validation error: {str(e)}"
        )


@router.get(
    "/config/health",
    summary="Overall configuration health",
    description="Quick health check for configuration registry"
)
async def config_health():
    """
    Quick configuration health check.
    
    Provides a fast overview without running full validations.
    
    Returns:
        Configuration health status
    """
    try:
        from ...config.registry import get_registry
        
        registry = get_registry()
        
        # Quick checks
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "registry_loaded": True,
            "services": [],
            "issues": []
        }
        
        # Check service configuration
        try:
            services = []
            for service in registry.services:
                service_info = {
                    "name": service.name,
                    "enabled": service.enabled,
                    "port": service.port
                }
                services.append(service_info)
            health_status["services"] = services
        except Exception as e:
            health_status["issues"].append(f"Service config error: {str(e)}")
            health_status["status"] = "degraded"
        
        # Check Redis configuration
        try:
            redis_streams = len(registry.redis.streams.model_dump())
            health_status["redis_streams"] = redis_streams
        except Exception as e:
            health_status["issues"].append(f"Redis config error: {str(e)}")
            health_status["status"] = "degraded"
        
        # Check database configuration
        try:
            db_url_set = bool(registry.database.connection.url)
            health_status["database_configured"] = db_url_set
        except Exception as e:
            health_status["issues"].append(f"Database config error: {str(e)}")
            health_status["status"] = "degraded"
        
        return JSONResponse(content=health_status)
    
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "timestamp": datetime.now().isoformat(),
                "status": "critical",
                "registry_loaded": False,
                "error": str(e),
                "issues": ["Failed to load configuration registry"]
            }
        )


@router.get(
    "/config/diff",
    summary="Compare registry vs runtime configuration",
    description="Identify differences between registry and actual runtime state"
)
async def config_diff():
    """
    Compare registry configuration with runtime state.
    
    Identifies mismatches between what's configured and what's actually running.
    
    Returns:
        List of configuration differences with recommendations
    """
    try:
        from ...config.registry import get_registry
        from ...config import settings
        from ...utils.redis_client import get_redis_client
        
        registry = get_registry()
        redis_client = get_redis_client()
        
        differences: List[ConfigDiff] = []
        
        # Compare Redis configuration
        if redis_client.INGESTION_STREAM != registry.redis.streams.ingestion.name:
            differences.append(ConfigDiff(
                category="Redis",
                field="ingestion_stream",
                registry_value=registry.redis.streams.ingestion.name,
                runtime_value=redis_client.INGESTION_STREAM,
                severity="critical",
                recommendation="Restart service to sync with registry"
            ))
        
        if redis_client.CONSUMER_GROUP != registry.redis.streams.ingestion.consumer_group:
            differences.append(ConfigDiff(
                category="Redis",
                field="consumer_group",
                registry_value=registry.redis.streams.ingestion.consumer_group,
                runtime_value=redis_client.CONSUMER_GROUP,
                severity="critical",
                recommendation="Restart service and recreate consumer groups"
            ))
        
        # Compare database configuration
        registry_db_url = registry.database.connection.url
        if str(settings.database_url) != registry_db_url:
            differences.append(ConfigDiff(
                category="Database",
                field="connection_url",
                registry_value=registry_db_url,
                runtime_value=str(settings.database_url),
                severity="high",
                recommendation="Check environment variables and restart service"
            ))
        
        # Compare ChromaDB configuration
        if settings.chroma_collection_name != registry.chromadb.collections.main.name:
            differences.append(ConfigDiff(
                category="ChromaDB",
                field="collection_name",
                registry_value=registry.chromadb.collections.main.name,
                runtime_value=settings.chroma_collection_name,
                severity="high",
                recommendation="Restart service to sync collection name"
            ))
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "total_differences": len(differences),
            "critical": sum(1 for d in differences if d.severity == "critical"),
            "high": sum(1 for d in differences if d.severity == "high"),
            "medium": sum(1 for d in differences if d.severity == "medium"),
            "low": sum(1 for d in differences if d.severity == "low"),
            "differences": [d.model_dump() for d in differences],
            "recommendation": (
                "Critical mismatches detected - restart required"
                if any(d.severity == "critical" for d in differences)
                else "No critical issues" if not differences
                else "Review and apply recommendations"
            )
        })
    
    except Exception as e:
        logger.error(f"Config diff error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Config diff error: {str(e)}"
        )


@router.get(
    "/config/registry",
    summary="Get full registry configuration",
    description="Get the complete configuration registry (YAML structure)"
)
async def get_registry_config():
    """
    Get the complete configuration registry.
    
    Returns the full YAML structure as loaded from service_registry.yaml.
    
    Returns:
        Complete registry configuration
    """
    try:
        from ...config.registry import get_registry
        
        registry = get_registry()
        
        # Convert to dict for JSON serialization
        config_dict = registry.model_dump()
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "source_file": "config/service_registry.yaml",
            "environment": registry.environment,
            "configuration": config_dict
        })
    
    except Exception as e:
        logger.error(f"Registry retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Registry retrieval error: {str(e)}"
        )

