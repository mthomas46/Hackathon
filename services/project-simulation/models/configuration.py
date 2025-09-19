"""Configuration models for Project Simulation Service.

This module defines all the Pydantic models used for configuration files,
simulation parameters, and API responses in the project simulation service.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID


class ProjectType(str, Enum):
    """Types of projects that can be simulated."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MOBILE_APPLICATION = "mobile_application"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"


class TeamRole(str, Enum):
    """Team member roles in the simulated project."""
    PRODUCT_MANAGER = "product_manager"
    TECHNICAL_LEAD = "technical_lead"
    SENIOR_DEVELOPER = "senior_developer"
    DEVELOPER = "developer"
    JUNIOR_DEVELOPER = "junior_developer"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DESIGNER = "designer"
    BUSINESS_ANALYST = "business_analyst"


class ExpertiseLevel(str, Enum):
    """Expertise levels for team members."""
    EXPERT = "expert"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


class CommunicationStyle(str, Enum):
    """Communication styles for team members."""
    VERBOSE = "verbose"
    CONCISE = "concise"
    TECHNICAL = "technical"
    BUSINESS_FOCUSED = "business_focused"
    COLLABORATIVE = "collaborative"


class WorkStyle(str, Enum):
    """Work styles for team members."""
    STRUCTURED = "structured"
    FLEXIBLE = "flexible"
    INNOVATIVE = "innovative"
    METHODICAL = "methodical"
    FAST_PACED = "fast_paced"


class DocumentType(str, Enum):
    """Types of documents that can be generated."""
    CONFLUENCE_PAGE = "confluence_page"
    DESIGN_DOCUMENT = "design_document"
    API_SPECIFICATION = "api_specification"
    PITCH_DOCUMENT = "pitch_document"
    USER_STORY = "user_story"
    JIRA_TICKET = "jira_ticket"
    GITHUB_PR = "github_pr"
    CODE_REVIEW = "code_review"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    TEST_PLAN = "test_plan"


class SimulationPhase(str, Enum):
    """Phases of the development lifecycle."""
    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class EventType(str, Enum):
    """Types of events that can occur during simulation."""
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    DOCUMENT_CREATED = "document_created"
    TICKET_CREATED = "ticket_created"
    PR_CREATED = "pr_created"
    WORKFLOW_EXECUTED = "workflow_executed"
    ANALYSIS_COMPLETED = "analysis_completed"
    ERROR_OCCURRED = "error_occurred"


# Configuration Models


class ServiceEndpoint(BaseModel):
    """Configuration for an ecosystem service endpoint."""
    url: str = Field(..., description="Base URL of the service")
    timeout: int = Field(30, description="Request timeout in seconds")
    retries: int = Field(3, description="Number of retry attempts")
    health_check_path: str = Field("/health", description="Health check endpoint path")


class EcosystemServices(BaseModel):
    """Configuration for all ecosystem services."""
    doc_store: ServiceEndpoint
    prompt_store: ServiceEndpoint
    orchestrator: ServiceEndpoint
    analysis_service: ServiceEndpoint
    llm_gateway: ServiceEndpoint
    notification_service: Optional[ServiceEndpoint] = None
    frontend: Optional[ServiceEndpoint] = None


class TeamMemberProfile(BaseModel):
    """Profile configuration for a simulated team member."""
    name: str = Field(..., description="Full name of the team member")
    role: TeamRole = Field(..., description="Primary role in the team")
    expertise_level: ExpertiseLevel = Field(..., description="Level of technical expertise")
    communication_style: CommunicationStyle = Field(..., description="How they communicate")
    work_style: WorkStyle = Field(..., description="Their preferred work approach")
    specialization: List[str] = Field(default_factory=list, description="Technical specializations")
    productivity_multiplier: float = Field(1.0, description="Productivity factor (0.5-2.0)")

    @validator('productivity_multiplier')
    def validate_productivity(cls, v):
        if not 0.5 <= v <= 2.0:
            raise ValueError('Productivity multiplier must be between 0.5 and 2.0')
        return v


class TimelinePhase(BaseModel):
    """Configuration for a phase in the project timeline."""
    name: str = Field(..., description="Name of the phase")
    duration_days: int = Field(..., description="Duration of the phase in days")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisite phases")
    team_allocation: Dict[TeamRole, int] = Field(default_factory=dict, description="Team members needed by role")


