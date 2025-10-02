"""AI Insights API routes with comprehensive OpenAPI documentation."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()


class AIInsightResponse(BaseModel):
    """Response model for AI insight data."""
    id: str
    title: str
    description: str
    insight_type: str
    severity: str
    confidence_score: float
    data_source: str
    simulation_id: Optional[str]
    metrics: dict
    recommendations: List[str]
    is_actionable: bool
    action_taken: bool
    tags: List[str]
    created_at: Optional[datetime]


@router.get(
    "/",
    response_model=List[AIInsightResponse],
    summary="List AI insights with filtering",
    description="""
    Retrieve AI-generated insights with comprehensive filtering options.

    This endpoint provides access to AI-generated insights across all simulations,
    with filtering by type, severity, confidence, and other criteria.

    **Insight Types:**
    - `predictive`: Future trend predictions
    - `diagnostic`: Problem identification and root cause analysis
    - `prescriptive`: Recommended actions and solutions
    - `descriptive`: Current state descriptions and summaries
    - `anomaly`: Unusual pattern detection
    - `trend`: Long-term pattern analysis

    **Severity Levels:**
    - `low`: Minor observations
    - `medium`: Important findings requiring attention
    - `high`: Critical insights needing immediate action
    - `critical`: Urgent issues requiring immediate intervention

    **Filtering Options:**
    - Insight type and severity
    - Confidence score thresholds
    - Date ranges and simulation associations
    - Action status (actionable, action taken)
    """,
    response_description="List of AI insights matching filter criteria"
)
async def list_insights(
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    simulation_id: Optional[str] = Query(None, description="Filter by simulation ID"),
    actionable_only: bool = Query(False, description="Show only actionable insights"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
) -> List[AIInsightResponse]:
    """List AI insights with filtering."""
    # Mock response - in real implementation, query repository
    return []


@router.get(
    "/{insight_id}",
    response_model=AIInsightResponse,
    summary="Get AI insight details",
    description="""
    Retrieve detailed information about a specific AI insight.

    This endpoint provides comprehensive insight details including:
    - Insight content and analysis
    - Supporting data and evidence
    - Confidence metrics and validation
    - Recommended actions and rationale
    - Historical tracking information

    **Response includes:**
    - Complete insight metadata and content
    - Supporting data and evidence
    - Confidence scores and validation metrics
    - Action recommendations and status
    - Creation and update timestamps
    """,
    response_description="Detailed AI insight information"
)
async def get_insight(insight_id: str) -> AIInsightResponse:
    """Get AI insight details by ID."""
    raise HTTPException(status_code=404, detail="AI insight not found")


@router.post(
    "/{insight_id}/action",
    summary="Mark insight action taken",
    description="""
    Mark an AI insight as having had an action taken in response.

    This endpoint allows users to indicate that they have acted upon
    an AI insight recommendation, updating the insight's status for
    tracking and reporting purposes.

    **Action Tracking:**
    - Records timestamp of action
    - Updates insight status
    - Enables impact measurement
    - Supports audit trails

    **Use Cases:**
    - Risk mitigation implementation
    - Process improvements
    - Resource reallocations
    - Configuration changes
    """,
    response_description="Action recorded successfully"
)
async def mark_insight_action_taken(insight_id: str):
    """Mark that action has been taken on an insight."""
    raise HTTPException(status_code=404, detail="AI insight not found")
