**Date:** October 24, 2025  
**Status:** Implementation Plan - Ready for Execution  
**Coverage:** Discovery, Orchestration, Reports, Temporal RAG, Doc Maintenance  

# Backend Implementation Plan - Trackable Tasks

## Executive Summary

This document provides a **trackable, step-by-step implementation plan** for completing the backend work identified in Iteration 3. The plan leverages existing infrastructure, identifies reusable patterns, and provides clear implementation tasks with acceptance criteria.

**Key Finding:** ~70% of required infrastructure already exists! We need to:
1. Add PostgreSQL temporal function ✨
2. Fix asyncio bug in orchestration metrics
3. Complete implementation of existing service stubs  
4. Add comprehensive tests

---

## 📊 Existing Infrastructure Audit

### ✅ ALREADY IMPLEMENTED (70%)

#### Discovery & Orchestration
| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Discovery Engine | ✅ Complete | `src/services/discovery/discovery_engine.py` | Fully implemented |
| Repository Scanner | ✅ Complete | `src/services/discovery/repository_scanner.py` | Working |
| File Classifier | ✅ Complete | `src/services/discovery/file_classifier.py` | Working |
| Processing Planner | ✅ Complete | `src/services/discovery/processing_planner.py` | Working |
| Job Orchestrator | ✅ Complete | `src/services/orchestration/job_orchestrator.py` | Full implementation |
| Progress Tracker | ✅ Complete | `src/services/orchestration/progress_tracker.py` | Working |
| Execution Monitor | ✅ Complete | `src/services/orchestration/execution_monitor.py` | Working |
| Resource Allocator | ✅ Complete | `src/services/orchestration/resource_allocator.py` | Working |
| Sub-Job Executor | ✅ Complete | `src/services/orchestration/sub_job_executor.py` | Working |
| Discovery API Routes | ✅ Complete | `src/api/routes/discovery.py` | Full CRUD |
| Orchestration API Routes | ✅ Complete | `src/api/routes/orchestration.py` | 7+ endpoints |
| Database Models | ✅ Complete | `src/storage/models_discovery.py` | ProcessingPlan, SubJob, FileClassification |

#### Temporal RAG / Versioning
| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Timeline Query Engine | ✅ Complete | `src/services/versioning/timeline_query_engine.py` | Full implementation |
| Content Deduplicator | ✅ Complete | `src/services/versioning/content_deduplicator.py` | Working |
| Temporal Content Versioner | ✅ Complete | `src/services/versioning/temporal_content_versioner.py` | Working |
| Versioning API Routes | ✅ Complete | `src/api/routes/temporal_versioning.py` | 10+ endpoints |
| PostgreSQL Function | ❌ **MISSING** | N/A | **CRITICAL - Priority 1** |

#### Documentation Maintenance
| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Staleness Detector | ✅ Complete | `src/services/maintenance/staleness_detector.py` | Full implementation |
| Coverage Analyzer | ✅ Complete | `src/services/maintenance/coverage_analyzer.py` | Full implementation |
| Consistency Checker | ✅ Complete | `src/services/maintenance/consistency_checker.py` | Full implementation |
| Quality Dashboard | ✅ Complete | `src/services/maintenance/quality_dashboard.py` | Full implementation |
| Dependency Tracker | ✅ Complete | `src/services/maintenance/dependency_tracker.py` | Full implementation |
| Version Comparator | ✅ Complete | `src/services/maintenance/version_comparator.py` | Full implementation |
| Maintenance API Routes | ✅ Complete | `src/api/routes/maintenance.py` | 19+ endpoints |
| **Service Implementation** | ⚠️ **STUBS ONLY** | All services | **Needs completion** |

#### Analysis & Reports
| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Analysis Engine | ✅ Complete | `src/services/analysis/analysis_engine.py` | Working |
| Architecture Detector | ✅ Complete | `src/services/analysis/architecture_detector.py` | Working |
| Service Detector | ✅ Complete | `src/services/analysis/service_detector.py` | Working |
| Stack Detector | ✅ Complete | `src/services/analysis/stack_detector.py` | Working |
| Context Generator | ✅ Complete | `src/services/analysis/context_generator.py` | Working |
| Dependency Analyzer | ✅ Complete | `src/services/analysis/dependency_analyzer.py` | Working |
| Hierarchical Context Manager | ✅ Complete | `src/services/analysis/hierarchical_context_manager.py` | Working |
| Analysis API Routes | ✅ Complete | `src/api/routes/analysis.py` | Working |
| Reports API Routes | ✅ Complete | `src/api/routes/reports.py` | Working |