class ProjectConfiguration(BaseModel):
    """Main configuration model for a simulation project."""
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Project description")
    type: ProjectType = Field(..., description="Type of project")
    duration_weeks: int = Field(..., description="Total project duration in weeks")
    team_size: int = Field(..., description="Number of team members")
    complexity: str = Field("medium", description="Project complexity (low/medium/high)")
    budget: Optional[float] = Field(None, description="Project budget in dollars")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    team_members: List[TeamMemberProfile] = Field(..., description="Team member profiles")
    timeline_phases: List[TimelinePhase] = Field(..., description="Project timeline phases")
    services: EcosystemServices = Field(..., description="Ecosystem service endpoints")

    @validator('complexity')
    def validate_complexity(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('Complexity must be low, medium, or high')
        return v

    @validator('duration_weeks')
    def validate_duration(cls, v):
        if not 1 <= v <= 52:
            raise ValueError('Duration must be between 1 and 52 weeks')
        return v


class SimulationParameters(BaseModel):
    """Parameters that control the simulation execution."""
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    speed_multiplier: float = Field(1.0, description="Speed up simulation (1.0 = real-time)")
    enable_real_time_feed: bool = Field(True, description="Enable real-time event streaming")
    enable_analysis: bool = Field(True, description="Run analysis workflows during simulation")
    enable_notifications: bool = Field(False, description="Send notifications during simulation")
    max_concurrent_workflows: int = Field(5, description="Maximum concurrent workflow executions")
    output_directory: str = Field("./simulation_output", description="Directory for output files")

    @validator('speed_multiplier')
    def validate_speed(cls, v):
        if not 0.1 <= v <= 10.0:
            raise ValueError('Speed multiplier must be between 0.1 and 10.0')
        return v


# Runtime Models


class SimulationEvent(BaseModel):
    """An event that occurs during simulation execution."""
    id: str = Field(default_factory=lambda: str(UUID.uuid4()), description="Unique event ID")
    type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the event occurred")
    phase: Optional[str] = Field(None, description="Current simulation phase")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event-specific details")
    entity_id: Optional[str] = Field(None, description="ID of related entity (document, ticket, etc.)")
    entity_type: Optional[str] = Field(None, description="Type of related entity")


class SimulationProgress(BaseModel):
    """Current progress of a running simulation."""
    simulation_id: str = Field(..., description="Unique simulation identifier")
    status: str = Field(..., description="Current status (running/completed/error)")
    start_time: datetime = Field(..., description="When simulation started")
    current_time: datetime = Field(default_factory=datetime.now, description="Current simulation time")
    completed_phases: List[str] = Field(default_factory=list, description="Completed phases")
    current_phase: Optional[str] = Field(None, description="Currently executing phase")
    progress_percentage: float = Field(0.0, description="Overall progress (0-100)")
    documents_created: int = Field(0, description="Number of documents created")
    tickets_created: int = Field(0, description="Number of JIRA tickets created")
    prs_created: int = Field(0, description="Number of GitHub PRs created")
    workflows_executed: int = Field(0, description="Number of workflows executed")
    errors_encountered: int = Field(0, description="Number of errors encountered")


class DocumentMetadata(BaseModel):
    """Metadata for a generated document."""
    id: str = Field(default_factory=lambda: str(UUID.uuid4()), description="Unique document ID")
    type: DocumentType = Field(..., description="Type of document")
    title: str = Field(..., description="Document title")
    author: str = Field(..., description="Document author")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    phase: str = Field(..., description="Project phase when created")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    content_summary: str = Field(..., description="Brief content summary")
    word_count: int = Field(0, description="Document word count")
    complexity_score: float = Field(0.0, description="Content complexity score")


class TicketMetadata(BaseModel):
    """Metadata for a generated JIRA ticket."""
    id: str = Field(default_factory=lambda: str(UUID.uuid4()), description="Unique ticket ID")
    key: str = Field(..., description="JIRA ticket key (e.g., PROJ-123)")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: str = Field(..., description="Current status")
    assignee: str = Field(..., description="Assigned team member")
    reporter: str = Field(..., description="Ticket reporter")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    priority: str = Field("medium", description="Ticket priority")
    story_points: Optional[int] = Field(None, description="Agile story points")
    comments: List[Dict[str, Any]] = Field(default_factory=list, description="Ticket comments")


class PRMetadata(BaseModel):
    """Metadata for a generated GitHub PR."""
    id: str = Field(default_factory=lambda: str(UUID.uuid4()), description="Unique PR ID")
    number: int = Field(..., description="PR number")
    title: str = Field(..., description="PR title")
    description: str = Field(..., description="PR description")
    author: str = Field(..., description="PR author")
    status: str = Field("open", description="PR status")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    commits: List[Dict[str, Any]] = Field(default_factory=list, description="PR commits")
    reviews: List[Dict[str, Any]] = Field(default_factory=list, description="PR reviews")
    comments: List[Dict[str, Any]] = Field(default_factory=list, description="PR comments")


# API Response Models


class SimulationStatus(BaseModel):
    """Response model for simulation status queries."""
    simulation_id: str
    status: str
    progress: SimulationProgress
    recent_events: List[SimulationEvent] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Response model for completed simulation results."""
    simulation_id: str
    project_config: ProjectConfiguration
    execution_time: float
    total_events: int
    documents_created: List[DocumentMetadata]
    tickets_created: List[TicketMetadata]
    prs_created: List[PRMetadata]
    workflows_executed: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    benefits_demonstrated: List[str]
    inconsistencies_found: List[str]


class ServiceHealth(BaseModel):
    """Health status of ecosystem services."""
    service_name: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time: Optional[float] = None
    last_checked: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None


class EcosystemHealth(BaseModel):
    """Overall health of the ecosystem."""
    overall_status: str
    services: List[ServiceHealth]
    last_updated: datetime = Field(default_factory=datetime.now)


# Template Models


class DocumentTemplate(BaseModel):
    """Template for generating documents."""
    name: str = Field(..., description="Template name")
    type: DocumentType = Field(..., description="Document type")
    content_structure: Dict[str, Any] = Field(..., description="Content structure template")
    variables: List[str] = Field(default_factory=list, description="Required variables")
    ai_prompt_template: str = Field(..., description="AI generation prompt template")


class ProjectTemplate(BaseModel):
    """Complete project template configuration."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    project_type: ProjectType = Field(..., description="Project type")
    team_size: int = Field(..., description="Recommended team size")
    duration_weeks: int = Field(..., description="Recommended duration")
    team_composition: Dict[TeamRole, int] = Field(..., description="Recommended team composition")
    timeline_template: List[TimelinePhase] = Field(..., description="Timeline template")
    document_templates: List[DocumentTemplate] = Field(..., description="Document templates")
    technologies: List[str] = Field(default_factory=list, description="Default technologies")
