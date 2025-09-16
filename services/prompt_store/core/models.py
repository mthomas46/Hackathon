"""Core models for Prompt Store service.

Pydantic models for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# REQUEST MODELS
# ============================================================================

class PromptCreate(BaseModel):
    """Request model for creating prompts."""
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = ""
    content: str = Field(..., min_length=1)
    variables: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    is_template: Optional[bool] = False


class PromptUpdate(BaseModel):
    """Request model for updating prompts."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    lifecycle_status: Optional[str] = None


class ABTestCreate(BaseModel):
    """Request model for creating A/B tests."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    prompt_a_id: str
    prompt_b_id: str
    test_metric: Optional[str] = "response_quality"
    traffic_split: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    target_audience: Optional[Dict[str, Any]] = None


class PromptSearchFilters(BaseModel):
    """Filters for prompt search."""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    is_active: Optional[bool] = None
    is_template: Optional[bool] = None
    lifecycle_status: Optional[str] = None
    min_performance: Optional[float] = Field(None, ge=0.0, le=1.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PromptFork(BaseModel):
    """Request model for forking a prompt."""
    new_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    change_summary: str = Field(..., min_length=1)


class BulkOperationCreate(BaseModel):
    """Request model for bulk operations."""
    operation: str  # create_prompts, update_prompts, delete_prompts, tag_prompts
    prompt_ids: List[str]
    parameters: Optional[Dict[str, Any]] = None


class PromptRelationshipCreate(BaseModel):
    """Request model for creating prompt relationships."""
    target_prompt_id: str
    relationship_type: str  # extends, references, alternative, similar
    strength: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class WebhookCreate(BaseModel):
    """Request model for creating webhooks."""
    name: str = Field(..., min_length=1, max_length=100)
    url: str
    events: List[str]  # prompt.created, prompt.updated, ab_test.completed, etc.
    secret: Optional[str] = None
    is_active: Optional[bool] = True
    retry_count: Optional[int] = Field(3, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(30, ge=1, le=300)


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PromptResponse(BaseModel):
    """Response model for prompt operations."""
    id: str
    name: str
    category: str
    description: str
    content: str
    variables: List[str]
    tags: List[str]
    is_active: bool
    is_template: bool
    lifecycle_status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int
    parent_id: Optional[str]
    performance_score: float
    usage_count: int
    versions_count: int = 0
    analytics: Optional[Dict[str, Any]] = None
    ab_tests: List[str] = []  # List of active A/B test IDs
    relationships: List[Dict[str, Any]] = []


class ABTestResponse(BaseModel):
    """Response model for A/B test operations."""
    id: str
    name: str
    description: str
    prompt_a_id: str
    prompt_b_id: str
    test_metric: str
    is_active: bool
    traffic_split: float
    start_date: datetime
    end_date: Optional[datetime]
    target_audience: Dict[str, Any]
    created_by: str
    winner: Optional[str]
    prompt_a: PromptResponse
    prompt_b: PromptResponse
    current_results: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    """Response model for analytics queries."""
    total_prompts: int
    active_prompts: int
    total_usage: int
    avg_performance: float
    avg_response_time_ms: float
    top_performing_prompts: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    ab_test_summary: List[Dict[str, Any]]
    category_distribution: Dict[str, int]
    tag_distribution: Dict[str, int]
    performance_trends: List[Dict[str, Any]]


class SearchResponse(BaseModel):
    """Response model for prompt search."""
    prompts: List[PromptResponse]
    total_count: int
    filters_applied: PromptSearchFilters
    suggestions: List[str] = []  # Similar prompts or categories


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    operation_id: str
    operation_type: str
    status: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    errors: List[str]
    results: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class WebhookResponse(BaseModel):
    """Response model for webhook operations."""
    id: str
    name: str
    url: str
    events: List[str]
    is_active: bool
    retry_count: int
    timeout_seconds: int
    created_at: datetime
    last_delivery: Optional[datetime]
    delivery_count: int = 0
    failure_count: int = 0


class NotificationResponse(BaseModel):
    """Response model for notification queries."""
    total_events: int
    recent_events: List[Dict[str, Any]]
    webhook_stats: Dict[str, Any]
    event_types: Dict[str, int]


# ============================================================================
# LIFECYCLE MANAGEMENT MODELS
# ============================================================================

class PromptLifecycleUpdate(BaseModel):
    """Request model for updating prompt lifecycle status."""
    status: str
    reason: Optional[str] = None


class LifecycleStatusResponse(BaseModel):
    """Response model for prompts by lifecycle status."""
    status: str
    prompts: List[Dict[str, Any]]
    count: int
    limit: int
    offset: int


class LifecycleHistoryResponse(BaseModel):
    """Response model for lifecycle history."""
    prompt_id: str
    current_status: str
    lifecycle_history: List[Dict[str, Any]]
    history_count: int


class LifecycleCountsResponse(BaseModel):
    """Response model for lifecycle status counts."""
    status_counts: Dict[str, int]
    total_prompts: int
    last_updated: str


class LifecycleTransitionValidation(BaseModel):
    """Response model for transition validation."""
    valid: bool
    current_status: str
    requested_status: str
    reason: Optional[str] = None


class BulkLifecycleUpdate(BaseModel):
    """Request model for bulk lifecycle updates."""
    prompt_ids: List[str]
    status: str
    reason: Optional[str] = None


# ============================================================================
# RELATIONSHIPS MODELS
# ============================================================================

class RelationshipUpdate(BaseModel):
    """Request model for updating relationship properties."""
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class RelationshipGraphRequest(BaseModel):
    """Request model for relationship graph queries."""
    depth: Optional[int] = Field(2, ge=1, le=5)
    include_prompt_details: Optional[bool] = True


class RelatedPromptsFilter(BaseModel):
    """Request model for filtering related prompts."""
    relationship_types: Optional[List[str]] = None
    min_strength: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    direction: Optional[str] = Field("both", pattern="^(both|outgoing|incoming)$")


class RelationshipValidationRequest(BaseModel):
    """Request model for relationship validation."""
    source_prompt_id: str
    target_prompt_id: str
    relationship_type: str
