"""
Software Development Domain Model
=================================

Provides domain knowledge for software development including ticket types,
complexity factors, technology stacks, and best practices patterns.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TicketType(Enum):
    """Types of development tickets."""
    USER_STORY = "user_story"
    BUG = "bug"
    SPIKE = "spike"
    TASK = "task"
    EPIC = "epic"
    IMPROVEMENT = "improvement"
    REFACTORING = "refactoring"


class Priority(Enum):
    """Priority levels for tickets."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplexityLevel(Enum):
    """Complexity levels for estimation."""
    TRIVIAL = "trivial"  # < 1 hour
    SIMPLE = "simple"  # 1-4 hours
    MODERATE = "moderate"  # 1-2 days
    COMPLEX = "complex"  # 3-5 days
    VERY_COMPLEX = "very_complex"  # 1-2 weeks


class TechnologyCategory(Enum):
    """Technology categories."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    SECURITY = "security"
    AI_ML = "ai_ml"


@dataclass
class TicketTemplate:
    """Template for a ticket type with standard fields and guidance."""
    type: TicketType
    title_pattern: str
    description_template: str
    required_fields: List[str]
    optional_fields: List[str]
    acceptance_criteria_template: List[str]
    typical_complexity: ComplexityLevel
    estimated_hours_range: tuple[int, int]
    common_subtasks: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class ComplexityFactor:
    """Factor that affects task complexity."""
    name: str
    category: str  # technical, domain, team, external
    description: str
    impact: str  # low, medium, high
    mitigation: Optional[str] = None


@dataclass
class TechnologyStack:
    """Definition of a technology stack."""
    name: str
    category: TechnologyCategory
    description: str
    common_tasks: List[str]
    complexity_factors: List[str]
    typical_patterns: List[str]
    learning_curve: str  # low, medium, high
    maturity: str  # experimental, stable, mature


@dataclass
class BestPracticePattern:
    """Best practice pattern for software development."""
    name: str
    category: str  # architecture, testing, deployment, etc.
    description: str
    when_to_use: str
    benefits: List[str]
    considerations: List[str]
    examples: List[str]


class SoftwareDevelopmentDomain:
    """
    Central domain model for software development knowledge.
    
    Provides templates, patterns, and domain expertise for:
    - Ticket decomposition
    - Complexity estimation
    - Technology selection
    - Best practices application
    """
    
    def __init__(self):
        """Initialize with standard templates and patterns."""
        self.ticket_templates = self._initialize_ticket_templates()
        self.complexity_factors = self._initialize_complexity_factors()
        self.technology_stacks = self._initialize_technology_stacks()
        self.best_practices = self._initialize_best_practices()
    
    def _initialize_ticket_templates(self) -> Dict[TicketType, TicketTemplate]:
        """Initialize standard ticket templates."""
        return {
            TicketType.USER_STORY: TicketTemplate(
                type=TicketType.USER_STORY,
                title_pattern="As a [user type], I want to [action] so that [benefit]",
                description_template="""
**User Story**
As a [user type], I want to [action] so that [benefit].

**Acceptance Criteria**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Technical Notes**
[Any technical considerations]

**Dependencies**
[List any dependencies]
                """.strip(),
                required_fields=["user_type", "action", "benefit", "acceptance_criteria"],
                optional_fields=["technical_notes", "dependencies", "mockups"],
                acceptance_criteria_template=[
                    "User can successfully [action]",
                    "System validates [inputs/conditions]",
                    "Error handling for [edge cases]",
                    "UI/UX matches design specifications"
                ],
                typical_complexity=ComplexityLevel.MODERATE,
                estimated_hours_range=(8, 24),
                common_subtasks=[
                    "Design UI/UX",
                    "Implement frontend components",
                    "Create API endpoints",
                    "Add data validation",
                    "Write unit tests",
                    "Write integration tests",
                    "Update documentation"
                ],
                examples=[
                    "As a user, I want to reset my password so that I can regain access to my account",
                    "As an admin, I want to view user analytics so that I can make data-driven decisions"
                ]
            ),
            
            TicketType.BUG: TicketTemplate(
                type=TicketType.BUG,
                title_pattern="[Component] [Brief description of the issue]",
                description_template="""
