"""
Constants for expert-finder-service.

Centralizes all magic numbers and strings to improve maintainability.
Replaces ~20 lines of hardcoded values scattered throughout the codebase.
"""

# ============================================================================
# Scoring Weights (configurable via environment)
# ============================================================================

# Default weights for relevance scoring algorithm
# These define how much each factor contributes to the overall relevance score
DEFAULT_ROLE_WEIGHT = 0.30      # 30% - Role matching
DEFAULT_TOPIC_WEIGHT = 0.40     # 40% - Topic/interest matching (strongest signal)
DEFAULT_SERVICE_WEIGHT = 0.20   # 20% - Service subscriptions
DEFAULT_DOCUMENT_WEIGHT = 0.10  # 10% - Document relationships

# ============================================================================
# Validation Limits
# ============================================================================

MIN_QUERY_LENGTH = 1            # Minimum query text length (characters)
MAX_QUERY_LENGTH = 500          # Maximum query text length (characters)
MAX_RESULTS = 100               # Maximum number of results to return
DEFAULT_RESULTS = 10            # Default number of results if not specified

# ============================================================================
# SME (Subject Matter Expert) Thresholds
# ============================================================================

SME_MIN_DOCUMENTS = 10          # Minimum documents required to be considered SME
SME_MIN_SCORE = 0.7             # Minimum relevance score required for SME status

# ============================================================================
# HTTP Configuration
# ============================================================================

DEFAULT_TIMEOUT_SECONDS = 10.0  # Default HTTP request timeout
DEFAULT_RETRY_ATTEMPTS = 3      # Default number of retry attempts for failed requests

# ============================================================================
# Scoring Thresholds
# ============================================================================

# Relevance score thresholds for categorizing matches
EXCELLENT_MATCH_THRESHOLD = 0.8  # 80%+ = Excellent match
GOOD_MATCH_THRESHOLD = 0.6       # 60%+ = Good match
FAIR_MATCH_THRESHOLD = 0.4       # 40%+ = Fair match
# Below 40% = Poor match (typically not returned)

# ============================================================================
# Service URLs (defaults)
# ============================================================================

# Default URLs for external services
# These are typically overridden by environment variables
DEFAULT_USER_STORE_URL = "http://user-store:5120"
DEFAULT_DOC_STORE_URL = "http://doc-store:5130"
DEFAULT_SERVICE_STORE_URL = "http://external-service-store:5170"

# ============================================================================
# Service Metadata
# ============================================================================

SERVICE_NAME = "expert-finder-service"
SERVICE_VERSION = "1.0.0"
DEFAULT_SERVICE_PORT = 5160

# ============================================================================
# Match Quality Labels
# ============================================================================

MATCH_EXCELLENT = "excellent"   # 80%+ relevance
MATCH_GOOD = "good"            # 60-80% relevance
MATCH_FAIR = "fair"            # 40-60% relevance
MATCH_POOR = "poor"            # < 40% relevance

# ============================================================================
# Seniority Levels
# ============================================================================

SENIORITY_SENIOR = "senior"
SENIORITY_MID = "mid"
SENIORITY_JUNIOR = "junior"

# Seniority multipliers for role scoring
SENIORITY_MULTIPLIERS = {
    SENIORITY_SENIOR: 1.0,
    SENIORITY_MID: 0.7,
    SENIORITY_JUNIOR: 0.5
}

# ============================================================================
# Cache Configuration
# ============================================================================

DEFAULT_CACHE_TTL_SECONDS = 300  # 5 minutes cache TTL
DEFAULT_CACHE_MAX_SIZE = 100     # Maximum number of cached items

# ============================================================================
# Pagination
# ============================================================================

MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 10

# ============================================================================
# Logging
# ============================================================================

LOG_CORRELATION_ID_HEADER = "X-Correlation-ID"
LOG_REQUEST_ID_HEADER = "X-Request-ID"

# ============================================================================
# API Endpoints
# ============================================================================

# Standard endpoints (implemented in all services)
ENDPOINT_HEALTH = "/health"
ENDPOINT_ABOUT_ME = "/about-me"
ENDPOINT_ENDPOINTS = "/endpoints"
ENDPOINT_PROVIDER_CONSUMER = "/provider-consumer"
ENDPOINT_OPENAPI = "/openapi.json"
ENDPOINT_DEMOS = "/demos"
ENDPOINT_RUN_DEMO = "/run-demo"

# Business endpoints (service-specific)
ENDPOINT_FIND_EXPERTS = "/find-experts"
ENDPOINT_IDENTIFY_SMES = "/identify-smes"
ENDPOINT_FIND_TEAMMATES = "/find-teammates"
ENDPOINT_AGGREGATE_TEAM_EXPERTISE = "/aggregate-team-expertise"
ENDPOINT_SEARCH_BY_SERVICE = "/search-by-service"
ENDPOINT_SEARCH_BY_TOPIC = "/search-by-topic"

# ============================================================================
# Error Messages
# ============================================================================

ERROR_QUERY_EMPTY = "Query text cannot be empty"
ERROR_LIMIT_TOO_LOW = "Limit must be at least 1"
ERROR_LIMIT_TOO_HIGH = "Limit must not exceed {max}"
ERROR_ID_EMPTY = "{id_type} cannot be empty"
ERROR_COUNT_NEGATIVE = "{count_type} must be non-negative"
ERROR_SCORE_INVALID = "Score threshold must be between 0.0 and 1.0"
ERROR_SERVICE_UNAVAILABLE = "External service {service} is unavailable"
ERROR_INVALID_REQUEST = "Invalid request: {reason}"

# ============================================================================
# Success Messages
# ============================================================================

SUCCESS_EXPERTS_FOUND = "Found {count} experts matching query"
SUCCESS_SMES_IDENTIFIED = "Identified {count} subject matter experts"
SUCCESS_TEAMMATES_FOUND = "Found {count} potential teammates"
SUCCESS_TEAM_EXPERTISE_AGGREGATED = "Aggregated expertise for team {team_id}"

