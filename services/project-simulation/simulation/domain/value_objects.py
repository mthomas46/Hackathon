"""Value Objects - Immutable Domain Concepts.

This module defines value objects following Domain Driven Design principles.
Value objects are immutable and compared by value, not identity.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import hashlib


class ProjectType(Enum):
    """Project type value object."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MOBILE_APPLICATION = "mobile_application"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"
    DATA_SCIENCE = "data_science"
    DEVOPS_TOOL = "devops_tool"


class ComplexityLevel(Enum):
    """Project complexity level."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ProjectStatus(Enum):
    """Project status value object."""
    CREATED = "created"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SimulationStatus(Enum):
    """Simulation execution status."""
    CREATED = "created"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MilestoneStatus(Enum):
    """Milestone status value object."""
    UPCOMING = "upcoming"
    ACHIEVED = "achieved"
    MISSED = "missed"


@dataclass(frozen=True)
class DocumentReference:
    """Document reference value object."""
    document_id: str
    document_type: str
    relationship: str
    description: Optional[str] = None


class ExpertiseLevel(Enum):
    """Team member expertise levels."""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"
    LEAD = "lead"


class Phase(Enum):
    """Project phases."""
    PLANNING = "planning"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


class PhaseStatus(Enum):
    """Phase execution status."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    DELAYED = "delayed"


class Role(Enum):
    """Team member role value object."""
    DEVELOPER = "developer"
    QA = "qa"
    DESIGNER = "designer"
    UX_DESIGNER = "ux_designer"
    PRODUCT_MANAGER = "product_manager"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    ARCHITECT = "architect"
    DEVOPS = "devops"


class TeamMemberRole(Enum):
    """Team member role - alias for Role for backward compatibility."""
    DEVELOPER = "developer"
    QA = "qa"
    DESIGNER = "designer"
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    DEVOPS = "devops"


