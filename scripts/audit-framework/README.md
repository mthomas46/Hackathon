# LLM Documentation Ecosystem Audit Framework

A comprehensive, modular audit framework for evaluating the quality, architecture, and maintainability of Python services in the LLM Documentation Ecosystem.

## 🎯 Overview

The Audit Framework provides automated analysis of Python services across four key dimensions:

- **🏗️ Architecture** (30%) - DDD compliance, REST API design, layer separation
- **💻 Code Quality** (25%) - Complexity, testing, linting, duplication
- **⚡ Performance** (20%) - Resource usage, response times, system metrics
- **🔧 Maintainability** (25%) - Documentation, organization, dead code detection

## 📊 Grading System

### Final Grade Scale
- **A (90-100)**: Excellent - Production-ready with best practices
- **B (80-89)**: Good - Well-structured with minor improvements needed
- **C (70-79)**: Satisfactory - Functional but requires attention
- **D (50-69)**: Poor - Significant issues requiring fixes
- **F (0-49)**: Critical - Major architectural/design problems

### Weighted Scoring
```python
overall_score = (
    architecture_score * 0.30 +
    code_quality_score * 0.25 +
    performance_score * 0.20 +
    maintainability_score * 0.25
)
```

## 🏗️ Architecture Dimension (30% Weight)

### DDD+REST Compliance (40% of Architecture)
Evaluates Domain-Driven Design implementation and REST API architecture.

#### Directory Structure Standards
```
service/
├── domain/                    # Business logic layer
│   ├── entities/             # Core business entities
│   ├── services/             # Domain services
│   ├── repositories/         # Data access contracts
│   ├── value_objects/        # Value objects
│   └── exceptions/           # Domain exceptions
├── application/              # Use case orchestration
│   ├── handlers/            # Command/query handlers
│   ├── dto/                 # Data transfer objects
│   └── validators/          # Business rule validators
├── infrastructure/           # External concerns
│   ├── repositories/        # Data access implementations
│   ├── external_services/   # API clients, integrations
│   └── config/              # Configuration management
└── presentation/             # HTTP/API layer
    ├── controllers/         # Request/response handling
    ├── routes/              # Route definitions (by domain)
    │   ├── analysis.py      # Analysis endpoints
    │   ├── documents.py     # Document endpoints
    │   ├── workflows.py     # Workflow endpoints
    │   ├── reports.py       # Report endpoints
    │   └── health.py        # Health endpoints
    └── models/              # API models/schemas
```

#### Routes Directory Requirements
- **Required**: `presentation/routes/` with `__init__.py`
- **Recommended**: Domain-organized route files
- **Penalty**: Missing routes structure (-4 points max)
- **File Size Limit**: 300 lines per route file

### REST API Compliance (35% of Architecture)
Evaluates HTTP API design and OpenAPI documentation quality.

#### OpenAPI Documentation Requirements
- **Required**: `summary`, `description`, `response_model`
- **Recommended**: `responses`, `tags`, `deprecated`
- **Scoring**: 25 points per missing required annotation
- **Bonus**: Multi-line descriptions, detailed response examples

#### REST Standards Enforcement
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Standard status codes (200, 201, 400, 404, 500)
- Consistent resource naming
- Error response formatting

### Layer Separation (25% of Architecture)
Evaluates clean architecture principles and separation of concerns.

#### Forbidden Cross-Layer Dependencies
- **Domain**: Cannot import from presentation/infrastructure
- **Application**: Cannot import from infrastructure
- **Presentation**: Cannot contain business logic
- **Infrastructure**: Cannot contain domain logic

## 💻 Code Quality Dimension (25% Weight)

### Complexity Analysis (25% of Code Quality)
Evaluates code maintainability and cognitive complexity.

#### Cyclomatic Complexity Limits
- **Functions**: Max 10 (recommended: 8 for strict profiles)
- **Classes**: Max 50
- **Penalty**: 5 points for functions >10 complexity
- **Bonus**: -2 points for average complexity ≤8

### Testing Quality (30% of Code Quality)
Evaluates test coverage and test suite quality.

