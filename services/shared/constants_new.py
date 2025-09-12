"""Shared constants and enums to reduce magic strings and numbers."""

from enum import Enum


# ============================================================================
# HTTP STATUS CODES
# ============================================================================

class HTTPStatus:
    """HTTP status codes with descriptive names."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ============================================================================
# ENVIRONMENT VARIABLE CONSTANTS
# ============================================================================

# Consolidated EnvVars class
class EnvVars:
    """Common environment variable names."""

    # Basic environment
    ENVIRONMENT = "ENVIRONMENT"
    DEBUG = "DEBUG"
    DATABASE_URL = "DATABASE_URL"
    REDIS_URL = "REDIS_URL"
    SECRET_KEY = "SECRET_KEY"

    # HTTP Headers
    CORRELATION_ID_HEADER = "X-Correlation-ID"

    # Service URLs
    LOG_COLLECTOR_URL_ENV = "LOG_COLLECTOR_URL"
    REPORTING_URL_ENV = "REPORTING_URL"
    CONSISTENCY_ENGINE_URL_ENV = "CONSISTENCY_ENGINE_URL"
    ORCHESTRATOR_URL = "ORCHESTRATOR_URL"
    ORCHESTRATOR_URL_ENV = "ORCHESTRATOR_URL"
    GITHUB_AGENT_URL_ENV = "GITHUB_AGENT_URL"
    JIRA_AGENT_URL_ENV = "JIRA_AGENT_URL"
    CONFLUENCE_AGENT_URL_ENV = "CONFLUENCE_AGENT_URL"
    SWAGGER_AGENT_URL_ENV = "SWAGGER_AGENT_URL"
    SECURE_ANALYZER_URL_ENV = "SECURE_ANALYZER_URL"
    SUMMARIZER_HUB_URL_ENV = "SUMMARIZER_HUB_URL"
    DOC_STORE_URL = "DOC_STORE_URL"
    DOC_STORE_URL_ENV = "DOC_STORE_URL"
    ANALYSIS_SERVICE_URL = "ANALYSIS_SERVICE_URL"
    SOURCE_AGENT_URL = "SOURCE_AGENT_URL"
    PROMPT_STORE_URL = "PROMPT_STORE_URL"
    INTERPRETER_URL = "INTERPRETER_URL"

    # Provider retry/rate config
    JIRA_RETRY_ATTEMPTS_ENV = "JIRA_RETRY_ATTEMPTS"
    CONFLUENCE_RETRY_ATTEMPTS_ENV = "CONFLUENCE_RETRY_ATTEMPTS"
    GITHUB_RETRY_ATTEMPTS_ENV = "GITHUB_RETRY_ATTEMPTS"

    # Configuration
    HTTP_TIMEOUT = "HTTP_CLIENT_TIMEOUT"
    LOG_LEVEL = "LOG_LEVEL"


# ============================================================================
# SERVICE NAMES AND PORTS
# ============================================================================

class ServiceNames:
    """Standardized service names."""
    ORCHESTRATOR = "orchestrator"
    ANALYSIS_SERVICE = "analysis-service"
    DOC_STORE = "doc-store"
    SOURCE_AGENT = "source-agent"
    PROMPT_STORE = "prompt-store"
    INTERPRETER = "interpreter"
    CLI = "cli"
    FRONTEND = "frontend"
    DISCOVERY_AGENT = "discovery-agent"
    MEMORY_AGENT = "memory-agent"
    SECURE_ANALYZER = "secure-analyzer"
    SUMMARIZER_HUB = "summarizer-hub"
    CODE_ANALYZER = "code-analyzer"
    NOTIFICATION_SERVICE = "notification-service"
    LOG_COLLECTOR = "log-collector"
    BEDROCK_PROXY = "bedrock-proxy"


class ServicePorts:
    """Default service ports."""
    ORCHESTRATOR = 5000
    ANALYSIS_SERVICE = 5020
    DOC_STORE = 5010
    SOURCE_AGENT = 5000
    PROMPT_STORE = 5110
    INTERPRETER = 5120
    CLI = 5130


# ============================================================================
# STATUS ENUMS
# ============================================================================

class HealthStatus(str, Enum):
    """Health status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisStatus(str, Enum):
    """Analysis operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# ERROR CODES
# ============================================================================

class ErrorCodes:
    """Standardized error codes."""
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    DOCUMENT_NOT_FOUND = "document_not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    SERVICE_UNAVAILABLE = "service_unavailable"
    DATABASE_ERROR = "database_error"
    ANALYSIS_FAILED = "analysis_failed"
    REPORT_GENERATION_FAILED = "report_generation_failed"
    DOCUMENT_FETCH_FAILED = "document_fetch_failed"
    CATEGORY_RETRIEVAL_FAILED = "category_retrieval_failed"
    NATURAL_LANGUAGE_ANALYSIS_FAILED = "natural_language_analysis_failed"


# ============================================================================
# COMMON LIMITS AND TIMEOUTS
# ============================================================================

class Limits:
    """Size and count limits."""
    MAX_FILE_SIZE_MB = 100
    MAX_REQUEST_SIZE_MB = 50
    MAX_STRING_LENGTH = 10000
    MAX_LIST_ITEMS = 1000
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 1000


class Timeouts:
    """Timeout constants in seconds."""
    DEFAULT_REQUEST_TIMEOUT = 30
    HEALTH_CHECK_TIMEOUT = 5
    DATABASE_CONNECTION_TIMEOUT = 10
    EXTERNAL_API_TIMEOUT = 15


# ============================================================================
# COMMON PATTERNS AND REGEX
# ============================================================================

class Patterns:
    """Common regex patterns."""
    EMAIL = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    URL = r"https?://[^\s]+"
    UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    VARIABLE = r"\{([^}]+)\}"




# ============================================================================
# CONTENT TYPES AND HEADERS
# ============================================================================

class ContentTypes:
    """Common content type headers."""
    JSON = "application/json"
    FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"


class Headers:
    """Standard HTTP headers."""
    CONTENT_TYPE = "Content-Type"
    AUTHORIZATION = "Authorization"
    X_REQUEST_ID = "X-Request-ID"
    X_CORRELATION_ID = "X-Correlation-ID"


# Correlation ID header (backward compatibility)
CORRELATION_ID_HEADER = Headers.X_CORRELATION_ID
