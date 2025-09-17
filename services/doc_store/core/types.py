"""Type definitions for Doc Store service.

Centralized type hints and aliases for better code maintainability.
"""
from typing import Dict, Any, List, Optional, Union, Protocol
from datetime import datetime


# Basic types
DocumentID = str
CorrelationID = str
ContentHash = str
AnalysisID = str
OperationID = str
TagName = str
RelationshipType = str

# Complex types
Metadata = Dict[str, Any]
AnalysisResult = Dict[str, Any]
SearchFilters = Dict[str, Any]
QualityFlags = List[str]

# Response types
ApiResponse = Dict[str, Any]
PaginatedResponse = Dict[str, Any]

# Domain-specific types
DocumentData = Dict[str, Any]
AnalysisData = Dict[str, Any]
BulkOperationData = Dict[str, Any]
RelationshipData = Dict[str, Any]
TagData = Dict[str, Any]

# Lifecycle types
LifecyclePhase = str  # 'active', 'archived', 'deleted'
PolicyCondition = Dict[str, Any]
PolicyAction = Dict[str, Any]

# Cache types
CacheKey = str
CacheTags = List[str]

# Notification types
WebhookID = str
EventType = str
NotificationPayload = Dict[str, Any]

# Search types
SearchQuery = str
SearchResults = List[Dict[str, Any]]

# Analytics types
AnalyticsPeriod = str  # 'day', 'week', 'month', 'year'
AnalyticsGroupBy = str  # 'analyzer', 'model', 'document', 'date'

# Protocol for handlers
class HandlerProtocol(Protocol):
    """Protocol for request handlers."""
    async def handle(self, request: Any) -> ApiResponse:
        """Handle a request."""
        ...


# Protocol for repositories
class RepositoryProtocol(Protocol):
    """Protocol for data repositories."""
    def get_by_id(self, id: str) -> Optional[Any]:
        """Get entity by ID."""
        ...

    def save(self, entity: Any) -> None:
        """Save entity."""
        ...

    def delete(self, id: str) -> None:
        """Delete entity by ID."""
        ...


# Protocol for services
class ServiceProtocol(Protocol):
    """Protocol for business services."""
    def process(self, data: Any) -> Any:
        """Process business logic."""
        ...


# Utility type aliases
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]

# Database result types
DBRow = Dict[str, Any]
DBResult = Union[None, DBRow, List[DBRow]]

# HTTP types
HTTPStatus = int
HTTPHeaders = Dict[str, str]
HTTPRequest = Dict[str, Any]
HTTPResponse = Dict[str, Any]

# Configuration types
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any]]
ServiceConfig = Dict[str, ConfigValue]

# Error types
ErrorCode = str
ErrorMessage = str
ErrorDetails = Dict[str, Any]