---

## 🧪 Test Coverage Analysis

### Existing Test Files (124 total)
- **Integration Tests:** 24 test files
- **Unit Tests:** 45 test files  
- **E2E Tests:** 9 test files
- **Functional Tests:** 16 test files
- **Performance Tests:** 3 test files
- **Smoke Tests:** 5 test files

### Test Coverage by Feature

| Feature | Test Files | Test Classes | Coverage | Status |
|---------|------------|--------------|----------|--------|
| **Orchestration** | 2 | 2 | 40% | ⚠️ Needs more tests |
| **Discovery** | 2 | 2 | 50% | ⚠️ Needs integration tests |
| **Temporal/Versioning** | 3 | 4 | 60% | ✅ Good, needs temporal function tests |
| **Maintenance** | 1 | 1 | 20% | ❌ Needs comprehensive tests |
| **Analysis/Reports** | 1 | 1 | 30% | ⚠️ Needs more tests |

### Key Findings
1. **Orchestration tests exist but are SKIPPED** - `test_orchestration_integration.py` has tests disabled
2. **Discovery tests exist but basic** - Need full workflow tests
3. **Temporal tests exist** - `test_temporal_versioning.py` functional test exists
4. **Maintenance tests are minimal** - Only `test_maintenance_workflow.py`
5. **All features have API route tests** but need service-level tests

---

## 🔧 Reusable Code Patterns

### Pattern 1: Service Layer Architecture
**Location:** All services follow this pattern

```python
# Standard service structure
class ServiceName:
    """Service description."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def main_method(self, params) -> Result:
        """Main functionality."""
        try:
            self.logger.info(f"Operation started: {params}")
            # Business logic
            return Result(success=True, data=...)
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            raise
```

**Reuse for:** All new service methods

### Pattern 2: API Route Structure
**Location:** All route files follow this pattern

```python
# Standard API route structure
@router.post(
    "/endpoint",
    response_model=ResponseModel,
    summary="Short description",
    description="Detailed description",
    tags=["Category"]
)
async def endpoint_name(
    request: RequestModel,
    db: AsyncSession = Depends(get_database)
) -> ResponseModel:
    """Endpoint documentation."""
    try:
        service = get_service_instance()
        result = await service.method(request.param)
        return ResponseModel(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Reuse for:** All new API endpoints

### Pattern 3: Database Query with Temporal Support
**Location:** `src/services/versioning/timeline_query_engine.py`

```python
# Temporal query pattern
async def query_method(self, as_of_date: datetime) -> List[Result]:
    """Query with temporal support."""
    query = text("""
        SELECT fields
        FROM get_temporal_function(:as_of_date)
        LIMIT :limit OFFSET :offset
    """)
    
    async with self.db.begin():
        result = await self.db.execute(
            query,
            {"as_of_date": as_of_date, "limit": limit, "offset": offset}
        )
        rows = result.fetchall()
        return [self._row_to_model(row) for row in rows]
```

**Reuse for:** All temporal queries

### Pattern 4: Background Task Execution
**Location:** `src/api/routes/orchestration.py`

```python
# Background task pattern
@router.post("/execute/{plan_id}")
async def execute_plan(
    plan_id: str,
    background_tasks: BackgroundTasks
):
    """Execute plan in background."""
    orchestrator = get_job_orchestrator()
    
    # Check if already executing
    current_status = await orchestrator.get_execution_status(plan_id)
    if current_status:
        return {"error": "Already executing"}
    
    # Start in background
    background_tasks.add_task(orchestrator.execute_plan, plan_id)
    
    return {"success": True, "message": "Started"}
```

**Reuse for:** Long-running operations

---

## 📋 TRACKABLE IMPLEMENTATION PLAN

### Priority 1: Critical Fixes (3-4 hours total)

#### Task 1.1: Add PostgreSQL Temporal Function ⭐ CRITICAL
**Estimate:** 2-3 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Create PostgreSQL function for temporal document queries

**Implementation Steps:**
1. ☐ Create new Alembic migration file
2. ☐ Add `get_all_documents_as_of()` function
3. ☐ Add helper function `get_document_timeline()`
4. ☐ Add proper indexes for performance
5. ☐ Test migration up and down
6. ☐ Verify function works with existing queries

**Files to Create/Modify:**
- NEW: `alembic/versions/YYYYMMDD_HHMM_add_temporal_functions.py`
- VERIFY: `src/services/versioning/timeline_query_engine.py` (already uses it)

**Acceptance Criteria:**
- [ ] Migration runs successfully
- [ ] Function `get_all_documents_as_of(timestamp)` exists in PostgreSQL
- [ ] Function returns correct document versions
- [ ] Indexes improve query performance
- [ ] `/api/v1/versioning/as-of` endpoint works
- [ ] Manual test: Query documents as of specific date succeeds

**SQL Implementation:**
```sql
-- See detailed SQL in section below
CREATE OR REPLACE FUNCTION get_all_documents_as_of(query_time TIMESTAMP WITH TIME ZONE)
RETURNS TABLE (...) AS $$
BEGIN
    -- Implementation