#### Coverage Requirements
- **Standard**: 70% minimum coverage
- **Strict**: 85% minimum coverage
- **Relaxed**: 50% minimum coverage
- **CI-Fast**: 40% minimum coverage

#### Test Quality Metrics
- Test naming conventions (`test_<behavior>_<condition>_<expected>`)
- Test isolation and mocking
- Parameterized tests usage
- Test file organization

### Linting & Code Style (20% of Code Quality)
Evaluates adherence to Python coding standards.

#### Tool Integration
- **Flake8**: Style guide enforcement
- **Pylint**: Code quality analysis
- **Black**: Code formatting compliance
- **isort**: Import organization

#### Scoring
- **Excellent**: 90+ pylint score
- **Good**: 80-89 pylint score
- **Poor**: <70 pylint score
- **Penalty**: 2 points per 10-point decrement

### Code Duplication (15% of Code Quality)
Detects and penalizes duplicate code blocks.

#### Detection Criteria
- **Threshold**: 10% duplication tolerance
- **Penalty**: 2 points per 5% over threshold
- **Tools**: Integrated AST-based duplicate detection

## ⚡ Performance Dimension (20% Weight)

### Resource Monitoring (40% of Performance)
Evaluates system resource usage during audit execution.

#### Thresholds
- **Memory**: <500MB usage
- **CPU**: <80% utilization
- **Response Time**: <1000ms per operation
- **Disk I/O**: Monitored for excessive usage

### System Metrics Collection (30% of Performance)
Real-time performance analysis during audit execution.

#### Metrics Tracked
- Memory consumption patterns
- CPU usage over time
- Network I/O statistics
- Disk access patterns
- Process resource allocation

### Database Performance (20% of Performance)
Evaluates data access layer efficiency.

#### Analysis Areas
- Query optimization potential
- Connection pooling effectiveness
- Caching strategy effectiveness
- Migration script efficiency

## 🔧 Maintainability Dimension (25% Weight)

### Documentation Quality (35% of Maintainability)
Evaluates code and API documentation completeness.

#### Docstring Coverage
- **Functions**: 90% coverage (strict), 80% (standard)
- **Classes**: 100% coverage required
- **Modules**: Recommended documentation

#### API Documentation
- OpenAPI/Swagger compliance (see Architecture section)
- Response examples completeness
- Parameter documentation quality

### Code Organization (25% of Maintainability)
Evaluates project structure and file organization.

#### File Size Limits
- **Maximum**: 1000 lines per file
- **Recommended**: 500 lines per file
- **Penalty**: 0.5 points per file over limit

#### Directory Structure
- Maximum 15 files per directory
- Logical grouping by feature/domain
- Clear separation of concerns

### Dead Code Detection (20% of Maintainability)
Identifies unreachable or unused code.

#### Detection Methods
- **AST Analysis**: Unreachable code blocks
- **Import Analysis**: Unused imports
- **Function Analysis**: Unused private methods
- **Coverage Analysis**: Untested code paths

#### Tolerance Levels
- **Standard**: 5% dead code tolerance
- **Penalty**: 2 points per 10% over tolerance

### Dependency Coupling (10% of Maintainability)
Evaluates inter-module dependencies and coupling.

#### Metrics
- **Import Count**: Max 20 imports per file
- **Circular Dependencies**: Detected and penalized
- **Tight Coupling**: High coupling scores penalized

## ⚙️ Configuration Profiles

### Built-in Profiles

#### `strict` - Maximum Quality Enforcement
```python
- Critical issues threshold: 1
- Complexity max: 8
- Test coverage: 85%
- Docstring coverage: 90%
- File size limit: 800 lines
```

#### `standard` - Balanced Analysis
```python
- Critical issues threshold: 2
- Complexity max: 10
- Test coverage: 70%
- Docstring coverage: 80%
- File size limit: 1000 lines
```

#### `relaxed` - Development-Friendly
```python
- Critical issues threshold: 3
- Complexity max: 15
- Test coverage: 50%
- Docstring coverage: 60%
- File size limit: 1500 lines
```

#### `ci_fast` - Quick CI Checks
```python
- Analysis depth: Minimal
- System metrics: Disabled
- Third-party tools: Disabled
- Focus: Critical issues only
- Timeout: 60 seconds
```