@dataclass(frozen=True)
class TeamMember:
    """Team member value object."""
    name: str
    role: Role
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation configuration value object."""
    project_type: ProjectType
    complexity: ComplexityLevel
    team_size: int = 5
    duration_days: int = 30


@dataclass(frozen=True)
class Milestone:
    """Project milestone value object."""
    name: str
    description: str
    due_date: datetime
    completed: bool = False


class DocumentType(Enum):
    """Document type value object."""
    # Existing types
    PROJECT_REQUIREMENTS = "project_requirements"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    USER_STORY = "user_story"
    TECHNICAL_DESIGN = "technical_design"
    CODE_REVIEW_COMMENTS = "code_review_comments"
    TEST_SCENARIOS = "test_scenarios"
    DEPLOYMENT_GUIDE = "deployment_guide"
    MAINTENANCE_DOCS = "maintenance_docs"
    CHANGE_LOG = "change_log"
    TEAM_RETROSPECTIVE = "team_retrospective"

    # Collaboration and Communication
    CONFLUENCE_PAGE = "confluence_page"
    JIRA_TICKET = "jira_ticket"
    GITHUB_PR = "github_pr"
    GITHUB_ISSUE = "github_issue"
    SLACK_MESSAGE = "slack_message"
    EMAIL = "email"
    MEETING_NOTES = "meeting_notes"

    # Project Management
    REQUIREMENTS_DOC = "requirements_doc"
    DESIGN_DOC = "design_doc"
    ARCHITECTURE_DOC = "architecture_doc"
    TEST_PLAN = "test_plan"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    CODE_REVIEW = "code_review"
    RUNBOOK = "runbook"
    INCIDENT_REPORT = "incident_report"
    ROADMAP = "roadmap"
    STATUS_REPORT = "status_report"
    RETROSPECTIVE = "retrospective"
    WIKI_PAGE = "wiki_page"

    # Technical Documentation
    API_DOCUMENTATION = "api_documentation"
    DATABASE_SCHEMA = "database_schema"
    CONFIGURATION_FILE = "configuration_file"
    LOG_FILE = "log_file"
    METRICS_REPORT = "metrics_report"
    PERFORMANCE_REPORT = "performance_report"
    SECURITY_AUDIT = "security_audit"
    COMPLIANCE_REPORT = "compliance_report"


class ServiceHealth(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EmailAddress:
    """Email address value object."""
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValueError("Invalid email address")
        if len(self.value) > 254:
            raise ValueError("Email address too long")

        # Validate that both local and domain parts are non-empty
        local_part, domain_part = self.value.split('@', 1)
        if not local_part or not domain_part:
            raise ValueError("Invalid email address")

        # Basic domain validation (must contain at least one dot)
        if '.' not in domain_part:
            raise ValueError("Invalid email address")

    @property
    def domain(self) -> str:
        """Get email domain."""
        return self.value.split('@')[1]

    @property
    def local_part(self) -> str:
        """Get email local part."""
        return self.value.split('@')[0]


@dataclass(frozen=True)
class ProjectName:
    """Project name value object."""
    value: str

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("Project name cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Project name too long")
        if not self._is_valid_name(self.value):
            raise ValueError("Project name contains invalid characters")

    def _is_valid_name(self, name: str) -> bool:
        """Check if project name is valid."""
        # Allow alphanumeric, spaces, hyphens, underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', name))

    def slug(self) -> str:
        """Convert to URL-friendly slug."""
        return self.value.lower().replace(' ', '-')


@dataclass(frozen=True)
class Duration:
    """Duration value object."""
    weeks: int
    days: int = 0

    def __post_init__(self):
        if self.weeks < 0 or self.days < 0:
            raise ValueError("Duration cannot be negative")
        if self.days >= 7:
            raise ValueError("Days should be less than 7, use weeks instead")

    @property
    def total_days(self) -> int:
        """Get total duration in days."""
        return (self.weeks * 7) + self.days

    @property
    def total_weeks(self) -> float:
        """Get total duration in weeks."""
        return self.weeks + (self.days / 7)

    def __add__(self, other: Duration) -> Duration:
        """Add two durations."""
        total_days = self.total_days + other.total_days
        weeks = total_days // 7
        days = total_days % 7
        return Duration(weeks=weeks, days=days)

    def __str__(self) -> str:
        if self.days == 0:
            return f"{self.weeks} week{'s' if self.weeks != 1 else ''}"
        elif self.weeks == 0:
            return f"{self.days} day{'s' if self.days != 1 else ''}"
        else:
            return f"{self.weeks} week{'s' if self.weeks != 1 else ''} {self.days} day{'s' if self.days != 1 else ''}"


@dataclass(frozen=True)
class Money:
    """Money value object."""
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in ["USD", "EUR", "GBP"]:
            raise ValueError("Unsupported currency")

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(self.amount * factor, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"


@dataclass(frozen=True)
class Percentage:
    """Percentage value object."""
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError("Percentage must be between 0 and 100")

    @classmethod
    def from_fraction(cls, numerator: float, denominator: float) -> Percentage:
        """Create percentage from fraction."""
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        return cls((numerator / denominator) * 100)

    def to_fraction(self) -> float:
        """Convert to fraction (0-1)."""
        return self.value / 100

    def __str__(self) -> str:
        return f"{self.value:.1f}%"


@dataclass(frozen=True)
class ServiceEndpoint:
    """Service endpoint value object."""
    url: str
    timeout_seconds: int = 30
    retries: int = 3

    def __post_init__(self):
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.retries < 0:
            raise ValueError("Retries cannot be negative")

    @property
    def base_url(self) -> str:
        """Get base URL without path."""
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @property
    def is_https(self) -> bool:
        """Check if endpoint uses HTTPS."""
        return self.url.startswith('https://')


@dataclass(frozen=True)
class ServiceHealthStatus:
    """Service health status value object."""
    service_name: str
    status: ServiceHealth
    response_time_ms: Optional[float] = None
    last_checked: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == ServiceHealth.HEALTHY

    def needs_attention(self) -> bool:
        """Check if service needs attention."""
        return self.status in [ServiceHealth.DEGRADED, ServiceHealth.UNHEALTHY]


@dataclass(frozen=True)
class DocumentId:
    """Document identifier value object."""
    value: str

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("Document ID cannot be empty")

    @classmethod
    def generate(cls) -> DocumentId:
        """Generate a new document ID."""
        import uuid
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DocumentMetadata:
    """Document metadata value object."""
    document_id: DocumentId
    title: str
    type: DocumentType
    author: str
    created_at: datetime
    word_count: int = 0
    complexity_score: float = 0.0
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Document title cannot be empty")
        if self.word_count < 0:
            raise ValueError("Word count cannot be negative")
        if not 0 <= self.complexity_score <= 1:
            raise ValueError("Complexity score must be between 0 and 1")

    @property
    def age_days(self) -> int:
        """Get document age in days."""
        return (datetime.now() - self.created_at).days

    def matches_tag(self, tag: str) -> bool:
        """Check if document has specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]


