"""
External Service Entities - Phase 9
Data models for external service discovery, validation, and accuracy enhancement.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DiscoveryMethod(Enum):
    """Method used to discover an external service."""
    EXPLICIT_MENTION = "explicit_mention"
    TOPIC_MATCH = "topic_match"
    TECHNOLOGY_MATCH = "technology_match"
    RELATED_SERVICE = "related_service"
    TEAM_EXPERIENCE = "team_experience"
    HISTORICAL_USAGE = "historical_usage"


class ServiceCategory(Enum):
    """Category of external service integration."""
    DIRECT = "direct"  # Part of the plan, high relevance
    TANGENTIAL = "tangential"  # Future work, medium relevance
    EXCLUDED = "excluded"  # Low relevance, not included


class IssueSeverity(Enum):
    """Severity level for issues found."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExternalServiceMatch:
    """An external service discovered during analysis."""
    service_id: str
    name: str
    relevance_score: float  # 0.0-1.0
    discovery_methods: List[DiscoveryMethod]
    initial_category: ServiceCategory
    mentioned_context: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceCatalogEntry:
    """Cataloged external service with full relationship data."""
    service_match: ExternalServiceMatch
    skills_coverage: Dict[str, Any]  # Team skills that match
    historical_tickets: List[Dict[str, Any]]  # Related Jira tickets
    documentation_links: List[Dict[str, Any]]  # Related docs
    team_members: List[str]  # Team members with relevant skills
    coverage_score: float  # 0.0-1.0, how well team covers requirements
    documentation_quality: str  # "Excellent", "Good", "Fair", "Poor", "None"
    cataloged_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ValidationIssue:
    """An issue found during integration validation."""
    severity: IssueSeverity
    category: str  # "api_contract", "security", "rate_limits", etc.
    issue: str
    impact: str
    detection_method: str
    remediation: str
    story_points_to_add: int
    timeline_impact_days: float
    sprint: str
    assignee: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceValidationResult:
    """Results of compliance validation for a service."""
    service_id: str
    service_name: str  # Human-readable service name
    api_compliant: bool
    security_compliant: bool
    version_compatible: bool
    rate_limits_sufficient: bool
    issues: List[ValidationIssue]
    total_story_points_to_add: int
    total_timeline_impact_days: float
    validation_confidence: float  # 0.0-1.0
    validated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeGap:
    """A knowledge gap identified during analysis."""
    gap_type: str  # "documentation", "skills", "configuration"
    severity: IssueSeverity
    description: str
    impact: str
    remediation_actions: List[Dict[str, Any]]
    story_points_to_add: int
    timeline_impact_days: float
    assignee: Optional[str] = None


@dataclass
class KnowledgeGapAnalysis:
    """Complete knowledge gap analysis for a service."""
    service_id: str
    service_name: str  # Human-readable service name
    documentation_gaps: List[KnowledgeGap]
    skills_gaps: List[KnowledgeGap]
    configuration_gaps: List[KnowledgeGap]
    total_story_points_to_add: int
    total_timeline_impact_days: float
    enrichment_actions: List[Dict[str, Any]]


@dataclass
class DevelopmentBlindspot:
    """A development blindspot that could derail the project."""
    blindspot_type: str  # "hidden_dependency", "rate_limit_cascade", "scale_issue", etc.
    severity: IssueSeverity
    description: str
    why_missed: str
    impact: str
    detection_method: str
    story_points_to_add: int
    timeline_impact_days: float
    mitigation: str
    sprint: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlindspotAnalysis:
    """Complete blindspot analysis results."""
    service_id: str
    service_name: str  # Human-readable service name
    blindspots: List[DevelopmentBlindspot]
    severity_distribution: Dict[str, int]  # Count by severity
    total_story_points_missed: int
    total_timeline_impact_days: float
    detection_confidence: float  # 0.0-1.0, how confident we are we caught everything


@dataclass
class AccuracyEnhancementResult:
    """Final accuracy enhancement results."""
    original_story_points: int
    adjusted_story_points: int
    story_points_added: int
    story_points_change_percent: float
    
    original_weeks: float
    adjusted_weeks: float
    weeks_added: float
    timeline_change_percent: float
    
    original_confidence: int  # Percentage
    adjusted_confidence: int  # Percentage
    confidence_improvement: int  # Percentage points
    
    original_risk_level: str
    adjusted_risk_level: str
    risk_reduction_percent: float
    
    validation_findings: ComplianceValidationResult
    gap_findings: KnowledgeGapAnalysis
    blindspot_findings: BlindspotAnalysis
    
    services_discovered: int
    high_relevance_services: int
    issues_found_total: int
    blindspots_detected: int


@dataclass
class WorkflowEResult:
    """Complete Workflow E execution result."""
    discovered_services: List[ExternalServiceMatch]
    cataloged_services: List[ServiceCatalogEntry]
    validation_results: List[ComplianceValidationResult]
    gap_analyses: List[KnowledgeGapAnalysis]
    blindspot_analyses: List[BlindspotAnalysis]
    accuracy_enhancement: AccuracyEnhancementResult
    execution_time_seconds: float
    workflow_id: str = field(default_factory=lambda: f"workflow_e_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    executed_at: datetime = field(default_factory=datetime.utcnow)