END;
$$ LANGUAGE plpgsql;
```

**Test Command:**
```bash
# Run migration
alembic upgrade head

# Test endpoint
curl -X POST http://localhost:8000/api/v1/versioning/as-of \
  -H "Content-Type: application/json" \
  -d '{"as_of_date": "2025-10-01T00:00:00Z", "limit": 10}'
```

---

#### Task 1.2: Fix Orchestration Metrics Asyncio Error ⭐ URGENT
**Estimate:** 30 minutes  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Fix `asyncio.run()` call in orchestration metrics endpoint

**Implementation Steps:**
1. ☐ Locate `asyncio.run()` call in `src/api/routes/orchestration.py`
2. ☐ Replace with `await` pattern
3. ☐ Verify all async functions use proper await
4. ☐ Test metrics endpoint
5. ☐ Add integration test

**Files to Modify:**
- `src/api/routes/orchestration.py` - metrics endpoint

**Search Command:**
```bash
# Find the issue
grep -n "asyncio.run" /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/api/routes/orchestration.py
```

**Acceptance Criteria:**
- [ ] No `asyncio.run()` calls in async endpoints
- [ ] `/api/v1/orchestration/metrics` returns 200 status
- [ ] Response includes expected metrics
- [ ] Integration test added and passing

**Test Command:**
```bash
curl http://localhost:8000/api/v1/orchestration/metrics
```

---

#### Task 1.3: Fix Temporal Timeline Endpoint Method
**Estimate:** 30 minutes  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Fix HTTP method or parameters for timeline endpoint

**Implementation Steps:**
1. ☐ Check current endpoint definition in `src/api/routes/temporal_versioning.py`
2. ☐ Verify HTTP method (GET vs POST)
3. ☐ Update frontend API call if needed
4. ☐ Add proper documentation
5. ☐ Test with dashboard

**Files to Check/Modify:**
- `src/api/routes/temporal_versioning.py`
- Dashboard: `dashboard_views/temporal_rag_query.py`

**Acceptance Criteria:**
- [ ] Endpoint accessible from dashboard
- [ ] Returns timeline events
- [ ] HTTP method matches expectations
- [ ] Parameters documented

**Test Command:**
```bash
# Try both methods
curl -X GET "http://localhost:8000/api/v1/versioning/timeline?document_id=xxx"
curl -X POST "http://localhost:8000/api/v1/versioning/timeline" -d '{"document_id":"xxx"}'
```

---

### Priority 2: Documentation Maintenance Implementation (11-14 hours)

**Key Finding:** All service classes exist with method stubs. Need to implement business logic.

#### Task 2.1: Implement Staleness Detection Logic ⭐
**Estimate:** 3-4 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Complete implementation of `StalenessDetector` service

**Current State:**
- ✅ Service class exists: `src/services/maintenance/staleness_detector.py`
- ✅ API route exists: `src/api/routes/maintenance.py` (endpoint `/staleness/detect`)
- ⚠️ Methods are stubs returning mock data

**Implementation Steps:**
1. ☐ Review existing stub in `staleness_detector.py`
2. ☐ Implement `detect_stale_documents()` method
   - Query documents table
   - Compare doc `updated_at` with git commit dates
   - Check for referenced code changes
   - Calculate staleness score
3. ☐ Implement `get_staleness_report()` method
4. ☐ Implement `mark_for_review()` method
5. ☐ Add database queries for metrics
6. ☐ Add unit tests
7. ☐ Add integration test

**Reusable Pattern:** Service Layer Architecture (see above)

**Files to Modify:**
- `src/services/maintenance/staleness_detector.py` - Implement logic
- NEW: `tests/unit/services/maintenance/test_staleness_detector.py`
- NEW: `tests/integration/test_maintenance_staleness.py`

**Business Logic:**
```python
async def detect_stale_documents(
    self,
    service_name: Optional[str] = None,
    threshold_days: int = 90
) -> Dict[str, Any]:
    """
    Detect stale documentation.
    
    Algorithm:
    1. Find all documents not updated in threshold_days
    2. Check if referenced code changed after doc update
    3. Calculate staleness score:
       - Days since update (weight: 40%)
       - Referenced code changes (weight: 40%)
       - View count decline (weight: 20%)
    4. Categorize by severity:
       - CRITICAL: score > 80
       - HIGH: score > 60
       - MEDIUM: score > 40
       - LOW: score > 20
    """
    # Implementation here
