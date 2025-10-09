# Domain Model - code-analyzer

**Service**: code-analyzer  
**Date**: October 9, 2025  
**Phase**: 2.1 Domain Modeling

---

## 🎯 Bounded Context

**code-analyzer** operates within the **Code Analysis Context**, responsible for:
- Extracting structural information from source code
- Identifying code patterns and anti-patterns
- Measuring code complexity
- Detecting security vulnerabilities
- Providing analysis data to other services (primarily prompt-store)

**Out of Scope**:
- Actual code execution or compilation
- Code generation or modification
- Long-term storage of analysis results (consumed by others)
- User authentication (handled by shared infrastructure)

---

## 📊 Core Domain Entities

### 1. CodeAnalysis (Aggregate Root)

**Purpose**: Represents a complete analysis of a code artifact

**Attributes**:
- `analysis_id: UUID` - Unique identifier
- `code_content: str` - Source code being analyzed
- `language: Language` - Programming language (value object)
- `timestamp: datetime` - When analysis was performed
- `status: AnalysisStatus` - Current state of analysis
- `results: AnalysisResults` - Analysis findings (entity)

**Invariants**:
- Must have non-empty code content
- Language must be supported
- Results must be present if status is COMPLETED

**Lifecycle**:
```
PENDING → ANALYZING → COMPLETED
                   ↓
                FAILED
```

---

### 2. AnalysisResults (Entity)

**Purpose**: Contains all findings from code analysis

**Attributes**:
- `structures: List[CodeStructure]` - Functions, classes discovered
- `complexity_metrics: ComplexityMetrics` - Cyclomatic complexity, etc.
- `style_issues: List[StyleIssue]` - Code style violations
- `security_findings: List[SecurityFinding]` - Security vulnerabilities
- `imports: List[ImportStatement]` - External dependencies used
- `patterns: List[DetectedPattern]` - Design patterns identified

**Invariants**:
- All lists must be initialized (can be empty)
- Complexity metrics must be non-negative

---

### 3. CodeStructure (Entity)

**Purpose**: Represents a structural element (function, class, module)

**Attributes**:
- `structure_type: StructureType` - FUNCTION, CLASS, MODULE
- `name: str` - Identifier name
- `line_start: int` - Starting line number
- `line_end: int` - Ending line number
- `docstring: Optional[str]` - Documentation string
- `parameters: List[Parameter]` - For functions/methods
- `methods: List[CodeStructure]` - For classes (recursive)

**Invariants**:
- Name must be valid identifier
- line_start <= line_end
- If type is CLASS, may have methods

---

## 💎 Value Objects

### Language

**Purpose**: Represents supported programming language

**Values**:
- `PYTHON`
- `JAVASCRIPT`
- `TYPESCRIPT`
- `JAVA`
- `GO`
- `RUST`

**Properties**:
- Immutable
- Has file extensions mapping
- Has syntax rules reference

---

### AnalysisStatus

**Purpose**: State of analysis process

**Values**:
- `PENDING` - Queued for analysis
- `ANALYZING` - Currently processing
- `COMPLETED` - Successfully finished
- `FAILED` - Error occurred

---

### ComplexityMetrics

**Purpose**: Code complexity measurements

**Attributes**:
- `cyclomatic_complexity: int` - Decision point count
- `cognitive_complexity: int` - Mental load metric
- `maintainability_index: float` - 0-100 score
- `lines_of_code: int` - Total lines
- `comment_ratio: float` - % of comment lines

**Invariants**:
- All metrics non-negative
- Ratios between 0.0 and 1.0
- Maintainability index between 0 and 100

---

### StyleIssue

**Purpose**: Code style violation

**Attributes**:
- `severity: Severity` - ERROR, WARNING, INFO
- `line_number: int` - Where issue occurs
- `message: str` - Description of issue
- `rule_id: str` - Style rule violated (e.g., "E501")

---

### SecurityFinding

**Purpose**: Potential security vulnerability

**Attributes**:
- `severity: Severity` - CRITICAL, HIGH, MEDIUM, LOW
- `vulnerability_type: str` - SQL injection, XSS, etc.
- `line_number: int` - Location in code
- `description: str` - Detailed explanation
- `recommendation: str` - How to fix

---

## 🔄 Domain Services

### CodeAnalyzer (Domain Service)

**Purpose**: Orchestrates analysis of code

**Methods**:
```python
def analyze_code(
    code: str,
    language: Language,
    options: AnalysisOptions
) -> CodeAnalysis:
    """
    Perform comprehensive analysis of code.
    
    Returns CodeAnalysis aggregate with all findings.
    """
```

**Responsibilities**:
- Validate input
- Coordinate sub-analyzers
- Aggregate results
- Apply business rules

---

### StructureExtractor (Domain Service)

**Purpose**: Extracts structural elements from code

**Methods**:
```python
def extract_structures(
    code: str,
    language: Language
) -> List[CodeStructure]:
    """
    Parse code and identify functions, classes, modules.
    """
```

---

### ComplexityCalculator (Domain Service)

**Purpose**: Calculates complexity metrics

**Methods**:
```python
def calculate_complexity(
    structures: List[CodeStructure]
) -> ComplexityMetrics:
    """
    Compute cyclomatic and cognitive complexity.
    """
```

---

### SecurityScanner (Domain Service)

**Purpose**: Identifies security vulnerabilities

**Methods**:
```python
def scan_for_vulnerabilities(
    code: str,
    language: Language
) -> List[SecurityFinding]:
    """
    Check for common security issues.
    """
```

---