#### `ci_comprehensive` - Full CI Analysis
```python
- Full analysis enabled
- JSON output format
- Fail on critical issues
- Comprehensive reporting
```

### Custom Profile Creation
```python
from audit_framework.config import profile_manager

# Create custom profile
custom_profile = profile_manager.create_custom_profile(
    'standard',
    {
        'code_quality': {'complexity_threshold': 12},
        'maintainability': {'docstring_coverage_required': 85}
    }
)
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic audit with default profile
audit-framework audit --service my-service

# Use specific profile
audit-framework audit --service my-service --profile strict

# JSON output for CI/CD
audit-framework audit --service my-service --output json

# Verbose output
audit-framework audit --service my-service --verbose
```

### Programmatic Usage

```python
from audit_framework import AuditFramework
from audit_framework.config import profile_manager

# Initialize with custom profile
profile = profile_manager.get_profile('strict')
auditor = AuditFramework(profile=profile)

# Run audit
results = await auditor.audit_service('my-service')

# Access detailed results
print(f"Overall Score: {results.overall_score}")
print(f"Architecture: {results.architecture.score}")
print(f"Critical Issues: {len(results.critical_issues)}")
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Code Quality Audit
  run: |
    audit-framework audit --service . --profile ci_comprehensive --output json > audit-results.json

- name: Check Audit Results
  run: |
    score=$(jq '.overall_score' audit-results.json)
    if (( $(echo "$score < 70" | bc -l) )); then
      echo "Audit failed: Score $score < 70"
      exit 1
    fi
```

## 📋 Critical Issues & Failure Conditions

### Automatic Failure Triggers
- **Critical Issues > Threshold**: Profile-dependent (1-3 issues)
- **Overall Score < 50**: Fundamental architectural problems
- **Security Vulnerabilities**: Zero tolerance for high-severity issues
- **Data Loss Risks**: Any potential data integrity issues

### Issue Severity Levels
- **Critical**: Blocks deployment, requires immediate attention
- **High**: Should be addressed in next sprint
- **Medium**: Address when time permits
- **Low**: Nice-to-have improvements

## 🔧 Extending the Framework

### Adding New Analyzers

```python
from audit_framework.analyzers.base import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    async def analyze(self, service: ServiceInfo) -> AnalysisResult:
        # Your analysis logic here
        return AnalysisResult(score=85.0, issues=[], recommendations=[])
```

### Adding New Metrics

```python
# Add to thresholds configuration
'custom_metric': {
    'min_value': 70,
    'max_value': 100,
    'weight': 0.1
}
```

### Custom Profile Creation

```python
custom_profile = AuditProfile(
    name="enterprise",
    intensity=AuditIntensity.STRICT,
    dimension_weights={
        'architecture': 35,
        'code_quality': 30,
        'performance': 15,
        'maintainability': 20
    },
    # Custom settings...
)
```

## 📊 Reporting & Output Formats

### Rich Console Output
Interactive terminal display with colors, tables, and progress indicators.

### JSON Output
Structured data for CI/CD integration and automated processing.

### Markdown Output
Human-readable reports for documentation and sharing.

## 🔬 Advanced Features

### Third-Party Tool Integration
- **Bandit**: Security vulnerability scanning
- **Radon**: Complexity analysis
- **Interrogate**: Docstring coverage
- **Coverage.py**: Test coverage measurement

### System Resource Monitoring
Real-time tracking of CPU, memory, and I/O during analysis.

### Intelligent Recommendations
Context-aware suggestions based on detected issues and codebase patterns.

### Historical Trend Analysis
Track improvement over time with comparative reporting.

---

## 🎯 Quality Gates & CI/CD Integration

The framework provides configurable quality gates for different deployment stages:

- **Development**: Relaxed thresholds, focus on major issues
- **Staging**: Standard thresholds, comprehensive analysis
- **Production**: Strict thresholds, zero critical issues
- **CI/CD**: Fast checks for pull requests, comprehensive for releases

Each profile includes specific thresholds and can be customized per project requirements, ensuring consistent quality standards across the entire ecosystem.
