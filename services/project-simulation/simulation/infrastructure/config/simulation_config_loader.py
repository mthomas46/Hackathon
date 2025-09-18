"""Simulation Configuration File Loader - Load and Validate External Configuration Files.

This module provides functionality to load, validate, and process external configuration
files for simulation parameters, timeline specifications, and team configurations.
Supports YAML and JSON formats with comprehensive validation and error handling.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import yaml
import json
import os
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger


class ConfigFileFormat(str, Enum):
    """Supported configuration file formats."""
    YAML = "yaml"
    YML = "yml"
    JSON = "json"


class SimulationType(str, Enum):
    """Types of simulation scenarios."""
    FULL_PROJECT = "full_project"
    PHASE_FOCUS = "phase_focus"
    TEAM_DYNAMICS = "team_dynamics"
    DOCUMENT_GENERATION = "document_generation"
    WORKFLOW_EXECUTION = "workflow_execution"
    PERFORMANCE_TEST = "performance_test"


class ProjectType(str, Enum):
    """Types of projects that can be simulated."""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    MOBILE_APPLICATION = "mobile_application"
    MICROSERVICES = "microservices"
    DATA_PIPELINE = "data_pipeline"
    MACHINE_LEARNING = "machine_learning"


class ComplexityLevel(str, Enum):
    """Project complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


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
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    EXPERT = "expert"
    LEAD = "lead"


class TimelinePhaseConfig(BaseModel):
    """Configuration for a timeline phase."""
    name: str = Field(..., description="Phase name")
    description: str = Field("", description="Phase description")
    duration_days: int = Field(..., ge=1, le=365, description="Phase duration in days")
    start_date: Optional[str] = Field(None, description="Phase start date (ISO format)")
    dependencies: List[str] = Field(default_factory=list, description="Phase dependencies")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")
    team_allocation: Dict[str, float] = Field(default_factory=dict, description="Team allocation by role")


class TeamMemberConfig(BaseModel):
    """Configuration for a team member."""
    name: str = Field(..., description="Team member name")
    role: TeamRole = Field(..., description="Team member role")
    expertise_level: ExpertiseLevel = Field(ExpertiseLevel.MID_LEVEL, description="Expertise level")
    productivity_multiplier: float = Field(1.0, ge=0.1, le=3.0, description="Productivity multiplier")
    skills: List[str] = Field(default_factory=list, description="Technical skills")
    cost_per_hour: Optional[float] = Field(None, ge=0, description="Cost per hour")
    availability_percentage: float = Field(100.0, ge=0, le=100, description="Availability percentage")


