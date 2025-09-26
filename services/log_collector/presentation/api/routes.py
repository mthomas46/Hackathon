"""API routes for log collector service."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ...application.commands import CollectLogCommand
from ...application.queries import ListLogsQuery
from ...domain.services import LogCollectionService
from ...infrastructure.persistence import LogRepository

# Create router
router = APIRouter(prefix="/api/v1", tags=["Log Collector API"])

# Request/Response models
class LogEntryRequest(BaseModel):
    """Request model for log entry."""
    service: str = Field(..., description="Service name that generated the log")
    level: str = Field(..., description="Log level (INFO, ERROR, WARNING, etc.)")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class LogQueryRequest(BaseModel):
    """Request model for log queries."""
    service: Optional[str] = Field(None, description="Filter by service name")
    level: Optional[str] = Field(None, description="Filter by log level")
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")

class FindingsResponse(BaseModel):
    """Response model for log findings."""
    findings: List[Dict[str, Any]] = Field(..., description="List of log findings")
    total_count: int = Field(..., description="Total number of findings")

class DetectorsResponse(BaseModel):
    """Response model for available detectors."""
    detectors: List[str] = Field(..., description="List of available detector names")

# Routes
@router.post("/logs", status_code=status.HTTP_201_CREATED, summary="Collect Log Entry", description="Submit a new log entry for processing and analysis.")
async def collect_log_entry(request: LogEntryRequest):
    """Collect a log entry for processing."""
    try:
        # Create command
        command = CollectLogCommand(
            service=request.service,
            level=request.level,
            message=request.message,
            metadata=request.metadata
        )

        # Execute command
        log_service = LogCollectionService()
        await log_service.collect_log(command)

        return {"message": "Log entry collected successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect log entry: {str(e)}"
        )

@router.get("/logs", summary="Query Logs", description="Query and retrieve log entries with optional filtering.")
async def query_logs(query: LogQueryRequest):
    """Query logs with filtering options."""
    try:
        # Create query
        log_query = ListLogsQuery(
            service=query.service,
            level=query.level,
            limit=query.limit
        )

        # Execute query
        repository = LogRepository()
        logs = await repository.find_logs(log_query)

        return {
            "logs": logs,
            "count": len(logs)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query logs: {str(e)}"
        )

@router.get("/findings", summary="Get Log Findings", description="Retrieve security findings and anomalies detected in logs.")
async def get_findings():
    """Get security findings from log analysis."""
    try:
        # Create query
        findings_query = GetFindingsQuery()

        # Execute query
        log_service = LogCollectionService()
        findings = await log_service.get_findings(findings_query)

        return FindingsResponse(
            findings=findings,
            total_count=len(findings)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get findings: {str(e)}"
        )

@router.get("/detectors", summary="List Detectors", description="Get list of available log analysis detectors.")
async def get_detectors():
    """Get available detectors."""
    try:
        log_service = LogCollectionService()
        detectors = await log_service.get_available_detectors()

        return DetectorsResponse(detectors=detectors)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detectors: {str(e)}"
        )

@router.post("/reports/generate", summary="Generate Report", description="Generate a comprehensive log analysis report.")
async def generate_report(report_config: Dict[str, Any]):
    """Generate a log analysis report."""
    try:
        log_service = LogCollectionService()
        report = await log_service.generate_report(report_config)

        return {
            "report_id": report.get("id"),
            "status": "generated",
            "report_url": report.get("url")
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