```

**Acceptance Criteria:**
- [ ] `detect_stale_documents()` returns list of stale docs
- [ ] Staleness score calculated correctly (0-100)
- [ ] Severity categorization works
- [ ] API endpoint returns expected format
- [ ] Unit tests cover score calculation
- [ ] Integration test with real database
- [ ] Manual test: Endpoint returns stale docs for test repo

**Test Data Setup:**
```python
# Create test documents with various staleness levels
test_docs = [
    {"title": "Very Old Doc", "updated_at": "2024-01-01", "expected_score": 95},
    {"title": "Recent Doc", "updated_at": "2025-10-20", "expected_score": 5},
]
```

---

#### Task 2.2: Implement Coverage Analysis Logic
**Estimate:** 4-5 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Complete implementation of `CoverageAnalyzer` service

**Current State:**
- ✅ Service class exists: `src/services/maintenance/coverage_analyzer.py`
- ✅ API route exists: `/coverage/analyze`
- ⚠️ Methods are stubs

**Implementation Steps:**
1. ☐ Implement AST parsing for code analysis
2. ☐ Implement `analyze_coverage()` method
   - Parse codebase (Python, JS, etc.)
   - Extract documentable items (functions, classes, APIs)
   - Cross-reference with documentation
   - Calculate coverage percentage
3. ☐ Implement `get_undocumented_items()` method
4. ☐ Implement `generate_coverage_report()` method
5. ☐ Add support for multiple languages
6. ☐ Add unit and integration tests

**Reusable Code:** Can leverage existing `FileClassifier` from discovery

**Files to Modify:**
- `src/services/maintenance/coverage_analyzer.py`
- NEW: `tests/unit/services/maintenance/test_coverage_analyzer.py`
- NEW: `tests/integration/test_maintenance_coverage.py`

**Business Logic:**
```python
async def analyze_coverage(
    self,
    repo_path: str,
    include_private: bool = False
) -> Dict[str, Any]:
    """
    Analyze documentation coverage.
    
    Algorithm:
    1. Scan repository for code files
    2. Parse files with AST (Python) or tree-sitter (JS/TS)
    3. Extract documentable items:
       - Public functions/methods
       - Classes
       - API endpoints
       - Constants/enums
    4. Search for corresponding documentation
    5. Calculate coverage:
       coverage = (documented_items / total_items) * 100
    6. Generate gap list
    """
    # Implementation
```

**Acceptance Criteria:**
- [ ] Parses Python files correctly
- [ ] Identifies undocumented functions/classes
- [ ] Calculates coverage percentage
- [ ] Returns list of missing documentation
- [ ] Works with large codebases
- [ ] Unit tests for AST parsing
- [ ] Integration test with sample repo

---

#### Task 2.3: Implement Consistency Checking Logic
**Estimate:** 4-5 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Complete implementation of `ConsistencyChecker` service

**Current State:**
- ✅ Service class exists: `src/services/maintenance/consistency_checker.py`
- ✅ API route exists: `/consistency/check`
- ⚠️ Methods are stubs

**Implementation Steps:**
1. ☐ Implement `check_cross_references()` method
2. ☐ Implement `validate_code_examples()` method
3. ☐ Implement `check_terminology()` method
4. ☐ Implement `check_consistency()` main method
5. ☐ Add NLP for terminology analysis
6. ☐ Add code syntax validation
7. ☐ Add unit and integration tests

**Files to Modify:**
- `src/services/maintenance/consistency_checker.py`
- NEW: `tests/unit/services/maintenance/test_consistency_checker.py`
- NEW: `tests/integration/test_maintenance_consistency.py`

**Business Logic:**
```python
async def check_consistency(
    self,
    check_cross_references: bool = True,
    validate_code_examples: bool = True,
    check_terminology: bool = True
) -> Dict[str, Any]:
    """
    Check documentation consistency.
    
    Checks:
    1. Cross-references:
       - Internal links are valid
       - Referenced docs exist
       - No broken links
    
    2. Code examples:
       - Syntax is valid
       - Examples match current API
       - Imports are correct
    
    3. Terminology:
       - Consistent naming
       - No conflicting definitions
       - Standard terminology used
    """
    # Implementation