class SimulationConfigFile(BaseModel):
    """Complete simulation configuration from file."""
    # Basic project information
    project_name: str = Field(..., description="Project name")
    project_description: str = Field("", description="Project description")
    project_type: ProjectType = Field(ProjectType.WEB_APPLICATION, description="Project type")
    complexity_level: ComplexityLevel = Field(ComplexityLevel.MEDIUM, description="Complexity level")

    # Simulation parameters
    simulation_type: SimulationType = Field(SimulationType.FULL_PROJECT, description="Simulation type")
    duration_weeks: int = Field(8, ge=1, le=52, description="Project duration in weeks")
    budget: Optional[float] = Field(None, ge=0, description="Project budget")

    # Timeline configuration
    timeline_phases: List[TimelinePhaseConfig] = Field(default_factory=list, description="Project phases")

    # Team configuration
    team_members: List[TeamMemberConfig] = Field(default_factory=list, description="Team members")
    max_team_size: int = Field(10, ge=1, le=50, description="Maximum team size")

    # Content generation settings
    include_document_generation: bool = Field(True, description="Generate documents")
    include_workflow_execution: bool = Field(True, description="Execute workflows")
    include_team_dynamics: bool = Field(True, description="Simulate team dynamics")

    # Analysis settings
    enable_analysis: bool = Field(True, description="Enable analysis")
    analysis_types: List[str] = Field(
        default_factory=lambda: ["quality", "consistency", "patterns"],
        description="Analysis types to run"
    )

    # Real-time settings
    real_time_progress: bool = Field(False, description="Enable real-time progress updates")
    websocket_enabled: bool = Field(True, description="Enable WebSocket updates")

    # Performance settings
    max_execution_time_minutes: int = Field(60, ge=1, le=480, description="Maximum execution time")
    generate_realistic_delays: bool = Field(True, description="Generate realistic delays")
    capture_metrics: bool = Field(True, description="Capture performance metrics")

    # Ecosystem integration
    enable_ecosystem_integration: bool = Field(True, description="Enable ecosystem integration")
    custom_service_endpoints: Dict[str, str] = Field(default_factory=dict, description="Custom service endpoints")

    @validator('timeline_phases')
    def validate_timeline_phases(cls, v):
        """Validate timeline phases configuration."""
        if not v:
            # Create default phases if none provided
            return [
                TimelinePhaseConfig(
                    name="Planning",
                    description="Project planning and requirements gathering",
                    duration_days=15,
                    deliverables=["Requirements Document", "Project Plan"]
                ),
                TimelinePhaseConfig(
                    name="Design",
                    description="System design and architecture",
                    duration_days=30,
                    deliverables=["System Architecture", "UI/UX Designs"]
                ),
                TimelinePhaseConfig(
                    name="Development",
                    description="Core development and implementation",
                    duration_days=60,
                    deliverables=["Working Software", "Code Repository"]
                ),
                TimelinePhaseConfig(
                    name="Testing",
                    description="Quality assurance and testing",
                    duration_days=20,
                    deliverables=["Test Reports", "Quality Metrics"]
                ),
                TimelinePhaseConfig(
                    name="Deployment",
                    description="Production deployment and release",
                    duration_days=10,
                    deliverables=["Production Release", "Documentation"]
                )
            ]
        return v

    @validator('team_members')
    def validate_team_members(cls, v):
        """Validate team members configuration."""
        if not v:
            # Create default team if none provided
            return [
                TeamMemberConfig(
                    name="Alice Johnson",
                    role=TeamRole.PRODUCT_MANAGER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Product Strategy", "Requirements", "Agile"],
                    productivity_multiplier=0.9
                ),
                TeamMemberConfig(
                    name="Bob Smith",
                    role=TeamRole.TECHNICAL_LEAD,
                    expertise_level=ExpertiseLevel.EXPERT,
                    skills=["Architecture", "Python", "Leadership"],
                    productivity_multiplier=1.2
                ),
                TeamMemberConfig(
                    name="Carol Williams",
                    role=TeamRole.SENIOR_DEVELOPER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Python", "FastAPI", "React", "PostgreSQL"],
                    productivity_multiplier=1.1
                ),
                TeamMemberConfig(
                    name="David Brown",
                    role=TeamRole.QA_ENGINEER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Testing", "Automation", "Quality Assurance"],
                    productivity_multiplier=1.0
                )
            ]
        return v


