"""Entity Type Value Object."""

from enum import Enum


class EntityType(str, Enum):
    """
    Types of entities that can be extracted from queries.
    
    These represent the domain objects that queries reference.
    """
    
    # People & Teams
    PERSON = "person"              # Individual person/developer
    TEAM = "team"                  # Team or group
    ROLE = "role"                  # Job role or position
    
    # Organization
    CLIENT = "client"              # Client or customer
    COMPANY = "company"            # Company or organization
    DEPARTMENT = "department"      # Department or division
    
    # Projects & Work
    PROJECT = "project"            # Software project
    FEATURE = "feature"            # Product feature
    TASK = "task"                  # Work task or ticket
    SPRINT = "sprint"              # Agile sprint
    EPIC = "epic"                  # Large feature group
    
    # Technical
    TECHNOLOGY = "technology"      # Programming language, framework, tool
    REPOSITORY = "repository"      # Code repository
    SERVICE = "service"            # Microservice or component
    API = "api"                    # API endpoint or service
    DATABASE = "database"          # Database or data store
    
    # Code
    CODE_PATTERN = "code_pattern"  # Coding pattern or practice
    ARCHITECTURE = "architecture"  # System architecture
    DEPENDENCY = "dependency"      # Software dependency
    
    # Documentation
    DOCUMENT = "document"          # Documentation file
    SPECIFICATION = "specification" # Technical spec
    
    # Time
    TIME_PERIOD = "time_period"    # Time range (sprint, quarter, etc.)
    DATE = "date"                  # Specific date
    
    # Metrics & KPIs
    METRIC = "metric"              # Performance metric
    KPI = "kpi"                    # Key performance indicator
    
    # Other
    UNKNOWN = "unknown"            # Unrecognized entity type
    
    @property
    def is_organizational(self) -> bool:
        """Check if entity is organizational."""
        return self in {
            EntityType.CLIENT,
            EntityType.COMPANY,
            EntityType.DEPARTMENT,
            EntityType.TEAM,
        }
    
    @property
    def is_technical(self) -> bool:
        """Check if entity is technical."""
        return self in {
            EntityType.TECHNOLOGY,
            EntityType.REPOSITORY,
            EntityType.SERVICE,
            EntityType.API,
            EntityType.DATABASE,
            EntityType.CODE_PATTERN,
            EntityType.ARCHITECTURE,
            EntityType.DEPENDENCY,
        }
    
    @property
    def is_temporal(self) -> bool:
        """Check if entity is time-related."""
        return self in {
            EntityType.TIME_PERIOD,
            EntityType.DATE,
            EntityType.SPRINT,
        }