@dataclass(frozen=True)
class SimulationMetrics:
    """Simulation metrics value object."""
    total_documents: int
    total_tickets: int
    total_prs: int
    total_workflows: int
    execution_time_seconds: float
    average_response_time_ms: float
    error_count: int
    success_rate: Percentage

    @property
    def documents_per_second(self) -> float:
        """Get documents generated per second."""
        if self.execution_time_seconds == 0:
            return 0
        return self.total_documents / self.execution_time_seconds

    @property
    def workflows_per_minute(self) -> float:
        """Get workflows executed per minute."""
        minutes = self.execution_time_seconds / 60
        if minutes == 0:
            return 0
        return self.total_workflows / minutes

    def __str__(self) -> str:
        return (
            f"SimulationMetrics(docs={self.total_documents}, "
            f"workflows={self.total_workflows}, "
            f"time={self.execution_time_seconds:.1f}s, "
            f"success={self.success_rate})"
        )


@dataclass(frozen=True)
class EcosystemService:
    """Ecosystem service value object."""
    name: str
    endpoint: ServiceEndpoint
    health_check_endpoint: str = "/health"
    required_for_simulation: bool = True
    description: str = ""

    def get_health_check_url(self) -> str:
        """Get full health check URL."""
        base = self.endpoint.base_url.rstrip('/')
        endpoint = self.health_check_endpoint.lstrip('/')
        return f"{base}/{endpoint}"

    def __str__(self) -> str:
        return f"EcosystemService(name='{self.name}', url='{self.endpoint.url}')"


# Collection of all ecosystem services
ECOSYSTEM_SERVICES = [
    EcosystemService(
        name="doc_store",
        endpoint=ServiceEndpoint("http://doc_store:5010"),
        description="Document storage and versioning"
    ),
    EcosystemService(
        name="prompt_store",
        endpoint=ServiceEndpoint("http://prompt_store:5015"),
        description="Prompt management and versioning"
    ),
    EcosystemService(
        name="analysis_service",
        endpoint=ServiceEndpoint("http://analysis_service:5020"),
        description="Document analysis and insights"
    ),
    EcosystemService(
        name="llm_gateway",
        endpoint=ServiceEndpoint("http://llm_gateway:5055"),
        description="AI content generation"
    ),
    EcosystemService(
        name="orchestrator",
        endpoint=ServiceEndpoint("http://orchestrator:5000"),
        description="Workflow orchestration"
    ),
    EcosystemService(
        name="mock_data_generator",
        endpoint=ServiceEndpoint("http://mock_data_generator:5065"),
        description="Document generation service"
    ),
    EcosystemService(
        name="source_agent",
        endpoint=ServiceEndpoint("http://source_agent:5070"),
        description="Code analysis and documentation"
    ),
    EcosystemService(
        name="code_analyzer",
        endpoint=ServiceEndpoint("http://code_analyzer:5025"),
        description="Code quality analysis"
    ),
    EcosystemService(
        name="github_mcp",
        endpoint=ServiceEndpoint("http://github_mcp:5085"),
        description="GitHub integration"
    ),
    EcosystemService(
        name="bedrock_proxy",
        endpoint=ServiceEndpoint("http://bedrock_proxy:5090"),
        description="AWS AI services"
    ),
    EcosystemService(
        name="summarizer_hub",
        endpoint=ServiceEndpoint("http://summarizer_hub:5100"),
        description="Content summarization"
    ),
    EcosystemService(
        name="notification_service",
        endpoint=ServiceEndpoint("http://notification_service:5130"),
        description="Event notifications"
    ),
    EcosystemService(
        name="frontend",
        endpoint=ServiceEndpoint("http://frontend:3000"),
        description="Web interface"
    ),
    EcosystemService(
        name="discovery_agent",
        endpoint=ServiceEndpoint("http://discovery_agent:5140"),
        description="Service discovery"
    ),
    EcosystemService(
        name="log_collector",
        endpoint=ServiceEndpoint("http://log_collector:5150"),
        description="Centralized logging"
    ),
    EcosystemService(
        name="redis",
        endpoint=ServiceEndpoint("http://redis:6379"),
        health_check_endpoint="PING",
        description="Caching and session storage"
    ),
    EcosystemService(
        name="ollama",
        endpoint=ServiceEndpoint("http://ollama:11434"),
        description="Local AI models"
    ),
    EcosystemService(
        name="architecture_digitizer",
        endpoint=ServiceEndpoint("http://architecture_digitizer:5160"),
        description="Architecture diagrams"
    ),
    EcosystemService(
        name="interpreter",
        endpoint=ServiceEndpoint("http://interpreter:5170"),
        description="Cross-document analysis"
    ),
    EcosystemService(
        name="memory_agent",
        endpoint=ServiceEndpoint("http://memory_agent:5180"),
        description="Context management"
    ),
    EcosystemService(
        name="secure_analyzer",
        endpoint=ServiceEndpoint("http://secure_analyzer:5190"),
        description="Security analysis"
    )
]