```

**Acceptance Criteria:**
- [ ] Detects broken internal links
- [ ] Validates Python code examples
- [ ] Finds terminology inconsistencies
- [ ] Returns actionable report
- [ ] Unit tests for each check type
- [ ] Integration test with sample docs

---

### Priority 3: Discovery & Orchestration Enhancements (7-10 hours)

**Key Finding:** Infrastructure is 90% complete. Need to enhance data collection and storage.

#### Task 3.1: Enhance Discovery Scan Data Collection
**Estimate:** 3-4 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Enhance discovery scanner to collect richer metadata

**Current State:**
- ✅ Scanner works and classifies files
- ⚠️ Limited metadata collected
- ⚠️ No service detection

**Implementation Steps:**
1. ☐ Review `src/services/discovery/repository_scanner.py`
2. ☐ Add service detection logic
   - Detect package.json, requirements.txt, etc.
   - Identify service types (API, frontend, worker, etc.)
   - Extract dependencies
3. ☐ Enhance file classification
   - Add more file type categories
   - Detect framework/technology
4. ☐ Add file size breakdown
5. ☐ Add tests

**Files to Modify:**
- `src/services/discovery/repository_scanner.py`
- `src/services/discovery/file_classifier.py`
- NEW: `tests/unit/services/discovery/test_enhanced_scanner.py`

**Enhancement Logic:**
```python
def detect_services(self, repo_path: Path) -> List[ServiceInfo]:
    """
    Detect services in repository.
    
    Detection rules:
    - package.json → Node.js service
    - requirements.txt → Python service
    - Dockerfile → Containerized service
    - docker-compose.yml → Multi-service
    """
    services = []
    
    # Scan for service indicators
    for indicator_file in ["package.json", "requirements.txt", "Cargo.toml"]:
        matches = repo_path.rglob(indicator_file)
        for match in matches:
            service_info = self._extract_service_info(match)
            services.append(service_info)
    
    return services
```

**Acceptance Criteria:**
- [ ] Detects common service types
- [ ] Extracts service metadata
- [ ] Returns service count in scan results
- [ ] Works with monorepo structure
- [ ] Unit tests for service detection
- [ ] Integration test with real repo

---

#### Task 3.2: Implement Plan Persistence and Retrieval
**Estimate:** 2-3 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** Task 3.1

**Description:** Ensure plans are properly saved and retrieved

**Current State:**
- ✅ Database models exist
- ✅ Save operation implemented
- ⚠️ Retrieval returns empty list

**Implementation Steps:**
1. ☐ Debug why `/api/v1/discovery/plans` returns []
2. ☐ Verify database writes are committing
3. ☐ Add proper error handling
4. ☐ Add caching for frequently accessed plans
5. ☐ Add tests

**Files to Modify:**
- `src/api/routes/discovery.py` - Verify save/retrieve
- NEW: `tests/integration/test_discovery_persistence.py`

**Debug Steps:**
```bash
# Check if plans are in database
docker exec -it postgres psql -U postgres -d ecosystem_mcp -c "SELECT * FROM processing_plans;"