## 📐 Domain Model Diagram

```
┌─────────────────────────────────────────────────┐
│           CodeAnalysis (Aggregate Root)          │
├─────────────────────────────────────────────────┤
│ - analysis_id: UUID                              │
│ - code_content: str                              │
│ - language: Language (VO)                        │
│ - timestamp: datetime                            │
│ - status: AnalysisStatus (VO)                    │
│ - results: AnalysisResults                       │
└──────────────────┬──────────────────────────────┘
                   │ owns
                   ▼
        ┌─────────────────────┐
        │  AnalysisResults     │
        ├─────────────────────┤
        │ - structures []      │───┐
        │ - complexity_metrics │   │
        │ - style_issues []    │   │ contains
        │ - security_findings []   │
        │ - imports []         │   │
        │ - patterns []        │   │
        └─────────────────────┘   │
                                  ▼
                    ┌──────────────────────┐
                    │   CodeStructure      │
                    ├──────────────────────┤
                    │ - structure_type     │
                    │ - name               │
                    │ - line_start/end     │
                    │ - parameters []      │
                    │ - methods []         │─┐ recursive
                    └──────────────────────┘ └─────────┘

Value Objects:
┌──────────┐  ┌─────────────┐  ┌──────────────────┐
│ Language │  │AnalysisStatus│  │ComplexityMetrics │
└──────────┘  └─────────────┘  └──────────────────┘

Domain Services:
┌──────────────┐  ┌────────────────────┐  ┌──────────────────┐
│CodeAnalyzer  │  │StructureExtractor  │  │ComplexityCalc    │
└──────────────┘  └────────────────────┘  └──────────────────┘
```

---

## 🔐 Invariants & Business Rules

### Business Rule 1: Supported Languages Only
- Analysis can only be performed on supported languages
- Invalid language request should fail fast
- Language detection can be attempted if not provided

### Business Rule 2: Minimum Code Length
- Code must be at least 1 non-whitespace line
- Empty or whitespace-only code returns empty results (not error)

### Business Rule 3: Complexity Thresholds
- Functions with cyclomatic complexity > 10 flagged as "complex"
- Files with maintainability index < 20 flagged as "unmaintainable"

### Business Rule 4: Security Severity
- CRITICAL findings must be elevated in results
- At least one security check must run per analysis

---

## 🎭 Ubiquitous Language

**Terms used consistently across the domain**:

- **Analysis**: The process of examining code and extracting information
- **Structure**: A code element (function, class, module)
- **Complexity**: Measurement of code difficulty to understand/maintain
- **Finding**: Something discovered during analysis (issue, pattern)
- **Severity**: Importance level of a finding
- **Pattern**: Recognized design pattern or anti-pattern
- **Artifact**: Piece of code being analyzed
- **Extraction**: Process of identifying structures
- **Scanning**: Process of checking for issues

---

## 📦 Aggregates

### CodeAnalysis Aggregate

**Aggregate Root**: CodeAnalysis

**Members**:
- CodeAnalysis (root)
- AnalysisResults (entity)
- Multiple CodeStructure entities (entities)
- Multiple value objects (StyleIssue, SecurityFinding, etc.)

**Boundary**:
- All access to AnalysisResults goes through CodeAnalysis
- CodeStructures cannot exist outside an analysis
- Changes to any member must validate aggregate invariants

**Consistency**:
- Status must match results state
- All results must be for the same code artifact
- Modifications are atomic within aggregate

---

## 🔄 Domain Events

### AnalysisCompleted

**Triggered**: When analysis finishes successfully

**Data**:
- `analysis_id: UUID`
- `service_name: str` - "code-analyzer"
- `completion_timestamp: datetime`
- `results_summary: dict` - High-level findings

**Subscribers**: 
- prompt-store (consumes results)
- monitoring (tracks metrics)

---

### AnalysisFailed

**Triggered**: When analysis encounters error

**Data**:
- `analysis_id: UUID`
- `error_type: str`
- `error_message: str`
- `failed_at: datetime`

**Subscribers**:
- monitoring (alerts on failures)

---

## 🏗️ Repository Interfaces

### ICodeAnalysisRepository

**Purpose**: Persistence of analysis results (if needed)

**Methods**:
```python
def save(analysis: CodeAnalysis) -> None
def find_by_id(analysis_id: UUID) -> Optional[CodeAnalysis]
def find_recent(limit: int) -> List[CodeAnalysis]
```

**Note**: Current implementation may be ephemeral (no persistence)

---

## ✅ Domain Model Completeness Checklist

- [x] Bounded context defined
- [x] Core entities identified (CodeAnalysis, AnalysisResults, CodeStructure)
- [x] Value objects defined (Language, Status, Metrics, etc.)
- [x] Aggregates identified (CodeAnalysis aggregate)
- [x] Domain services specified (Analyzer, Extractor, Calculator, Scanner)
- [x] Invariants documented
- [x] Business rules captured
- [x] Ubiquitous language established
- [x] Domain events defined
- [x] Repository interfaces sketched

---

## 📝 Implementation Notes

**Next Steps**:
1. Validate domain model with stakeholders
2. Create domain layer implementation (Phase 3)
3. Design application services (Phase 2.2)
4. Plan testing strategy (Phase 2.3)

**Key Decisions**:
- Analysis is ephemeral (no persistence initially)
- Focus on Python analysis first, extend to other languages later
- Security scanning is basic (not comprehensive penetration testing)
- Complexity metrics use standard industry formulas

---

**Domain Model Complete**  
**Ready for Phase 2.2: API Design**