**Bug Description**
[Clear description of what's not working]

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
[What should happen]

**Actual Behavior**
[What actually happens]

**Environment**
- OS: [Operating System]
- Browser/Version: [If applicable]
- Version: [Application version]

**Additional Context**
[Screenshots, logs, error messages]
                """.strip(),
                required_fields=["description", "steps_to_reproduce", "expected_behavior", "actual_behavior"],
                optional_fields=["environment", "screenshots", "logs", "workaround"],
                acceptance_criteria_template=[
                    "Bug is reproducible and root cause identified",
                    "Fix resolves the issue without breaking existing functionality",
                    "Regression tests added to prevent recurrence",
                    "Documentation updated if behavior changed"
                ],
                typical_complexity=ComplexityLevel.SIMPLE,
                estimated_hours_range=(2, 16),
                common_subtasks=[
                    "Reproduce the bug",
                    "Identify root cause",
                    "Implement fix",
                    "Add regression tests",
                    "Verify fix in all environments",
                    "Update changelog"
                ],
                examples=[
                    "Login page crashes when username contains special characters",
                    "API returns 500 error when filtering by date range"
                ]
            ),
            
            TicketType.SPIKE: TicketTemplate(
                type=TicketType.SPIKE,
                title_pattern="Research: [Topic or question to investigate]",
                description_template="""
**Research Goal**
[What do we need to learn or decide?]

**Questions to Answer**
- Question 1
- Question 2
- Question 3

**Deliverables**
- [ ] Research findings document
- [ ] Recommendation with pros/cons
- [ ] Implementation estimate (if applicable)
- [ ] Prototype/POC (if needed)

**Time Box**
[Maximum time to spend on research]

**Success Criteria**
[How do we know we have enough information?]
                """.strip(),
                required_fields=["research_goal", "questions", "deliverables", "time_box"],
                optional_fields=["alternatives_considered", "resources"],
                acceptance_criteria_template=[
                    "All key questions are answered with sufficient detail",
                    "Recommendation is made with clear justification",
                    "Risks and trade-offs are identified",
                    "Next steps are clearly defined"
                ],
                typical_complexity=ComplexityLevel.MODERATE,
                estimated_hours_range=(4, 40),
                common_subtasks=[
                    "Literature review",
                    "Prototype/POC development",
                    "Performance testing",
                    "Cost analysis",
                    "Document findings",
                    "Present recommendations"
                ],
                examples=[
                    "Research: Best database for time-series data",
                    "Research: Evaluate authentication providers (Auth0 vs Cognito vs Custom)"
                ]
            ),
            
            TicketType.TASK: TicketTemplate(
                type=TicketType.TASK,
                title_pattern="[Action verb] [Object/Component]",
                description_template="""
**Task Description**
[What needs to be done]

**Subtasks**
- [ ] Subtask 1
- [ ] Subtask 2
- [ ] Subtask 3

**Definition of Done**
- [ ] Implementation complete
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

**Dependencies**
[Any blocking items]
                """.strip(),
                required_fields=["description", "definition_of_done"],
                optional_fields=["subtasks", "dependencies", "technical_approach"],
                acceptance_criteria_template=[
                    "Task is completed as described",
                    "Quality standards are met",
                    "Changes are verified",
                    "No regressions introduced"
                ],
                typical_complexity=ComplexityLevel.SIMPLE,
                estimated_hours_range=(2, 16),
                common_subtasks=[
                    "Implement changes",
                    "Write tests",
                    "Update documentation",
                    "Code review",
                    "Deploy to staging"
                ],
                examples=[
                    "Update API documentation for user endpoints",
                    "Configure CI/CD pipeline for frontend deployment",
                    "Add logging to payment processing service"
                ]
            ),
            
            TicketType.REFACTORING: TicketTemplate(
                type=TicketType.REFACTORING,
                title_pattern="Refactor: [Component/Module]",
                description_template="""
**Current State**
[Description of existing code/architecture]

**Problems**
- Problem 1
- Problem 2

**Proposed Changes**
[What will be refactored and how]

**Benefits**
- Benefit 1
- Benefit 2

**Risks**
[Potential risks and mitigation strategies]

**Testing Strategy**
[How to ensure no behavioral changes]
                """.strip(),
                required_fields=["current_state", "problems", "proposed_changes", "testing_strategy"],
                optional_fields=["benefits", "risks", "performance_impact"],
                acceptance_criteria_template=[
                    "Code is more maintainable and readable",
                    "All existing tests still pass",
                    "No behavioral changes introduced",
                    "Performance is maintained or improved",
                    "Technical debt is reduced"
                ],
                typical_complexity=ComplexityLevel.COMPLEX,
                estimated_hours_range=(16, 80),
                common_subtasks=[
                    "Analyze current implementation",
                    "Design new structure",
                    "Refactor in small increments",
                    "Run comprehensive tests",
                    "Update documentation",
                    "Code review"
                ],
                examples=[
                    "Refactor: Extract authentication logic into separate service",
                    "Refactor: Replace global state with context API"
                ]
            )
        }
    
    def _initialize_complexity_factors(self) -> List[ComplexityFactor]:
        """Initialize standard complexity factors."""
        return [
            # Technical Complexity
            ComplexityFactor(
                name="New Technology",
                category="technical",
                description="Using unfamiliar technology or framework",
                impact="high",
                mitigation="Allocate time for learning; consider spike/POC first"
            ),
            ComplexityFactor(
                name="Legacy Code Integration",
                category="technical",
                description="Working with poorly documented or complex legacy code",
                impact="high",
                mitigation="Budget extra time for understanding; refactor incrementally"
            ),
            ComplexityFactor(
                name="Multiple System Integration",
                category="technical",
                description="Coordinating changes across multiple systems",
                impact="medium",
                mitigation="Clear interfaces; comprehensive integration tests"
            ),
            ComplexityFactor(
                name="Performance Requirements",
                category="technical",
                description="Strict performance or scalability constraints",
                impact="medium",
                mitigation="Early performance testing; profiling and optimization"
            ),
            
            # Domain Complexity
            ComplexityFactor(
                name="Complex Business Logic",
                category="domain",
                description="Intricate domain rules and edge cases",
                impact="high",
                mitigation="Domain expert involvement; comprehensive test cases"
            ),
            ComplexityFactor(
                name="Unclear Requirements",
                category="domain",
                description="Ambiguous or incomplete requirements",
                impact="high",
                mitigation="Stakeholder collaboration; iterative clarification"
            ),
            ComplexityFactor(
                name="Regulatory Compliance",
                category="domain",
                description="Must comply with regulations (GDPR, HIPAA, etc.)",
                impact="medium",
                mitigation="Legal/compliance review; audit trails"
            ),
            
            # Team Complexity
            ComplexityFactor(
                name="Team Dependencies",
                category="team",
                description="Requires coordination across multiple teams",
                impact="medium",
                mitigation="Clear communication; defined interfaces; regular sync-ups"
            ),
            ComplexityFactor(
                name="Knowledge Silos",
                category="team",
                description="Only one person knows the area well",
                impact="medium",
                mitigation="Knowledge sharing; pair programming; documentation"
            ),
            
            # External Complexity
            ComplexityFactor(
                name="Third-Party API Dependency",
                category="external",
                description="Depends on external service availability and behavior",
                impact="medium",
                mitigation="Error handling; fallback strategies; API mocking for tests"
            ),
            ComplexityFactor(
                name="Database Migration",
                category="external",
                description="Requires schema changes with data migration",
                impact="high",
                mitigation="Rollback plan; data validation; incremental migration"
            )
        ]
    
    def _initialize_technology_stacks(self) -> Dict[str, TechnologyStack]:
        """Initialize technology stack definitions."""
        return {
            "react": TechnologyStack(
                name="React",
                category=TechnologyCategory.FRONTEND,
                description="JavaScript library for building user interfaces",
                common_tasks=[
                    "Create reusable components",
                    "Manage component state",
                    "Handle side effects",
                    "Implement routing",
                    "Optimize performance"
                ],
                complexity_factors=[
                    "Component lifecycle understanding",
                    "State management patterns",
                    "Performance optimization",
                    "Testing strategies"
                ],
                typical_patterns=[
                    "Container/Presentational components",
                    "Higher-Order Components",
                    "Render Props",
                    "Hooks",
                    "Context API"
                ],
                learning_curve="medium",
                maturity="mature"
            ),
            
            "fastapi": TechnologyStack(
                name="FastAPI",
                category=TechnologyCategory.BACKEND,
                description="Modern Python web framework for building APIs",
                common_tasks=[
                    "Define API endpoints",
                    "Implement request validation",
                    "Add authentication/authorization",
                    "Handle async operations",
                    "Generate API documentation"
                ],
                complexity_factors=[
                    "Async/await understanding",
                    "Pydantic models",
                    "Dependency injection",
                    "Security best practices"
                ],
                typical_patterns=[
                    "Dependency Injection",
                    "Request/Response models",
                    "Background tasks",
                    "Middleware",
                    "Path operations"
                ],
                learning_curve="low",
                maturity="stable"
            ),
            
            "postgresql": TechnologyStack(
                name="PostgreSQL",
                category=TechnologyCategory.DATABASE,
                description="Advanced open-source relational database",
                common_tasks=[
                    "Schema design",
                    "Query optimization",
                    "Index management",
                    "Data migration",
                    "Backup and recovery"
                ],
                complexity_factors=[
                    "SQL proficiency",
                    "Schema normalization",
                    "Query performance tuning",
                    "Transaction management"
                ],
                typical_patterns=[
                    "Normalized schemas",
                    "Materialized views",
                    "Partitioning",
                    "Replication",
                    "Connection pooling"
                ],
                learning_curve="medium",
                maturity="mature"
            ),
            
            "docker": TechnologyStack(
                name="Docker",
                category=TechnologyCategory.INFRASTRUCTURE,
                description="Containerization platform for deploying applications",
                common_tasks=[
                    "Create Dockerfiles",
                    "Build images",
                    "Manage containers",
                    "Configure networking",
                    "Set up volumes"
                ],
                complexity_factors=[
                    "Container concepts",
                    "Image optimization",
                    "Networking configuration",
                    "Security hardening"
                ],
                typical_patterns=[
                    "Multi-stage builds",
                    "Docker Compose",
                    "Health checks",
                    "Volume management",
                    "Environment variables"
                ],
                learning_curve="medium",
                maturity="mature"
            )
        }
    
    def _initialize_best_practices(self) -> List[BestPracticePattern]:
        """Initialize best practice patterns."""
        return [
            BestPracticePattern(
                name="Test-Driven Development (TDD)",
                category="testing",
                description="Write tests before implementing functionality",
                when_to_use="When requirements are clear and stable; for business-critical code",
                benefits=[
                    "Higher test coverage",
                    "Better API design",
                    "Confidence in refactoring",
                    "Living documentation"
                ],
                considerations=[
                    "Requires discipline and practice",
                    "May slow initial development",
                    "Not ideal for exploratory coding"
                ],
                examples=[
                    "Unit tests for business logic",
                    "Integration tests for API endpoints",
                    "End-to-end tests for user workflows"
                ]
            ),
            
            BestPracticePattern(
                name="Continuous Integration/Continuous Deployment (CI/CD)",
                category="deployment",
                description="Automated testing and deployment pipeline",
                when_to_use="Always; essential for modern software development",
                benefits=[
                    "Fast feedback on changes",
                    "Reduced deployment risk",
                    "Consistent builds",
                    "Automated quality gates"
                ],
                considerations=[
                    "Requires initial setup effort",
                    "Needs reliable test suite",
                    "Monitoring is essential"
                ],
                examples=[
                    "GitHub Actions workflow",
                    "Jenkins pipeline",
                    "GitLab CI/CD"
                ]
            ),
            
            BestPracticePattern(
                name="Domain-Driven Design (DDD)",
                category="architecture",
                description="Organize code around business domain concepts",
                when_to_use="Complex business domains; large codebases; long-term projects",
                benefits=[
                    "Better alignment with business",
                    "Clear boundaries and responsibilities",
                    "Easier to reason about code",
                    "Scalable architecture"
                ],
                considerations=[
                    "Requires domain understanding",
                    "More upfront design needed",
                    "May be overkill for simple apps"
                ],
                examples=[
                    "Entities and Value Objects",
                    "Aggregates and Repositories",
                    "Domain Services",
                    "Bounded Contexts"
                ]
            ),
            
            BestPracticePattern(
                name="API-First Design",
                category="architecture",
                description="Design and document API before implementation",
                when_to_use="When building services with multiple consumers; microservices",
                benefits=[
                    "Clear contracts between services",
                    "Parallel development of frontend/backend",
                    "Better API consistency",
                    "Auto-generated documentation"
                ],
                considerations=[
                    "Requires upfront planning",
                    "Changes to API contract are costly",
                    "Versioning strategy needed"
                ],
                examples=[
                    "OpenAPI/Swagger specification",
                    "GraphQL schema",
                    "gRPC proto files"
                ]
            ),
            
            BestPracticePattern(
                name="Code Review",
                category="quality",
                description="Peer review of code changes before merging",
                when_to_use="Always; for all production code changes",
                benefits=[
                    "Knowledge sharing",
                    "Catch bugs early",
                    "Maintain code quality",
                    "Ensure standards compliance"
                ],
                considerations=[
                    "Can slow development if not managed well",
                    "Requires team buy-in",
                    "Need clear review guidelines"
                ],
                examples=[
                    "Pull Request reviews",
                    "Pair programming",
                    "Mob programming"
                ]
            )
        ]
    
    def get_template(self, ticket_type: TicketType) -> Optional[TicketTemplate]:
        """Get template for a specific ticket type."""
        return self.ticket_templates.get(ticket_type)
    
    def get_technology_stack(self, name: str) -> Optional[TechnologyStack]:
        """Get technology stack information."""
        return self.technology_stacks.get(name.lower())
    
    def find_complexity_factors(self, category: Optional[str] = None) -> List[ComplexityFactor]:
        """Find complexity factors, optionally filtered by category."""
        if category:
            return [f for f in self.complexity_factors if f.category == category]
        return self.complexity_factors
    
    def estimate_complexity(
        self,
        description: str,
        technologies: List[str],
        is_new_feature: bool = True
    ) -> Dict[str, Any]:
        """
        Estimate complexity based on description and context.
        
        Args:
            description: Task description
            technologies: Technologies involved
            is_new_feature: Whether this is new development vs maintenance
            
        Returns:
            Dictionary with complexity estimate and factors
        """
        complexity_score = 0
        identified_factors = []
        
        # Analyze description for complexity indicators
        description_lower = description.lower()
        
        # Check for integration complexity
        if any(word in description_lower for word in ['integrate', 'connect', 'sync']):
            complexity_score += 2
            identified_factors.append("Multiple System Integration")
        
        # Check for migration complexity
        if any(word in description_lower for word in ['migrate', 'migration', 'refactor']):
            complexity_score += 3
            identified_factors.append("Database Migration" if 'database' in description_lower else "Legacy Code Integration")
        
        # Check for new technology
        unfamiliar_tech = [tech for tech in technologies if tech.lower() not in ['python', 'javascript', 'react', 'fastapi']]
        if unfamiliar_tech:
            complexity_score += 2
            identified_factors.append("New Technology")
        
        # Check for performance requirements
        if any(word in description_lower for word in ['performance', 'optimize', 'scale', 'fast']):
            complexity_score += 2
            identified_factors.append("Performance Requirements")
        
        # Check for security/compliance
        if any(word in description_lower for word in ['security', 'authentication', 'authorization', 'compliance', 'gdpr']):
            complexity_score += 1
            identified_factors.append("Regulatory Compliance")
        
        # Determine complexity level
        if complexity_score == 0:
            level = ComplexityLevel.TRIVIAL
            hours_estimate = 2
        elif complexity_score <= 2:
            level = ComplexityLevel.SIMPLE
            hours_estimate = 6
        elif complexity_score <= 4:
            level = ComplexityLevel.MODERATE
            hours_estimate = 16
        elif complexity_score <= 6:
            level = ComplexityLevel.COMPLEX
            hours_estimate = 32
        else:
            level = ComplexityLevel.VERY_COMPLEX
            hours_estimate = 60
        
        return {
            "complexity_level": level.value,
            "estimated_hours": hours_estimate,
            "complexity_score": complexity_score,
            "identified_factors": identified_factors,
            "confidence": "medium"
        }