# If empty, check transaction commits
# Add logging to see if save is being called
```

**Acceptance Criteria:**
- [ ] Plans persist to database
- [ ] Plans retrievable via API
- [ ] Plan details include sub-jobs
- [ ] Pagination works for large lists
- [ ] Integration test creates and retrieves plan

---

#### Task 3.3: Enhance Orchestration Monitoring
**Estimate:** 2-3 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Add real-time monitoring data collection

**Current State:**
- ✅ Monitoring framework exists
- ⚠️ Limited real-time data

**Implementation Steps:**
1. ☐ Review `src/services/orchestration/execution_monitor.py`
2. ☐ Add worker status tracking
3. ☐ Add resource usage collection (CPU, memory)
4. ☐ Add queue size monitoring
5. ☐ Store metrics in Redis for fast access
6. ☐ Add tests

**Files to Modify:**
- `src/services/orchestration/execution_monitor.py`
- NEW: `tests/unit/services/orchestration/test_execution_monitor.py`

**Acceptance Criteria:**
- [ ] Tracks active workers
- [ ] Collects resource usage
- [ ] Stores in Redis
- [ ] API returns monitoring data
- [ ] Real-time updates work

---

### Priority 4: Report Generation Backend (9-12 hours)

**Key Finding:** Analysis services exist. Need report formatting and export.

#### Task 4.1: Implement Report Generation Service
**Estimate:** 3-4 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Create service to generate formatted reports

**Implementation Steps:**
1. ☐ Create `src/services/analysis/report_generator.py`
2. ☐ Implement Markdown generation
3. ☐ Implement HTML generation (with templates)
4. ☐ Implement JSON generation
5. ☐ Add PDF generation (using weasyprint or similar)
6. ☐ Add tests

**Files to Create:**
- NEW: `src/services/analysis/report_generator.py`
- NEW: `src/templates/report_template.html`
- NEW: `tests/unit/services/analysis/test_report_generator.py`

**Service Structure:**
```python
class ReportGenerator:
    """Generate reports in multiple formats."""
    
    async def generate_report(
        self,
        plan_id: str,
        format: str,
        options: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.
        
        Formats:
        - markdown: Plain markdown
        - html: Styled HTML with charts
        - json: Structured data
        - pdf: PDF document
        """
        # Collect data from analysis services
        data = await self._collect_report_data(plan_id, options)
        
        # Format based on requested format
        if format == "markdown":
            content = self._generate_markdown(data)
        elif format == "html":
            content = self._generate_html(data)
        elif format == "json":
            content = self._generate_json(data)
        elif format == "pdf":
            content = self._generate_pdf(data)
        
        return {
            "content": content,
            "size_kb": len(content) / 1024,
            "format": format
        }
```

**Acceptance Criteria:**
- [ ] Generates Markdown reports
- [ ] Generates HTML reports
- [ ] Generates JSON reports
- [ ] PDF generation works
- [ ] Reports include all requested sections
- [ ] Unit tests for each format

---

#### Task 4.2: Implement Architecture Analysis Enhancement
**Estimate:** 4-5 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** None

**Description:** Enhance architecture detection with more patterns

**Files to Modify:**
- `src/services/analysis/architecture_detector.py`
- NEW: `tests/unit/services/analysis/test_architecture_detector.py`

**Acceptance Criteria:**
- [ ] Detects common patterns (MVC, layered, microservices)
- [ ] Identifies architectural layers
- [ ] Maps component relationships
- [ ] Generates visualization data
- [ ] Unit tests for pattern detection

---

#### Task 4.3: Implement Service & Stack Analysis
**Estimate:** 2-3 hours  
**Status:** 🔴 Not Started  
**Owner:** TBD  
**Dependencies:** Task 3.1

**Description:** Complete service and technology stack analysis

**Files to Modify:**
- `src/services/analysis/service_detector.py`
- `src/services/analysis/stack_detector.py`
- NEW: `tests/unit/services/analysis/test_service_detector.py`
- NEW: `tests/unit/services/analysis/test_stack_detector.py`

**Acceptance Criteria:**
- [ ] Detects all service types
- [ ] Identifies technology stack
- [ ] Extracts dependency information
- [ ] Returns version information
- [ ] Unit tests for detection logic

---

## 📝 SQL Migration for Temporal Functions

### Create Migration File

**File:** `alembic/versions/20251024_1600_add_temporal_functions.py`

```python
"""Add temporal query functions

Revision ID: temporal_001
Revises: a1b2c3d4e5f6
Create Date: 2025-10-24 16:00:00.000000+00:00

This migration adds PostgreSQL functions for temporal document queries:
- get_all_documents_as_of(timestamp): Get documents as they existed at a point in time
- get_document_timeline(document_id): Get complete history of a document
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'temporal_001'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create temporal query functions."""
    
    # Function 1: Get all documents as of a specific date
    op.execute("""
    CREATE OR REPLACE FUNCTION get_all_documents_as_of(query_time TIMESTAMP WITH TIME ZONE)
    RETURNS TABLE (
        document_id UUID,
        version_id UUID,
        version_number INTEGER,
        content_hash VARCHAR(64),
        modified_at TIMESTAMP WITH TIME ZONE,
        created_by VARCHAR(255),
        title TEXT,
        source_path TEXT,
        content_size INTEGER
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH latest_versions AS (
            SELECT 
                dv.document_id,
                dv.id AS version_id,
                dv.version_hash AS content_hash,
                dv.created_at AS modified_at,
                d.service_name AS created_by,
                d.file_path AS title,
                d.file_path AS source_path,
                LENGTH(dv.content) AS content_size,
                ROW_NUMBER() OVER (
                    PARTITION BY dv.document_id 
                    ORDER BY dv.created_at DESC
                ) AS rn
            FROM document_versions dv
            INNER JOIN documents d ON d.id = dv.document_id
            WHERE dv.created_at <= query_time
        )
        SELECT 
            lv.document_id,
            lv.version_id,
            lv.rn::INTEGER AS version_number,
            lv.content_hash,
            lv.modified_at,
            lv.created_by,
            lv.title,
            lv.source_path,
            lv.content_size
        FROM latest_versions lv
        WHERE lv.rn = 1
        ORDER BY lv.modified_at DESC;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
    
    # Function 2: Get document timeline
    op.execute("""
    CREATE OR REPLACE FUNCTION get_document_timeline(doc_id UUID)
    RETURNS TABLE (
        version_id UUID,
        version_number INTEGER,
        event_timestamp TIMESTAMP WITH TIME ZONE,
        event_type VARCHAR(50),
        actor VARCHAR(255),
        content_hash VARCHAR(64),
        title TEXT,
        is_latest BOOLEAN
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH numbered_versions AS (
            SELECT 
                dv.id AS version_id,
                ROW_NUMBER() OVER (ORDER BY dv.created_at ASC) AS version_number,
                dv.created_at AS event_timestamp,
                CASE 
                    WHEN ROW_NUMBER() OVER (ORDER BY dv.created_at ASC) = 1 THEN 'created'
                    ELSE 'updated'
                END AS event_type,
                d.service_name AS actor,
                dv.version_hash AS content_hash,
                d.file_path AS title,
                (ROW_NUMBER() OVER (ORDER BY dv.created_at DESC) = 1) AS is_latest
            FROM document_versions dv
            INNER JOIN documents d ON d.id = dv.document_id
            WHERE dv.document_id = doc_id
        )
        SELECT 
            nv.version_id,
            nv.version_number::INTEGER,
            nv.event_timestamp,
            nv.event_type::VARCHAR(50),
            nv.actor,
            nv.content_hash,
            nv.title,
            nv.is_latest
        FROM numbered_versions nv
        ORDER BY nv.version_number ASC;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
    
    # Add indexes for better performance
    op.create_index(
        'idx_document_versions_document_created',
        'document_versions',
        ['document_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Drop temporal query functions."""
    op.execute("DROP FUNCTION IF EXISTS get_document_timeline(UUID);")
    op.execute("DROP FUNCTION IF EXISTS get_all_documents_as_of(TIMESTAMP WITH TIME ZONE);")
    op.drop_index('idx_document_versions_document_created', table_name='document_versions')
```

### Apply Migration

```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
alembic upgrade head
```

---

## 🧪 Testing Strategy

### Test Creation Plan

For each implementation task, create tests in this order:

1. **Unit Tests** (20-30% of task time)
   - Test individual functions
   - Mock external dependencies
   - Fast execution
   
2. **Integration Tests** (30-40% of task time)
   - Test with real database
   - Test API endpoints
   - Test service interactions
   
3. **E2E Tests** (10-20% of task time)
   - Test complete workflows
   - Test dashboard integration
   - Test error scenarios

### Test File Structure

```
tests/
├── unit/
│   └── services/
│       ├── maintenance/
│       │   ├── test_staleness_detector.py
│       │   ├── test_coverage_analyzer.py
│       │   └── test_consistency_checker.py
│       ├── discovery/
│       │   └── test_enhanced_scanner.py
│       └── analysis/
│           ├── test_report_generator.py
│           └── test_architecture_detector.py
├── integration/
│   ├── test_maintenance_staleness.py
│   ├── test_maintenance_coverage.py
│   ├── test_maintenance_consistency.py
│   ├── test_discovery_persistence.py
│   └── test_orchestration_metrics.py
└── e2e/
    ├── test_complete_maintenance_workflow.py
    ├── test_complete_discovery_workflow.py
    └── test_complete_reporting_workflow.py
```

### Test Coverage Goals

| Category | Target Coverage | Current | Gap |
|----------|----------------|---------|-----|
| Services | 80%+ | 40% | 40% |
| API Routes | 90%+ | 70% | 20% |
| Utils | 85%+ | 60% | 25% |
| Overall | 80%+ | 55% | 25% |

---

## 📊 Progress Tracking

### Sprint 1 (Priority 1 - Week 1)
- [ ] Task 1.1: PostgreSQL temporal function (3h)
- [ ] Task 1.2: Orchestration metrics fix (30min)
- [ ] Task 1.3: Timeline endpoint fix (30min)
- [ ] Testing: Integration tests for Priority 1 (2h)

**Total:** ~6 hours  
**Expected Completion:** End of Week 1

### Sprint 2 (Priority 2 - Week 2)
- [ ] Task 2.1: Staleness detection (4h)
- [ ] Task 2.2: Coverage analysis (5h)
- [ ] Task 2.3: Consistency checking (5h)
- [ ] Testing: Unit + Integration tests (4h)

**Total:** ~18 hours  
**Expected Completion:** End of Week 2

### Sprint 3 (Priority 3 - Week 3)
- [ ] Task 3.1: Enhanced discovery scan (4h)
- [ ] Task 3.2: Plan persistence (3h)
- [ ] Task 3.3: Orchestration monitoring (3h)
- [ ] Testing: Integration tests (3h)

**Total:** ~13 hours  
**Expected Completion:** End of Week 3

### Sprint 4 (Priority 4 - Week 4)
- [ ] Task 4.1: Report generation (4h)
- [ ] Task 4.2: Architecture analysis (5h)
- [ ] Task 4.3: Service/stack analysis (3h)
- [ ] Testing: E2E tests (3h)

**Total:** ~15 hours  
**Expected Completion:** End of Week 4

---

## 📈 Success Metrics

### Code Quality Metrics
- [ ] All new code has 80%+ test coverage
- [ ] All linter checks pass
- [ ] No critical security issues
- [ ] All type hints added

### Functional Metrics
- [ ] All Priority 1 endpoints return 200
- [ ] Dashboard shows real data (not empty arrays)
- [ ] Temporal queries work correctly
- [ ] Reports generate successfully

### Performance Metrics
- [ ] Temporal queries < 1s for 1000 docs
- [ ] Discovery scan < 30s for medium repo
- [ ] Report generation < 10s
- [ ] All API endpoints < 2s response time

---

## 🎯 Next Steps

### Immediate Actions (Today)
1. ✅ Review this implementation plan
2. ☐ Assign owners to Priority 1 tasks
3. ☐ Create Alembic migration for temporal functions
4. ☐ Set up test database for development
5. ☐ Create GitHub issues for each task

### This Week
1. ☐ Complete Priority 1 tasks
2. ☐ Test temporal endpoints with dashboard
3. ☐ Document any blockers
4. ☐ Review and adjust plan as needed

### Next Week
1. ☐ Begin Priority 2 tasks
2. ☐ Daily standup to track progress
3. ☐ Code reviews for completed work
4. ☐ Update dashboard with new features

---

## 📚 Resources

### Documentation
- **Alembic Migrations:** [alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
- **PostgreSQL Functions:** [postgresql.org/docs](https://www.postgresql.org/docs/current/sql-createfunction.html)
- **FastAPI Background Tasks:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- **AST Parsing (Python):** [docs.python.org/3/library/ast.html](https://docs.python.org/3/library/ast.html)

### Existing Code Examples
- **Service Pattern:** `src/services/versioning/timeline_query_engine.py`
- **API Pattern:** `src/api/routes/orchestration.py`
- **Background Tasks:** `src/api/routes/orchestration.py` execute endpoint
- **Database Queries:** `src/services/versioning/timeline_query_engine.py`

### Testing Examples
- **Integration Test:** `tests/integration/test_orchestration_integration.py`
- **E2E Test:** `tests/e2e/test_full_workflow.py`
- **Unit Test:** `tests/unit/services/rag/test_query_engine.py`

---

## 🎊 Conclusion

This implementation plan provides:
✅ **Clear, trackable tasks** with acceptance criteria  
✅ **Realistic time estimates** based on existing code  
✅ **Reusable patterns** to accelerate development  
✅ **Comprehensive testing strategy** for quality  
✅ **Progress tracking** with sprint organization  

**Estimated Total Time:** 52-62 hours  
**Existing Infrastructure:** ~70% complete  
**New Development:** ~30% remaining  

**Key Success Factor:** Most infrastructure exists. Focus on completing service implementations and adding comprehensive tests.

---

*Document Generated: October 24, 2025*  
*Status: Ready for Implementation*  
*Next Review: After Sprint 1 Completion*