class SimulationConfigLoader:
    """Loads and validates simulation configuration files."""

    def __init__(self):
        """Initialize the configuration loader."""
        self.logger = get_simulation_logger()
        self._config_cache: Dict[str, SimulationConfigFile] = {}

    def load_config_file(self, file_path: Union[str, Path]) -> SimulationConfigFile:
        """Load and validate a simulation configuration file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Check cache first
        cache_key = str(file_path.absolute())
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        try:
            # Determine file format
            file_format = self._detect_file_format(file_path)

            # Load file content
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_format in [ConfigFileFormat.YAML, ConfigFileFormat.YML]:
                    raw_config = yaml.safe_load(f)
                elif file_format == ConfigFileFormat.JSON:
                    raw_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")

            # Validate and create configuration object
            config = SimulationConfigFile(**raw_config)

            # Cache the configuration
            self._config_cache[cache_key] = config

            self.logger.info(
                "Configuration file loaded successfully",
                file_path=str(file_path),
                project_name=config.project_name,
                simulation_type=config.simulation_type.value
            )

            return config

        except ValidationError as e:
            self.logger.error(
                "Configuration validation failed",
                file_path=str(file_path),
                errors=[{"field": err['loc'], "message": err['msg']} for err in e.errors()]
            )
            raise ValueError(f"Invalid configuration file: {e}") from e

        except Exception as e:
            self.logger.error(
                "Failed to load configuration file",
                file_path=str(file_path),
                error=str(e)
            )
            raise

    def create_config_from_dict(self, config_dict: Dict[str, Any]) -> SimulationConfigFile:
        """Create a configuration object from a dictionary."""
        try:
            config = SimulationConfigFile(**config_dict)
            self.logger.info(
                "Configuration created from dictionary",
                project_name=config.project_name
            )
            return config
        except ValidationError as e:
            self.logger.error(
                "Configuration validation failed",
                errors=[{"field": err['loc'], "message": err['msg']} for err in e.errors()]
            )
            raise ValueError(f"Invalid configuration: {e}") from e

    def save_config_file(self, config: SimulationConfigFile, file_path: Union[str, Path],
                        file_format: ConfigFileFormat = ConfigFileFormat.YAML) -> None:
        """Save a configuration object to a file."""
        file_path = Path(file_path)

        try:
            # Convert to dictionary
            config_dict = config.dict()

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_format in [ConfigFileFormat.YAML, ConfigFileFormat.YML]:
                    yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
                elif file_format == ConfigFileFormat.JSON:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")

            self.logger.info(
                "Configuration file saved successfully",
                file_path=str(file_path),
                project_name=config.project_name
            )

        except Exception as e:
            self.logger.error(
                "Failed to save configuration file",
                file_path=str(file_path),
                error=str(e)
            )
            raise

    def create_sample_config_file(self, file_path: Union[str, Path],
                                project_name: str = "Sample E-commerce Platform") -> SimulationConfigFile:
        """Create a sample configuration file with realistic defaults."""
        sample_config = SimulationConfigFile(
            project_name=project_name,
            project_description="A comprehensive e-commerce platform with microservices architecture",
            project_type=ProjectType.WEB_APPLICATION,
            complexity_level=ComplexityLevel.COMPLEX,
            simulation_type=SimulationType.FULL_PROJECT,
            duration_weeks=12,
            budget=250000.0,
            timeline_phases=[
                TimelinePhaseConfig(
                    name="Discovery & Planning",
                    description="Requirements gathering and project planning",
                    duration_days=20,
                    deliverables=["Business Requirements", "Technical Specifications", "Project Roadmap"],
                    team_allocation={"product_manager": 0.8, "business_analyst": 0.6}
                ),
                TimelinePhaseConfig(
                    name="Architecture Design",
                    description="System architecture and technical design",
                    duration_days=25,
                    deliverables=["System Architecture Diagram", "API Specifications", "Database Design"],
                    dependencies=["Discovery & Planning"],
                    team_allocation={"technical_lead": 1.0, "senior_developer": 0.7}
                ),
                TimelinePhaseConfig(
                    name="Core Development",
                    description="Implementation of core features and services",
                    duration_days=45,
                    deliverables=["User Service", "Product Service", "Order Service", "Payment Integration"],
                    dependencies=["Architecture Design"],
                    team_allocation={"senior_developer": 1.0, "developer": 0.8, "qa_engineer": 0.6}
                ),
                TimelinePhaseConfig(
                    name="Frontend Development",
                    description="User interface and frontend implementation",
                    duration_days=30,
                    deliverables=["React Frontend", "Admin Dashboard", "Mobile Responsive Design"],
                    dependencies=["Architecture Design"],
                    team_allocation={"senior_developer": 0.8, "developer": 1.0, "designer": 0.5}
                ),
                TimelinePhaseConfig(
                    name="Testing & QA",
                    description="Comprehensive testing and quality assurance",
                    duration_days=20,
                    deliverables=["Unit Tests", "Integration Tests", "E2E Tests", "Performance Tests"],
                    dependencies=["Core Development", "Frontend Development"],
                    team_allocation={"qa_engineer": 1.0, "senior_developer": 0.3}
                ),
                TimelinePhaseConfig(
                    name="Deployment & Launch",
                    description="Production deployment and go-live",
                    duration_days=10,
                    deliverables=["Production Deployment", "Monitoring Setup", "Documentation"],
                    dependencies=["Testing & QA"],
                    team_allocation={"devops_engineer": 1.0, "technical_lead": 0.5}
                )
            ],
            team_members=[
                TeamMemberConfig(
                    name="Sarah Chen",
                    role=TeamRole.PRODUCT_MANAGER,
                    expertise_level=ExpertiseLevel.EXPERT,
                    skills=["Product Strategy", "Agile", "E-commerce", "Stakeholder Management"],
                    productivity_multiplier=0.9,
                    cost_per_hour=75.0
                ),
                TeamMemberConfig(
                    name="Mike Rodriguez",
                    role=TeamRole.TECHNICAL_LEAD,
                    expertise_level=ExpertiseLevel.EXPERT,
                    skills=["System Architecture", "Python", "Microservices", "AWS"],
                    productivity_multiplier=1.2,
                    cost_per_hour=85.0
                ),
                TeamMemberConfig(
                    name="Emily Johnson",
                    role=TeamRole.SENIOR_DEVELOPER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
                    productivity_multiplier=1.1,
                    cost_per_hour=65.0
                ),
                TeamMemberConfig(
                    name="David Kim",
                    role=TeamRole.SENIOR_DEVELOPER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["React", "TypeScript", "Node.js", "GraphQL"],
                    productivity_multiplier=1.1,
                    cost_per_hour=65.0
                ),
                TeamMemberConfig(
                    name="Lisa Wong",
                    role=TeamRole.QA_ENGINEER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Test Automation", "Selenium", "pytest", "Performance Testing"],
                    productivity_multiplier=1.0,
                    cost_per_hour=55.0
                ),
                TeamMemberConfig(
                    name="Tom Anderson",
                    role=TeamRole.DEVOPS_ENGINEER,
                    expertise_level=ExpertiseLevel.SENIOR,
                    skills=["Docker", "Kubernetes", "CI/CD", "AWS", "Terraform"],
                    productivity_multiplier=1.0,
                    cost_per_hour=70.0
                )
            ],
            max_team_size=8,
            include_document_generation=True,
            include_workflow_execution=True,
            include_team_dynamics=True,
            enable_analysis=True,
            analysis_types=["quality", "consistency", "patterns", "performance"],
            real_time_progress=True,
            websocket_enabled=True,
            max_execution_time_minutes=120,
            generate_realistic_delays=True,
            capture_metrics=True,
            enable_ecosystem_integration=True
        )

        # Save the sample configuration
        self.save_config_file(sample_config, file_path)

        self.logger.info(
            "Sample configuration file created",
            file_path=str(file_path),
            project_name=sample_config.project_name
        )

        return sample_config

    def _detect_file_format(self, file_path: Path) -> ConfigFileFormat:
        """Detect the file format from the file extension."""
        suffix = file_path.suffix.lower()
        if suffix in ['.yaml', '.yml']:
            return ConfigFileFormat.YAML
        elif suffix == '.json':
            return ConfigFileFormat.JSON
        else:
            # Try to detect from content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_char = f.read(1)
                    if first_char == '{':
                        return ConfigFileFormat.JSON
                    else:
                        return ConfigFileFormat.YAML
            except Exception:
                raise ValueError(f"Cannot determine file format for: {file_path}")

    def validate_config(self, config: SimulationConfigFile) -> List[str]:
        """Validate a configuration object and return any issues."""
        issues = []

        # Check timeline consistency
        total_days = sum(phase.duration_days for phase in config.timeline_phases)
        expected_days = config.duration_weeks * 7

        if abs(total_days - expected_days) > 7:  # Allow 1 week variance
            issues.append(
                f"Timeline duration mismatch: {total_days} days vs expected {expected_days} days "
                f"from {config.duration_weeks} weeks"
            )

        # Check team size
        if len(config.team_members) > config.max_team_size:
            issues.append(
                f"Team size exceeds maximum: {len(config.team_members)} > {config.max_team_size}"
            )

        # Check for required roles
        required_roles = [TeamRole.PRODUCT_MANAGER, TeamRole.TECHNICAL_LEAD]
        existing_roles = {member.role for member in config.team_members}

        missing_roles = set(required_roles) - existing_roles
        if missing_roles:
            issues.append(f"Missing required team roles: {[role.value for role in missing_roles]}")

        return issues

    def get_config_template(self) -> Dict[str, Any]:
        """Get a configuration template for documentation."""
        return SimulationConfigFile().dict()


# Global configuration loader instance
_config_loader: Optional[SimulationConfigLoader] = None


def get_simulation_config_loader() -> SimulationConfigLoader:
    """Get the global simulation configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = SimulationConfigLoader()
    return _config_loader


def load_simulation_config(file_path: Union[str, Path]) -> SimulationConfigFile:
    """Convenience function to load a simulation configuration file."""
    return get_simulation_config_loader().load_config_file(file_path)


def create_sample_simulation_config(file_path: Union[str, Path],
                                  project_name: str = "Sample Project") -> SimulationConfigFile:
    """Convenience function to create a sample configuration file."""
    return get_simulation_config_loader().create_sample_config_file(file_path, project_name)


__all__ = [
    'SimulationConfigLoader',
    'SimulationConfigFile',
    'TimelinePhaseConfig',
    'TeamMemberConfig',
    'SimulationType',
    'ProjectType',
    'ComplexityLevel',
    'TeamRole',
    'ExpertiseLevel',
    'ConfigFileFormat',
    'get_simulation_config_loader',
    'load_simulation_config',
    'create_sample_simulation_config'
]
