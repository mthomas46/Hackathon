"""API Request and Response models for project-simulation service.

This module contains all Pydantic models used for API request/response validation
and serialization in the project-simulation service.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateSimulationRequest(BaseModel):
    """Request model for creating a simulation."""

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        None, max_length=500, description="Project description"
    )
    type: str = Field(
        "web_application",
        pattern="^(web_application|api_service|mobile_app|data_science|devops_tool)$",
        description="Project type",
    )
    team_size: int = Field(5, ge=1, le=20, description="Team size")
    complexity: str = Field(
        "medium", pattern="^(simple|medium|complex)$", description="Project complexity"
    )
    duration_weeks: int = Field(8, ge=1, le=52, description="Duration in weeks")
    team_members: Optional[list] = Field(None, description="Optional team members")
    phases: Optional[list] = Field(None, description="Optional project phases")


class SimulationResponse(BaseModel):
    """Response model for simulation operations."""

    success: bool
    message: str
    simulation_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class CreateSimulationFromConfigRequest(BaseModel):
    """Request model for creating simulation from configuration file."""

    config_file_path: str = Field(..., description="Path to configuration file")


class CreateSampleConfigRequest(BaseModel):
    """Request model for creating sample configuration file."""

    file_path: str = Field(
        ..., description="Path where sample config should be created"
    )
    project_name: str = Field(
        "Sample E-commerce Platform", description="Project name for sample config"
    )


class ValidateConfigRequest(BaseModel):
    """Request model for validating configuration file."""

    config_file_path: str = Field(
        ..., description="Path to configuration file to validate"
    )


class GenerateReportsRequest(BaseModel):
    """Request model for generating simulation reports."""

    report_types: List[str] = Field(
        default_factory=lambda: [
            "executive_summary",
            "technical_report",
            "workflow_analysis",
        ],
        description="Types of reports to generate",
    )


class ExportReportRequest(BaseModel):
    """Request model for exporting simulation reports."""

    report_type: str = Field(..., description="Type of report to export")
    format: str = Field("json", description="Export format (json, html, markdown, pdf)")
    output_path: Optional[str] = Field(
        None, description="Optional output path for the exported report"
    )


class StopUIMonitoringRequest(BaseModel):
    """Request model for stopping UI monitoring."""

    success: bool = Field(
        True, description="Whether the simulation completed successfully"
    )


class ReplayEventsRequest(BaseModel):
    """Request model for replaying simulation events."""

    event_types: Optional[List[str]] = Field(
        None, description="Types of events to replay"
    )
    start_time: Optional[str] = Field(
        None, description="Start time for replay (ISO format)"
    )
    end_time: Optional[str] = Field(
        None, description="End time for replay (ISO format)"
    )
    tags: Optional[List[str]] = Field(None, description="Tags to filter events")
    speed_multiplier: float = Field(
        1.0, description="Speed multiplier for replay (1.0 = real-time)"
    )
    include_system_events: bool = Field(
        False, description="Include system events in replay"
    )
    max_events: Optional[int] = Field(
        None, description="Maximum number of events to replay"
    )


class CleanupEventsRequest(BaseModel):
    """Request model for cleaning up old events."""

    days_old: int = Field(30, description="Remove events older than this many days")
