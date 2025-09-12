"""Database models for Prompt Store service."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Prompt(BaseModel):
    """Core prompt model."""
    id: Optional[str] = None
    name: str
    category: str
    description: str = ""
    content: str
    variables: List[str] = []
    tags: List[str] = []
    is_active: bool = True
    is_template: bool = False  # For template-based prompts
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    parent_id: Optional[str] = None  # For forked prompts


class PromptVersion(BaseModel):
    """Prompt version history."""
    id: Optional[str] = None
    prompt_id: str
    version: int
    content: str
    variables: List[str]
    change_summary: str = ""
    change_type: str = "update"  # create, update, fork, rollback
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ABTest(BaseModel):
    """A/B testing configuration."""
    id: Optional[str] = None
    name: str
    description: str = ""
    prompt_a_id: str
    prompt_b_id: str
    test_metric: str = "response_quality"  # response_quality, token_usage, response_time, user_satisfaction
    is_active: bool = True
    traffic_split: float = 0.5  # Percentage of traffic to send to prompt B (0.0-1.0)
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    target_audience: Optional[Dict[str, Any]] = None  # User segmentation rules
    created_by: str


class ABTestResult(BaseModel):
    """A/B test results and analytics."""
    id: Optional[str] = None
    test_id: str
    prompt_id: str
    metric_value: float
    sample_size: int
    confidence_level: float = 0.0
    statistical_significance: bool = False
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromptUsage(BaseModel):
    """Individual prompt usage log."""
    id: Optional[str] = None
    prompt_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    service_name: str
    operation: str = "generate"  # generate, test, validate, etc.
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    response_time_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromptAnalytics(BaseModel):
    """Aggregated prompt analytics."""
    prompt_id: str
    total_usage: int = 0
    avg_response_time_ms: float = 0.0
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    performance_score: float = 0.0  # 0.0 to 1.0
    user_satisfaction: float = 0.0   # 0.0 to 5.0


class PromptTemplate(BaseModel):
    """Reusable prompt template."""
    id: Optional[str] = None
    name: str
    category: str
    description: str = ""
    template_content: str
    required_variables: List[str] = []
    optional_variables: List[str] = []
    tags: List[str] = []
    is_active: bool = True
    usage_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    """User session for A/B testing and personalization."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: str
    ab_assignments: Dict[str, str] = Field(default_factory=dict)  # test_id -> prompt_id
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# API MODELS
# ============================================================================

class PromptCreate(BaseModel):
    """Request model for creating prompts."""
    name: str
    category: str
    description: Optional[str] = ""
    content: str
    variables: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    is_template: Optional[bool] = False


class PromptUpdate(BaseModel):
    """Request model for updating prompts."""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ABTestCreate(BaseModel):
    """Request model for creating A/B tests."""
    name: str
    description: Optional[str] = ""
    prompt_a_id: str
    prompt_b_id: str
    test_metric: Optional[str] = "response_quality"
    traffic_split: Optional[float] = 0.5
    target_audience: Optional[Dict[str, Any]] = None


class PromptSearchFilters(BaseModel):
    """Filters for prompt search."""
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    is_active: Optional[bool] = None
    min_performance: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PromptFork(BaseModel):
    """Request model for forking a prompt."""
    new_name: str
    description: Optional[str] = None
    change_summary: str = "Forked from parent prompt"


class BulkOperation(BaseModel):
    """Request model for bulk operations."""
    operation: str  # activate, deactivate, delete, tag
    prompt_ids: List[str]
    parameters: Optional[Dict[str, Any]] = None


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PromptResponse(BaseModel):
    """Response model for prompt operations."""
    prompt: Prompt
    versions_count: int = 0
    analytics: Optional[PromptAnalytics] = None
    ab_tests: List[str] = []  # List of active A/B test IDs


class ABTestResponse(BaseModel):
    """Response model for A/B test operations."""
    test: ABTest
    prompt_a: Prompt
    prompt_b: Prompt
    current_results: Optional[Dict[str, Any]] = None
    winner: Optional[str] = None  # "A", "B", or None


class AnalyticsResponse(BaseModel):
    """Response model for analytics queries."""
    total_prompts: int
    active_prompts: int
    total_usage: int
    avg_performance: float
    top_performing_prompts: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    ab_test_summary: List[Dict[str, Any]]


class SearchResponse(BaseModel):
    """Response model for prompt search."""
    prompts: List[PromptResponse]
    total_count: int
    filters_applied: PromptSearchFilters
    suggestions: List[str] = []  # Similar prompts or categories


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def serialize_for_db(obj: Any) -> str:
    """Serialize object for database storage."""
    if isinstance(obj, list):
        return json.dumps(obj)
    elif isinstance(obj, dict):
        return json.dumps(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return str(obj)


def deserialize_from_db(value: str, target_type: type) -> Any:
    """Deserialize object from database storage."""
    if target_type == list:
        return json.loads(value) if value else []
    elif target_type == dict:
        return json.loads(value) if value else {}
    elif target_type == datetime:
        return datetime.fromisoformat(value) if value else None
    else:
        return value
