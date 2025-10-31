# UTC Standardization: Enriched Implementation Plan

**Date:** October 26, 2025  
**Status:** 🎯 Ready for Phased Implementation  
**Scope:** Complete Codebase Audit & Integration Strategy

---

## 🔍 Codebase Audit Summary

### Services Audited
1. ✅ **services/ecosystem-mcp** - Main API service (86 files with datetime usage)
2. ✅ **services/ecosystem-mcp-dashboard** - Streamlit dashboard (datetime display & input)
3. ✅ **services/ecosystem-mcp-embedding** - Embedding generation service

### Datetime Usage Patterns Discovered

#### Pattern 1: `datetime.utcnow()` - Already UTC ✅
**Files:** 86 occurrences across main service

**Current Usage (Good):**
```python
# Models
created_at: datetime = Field(default_factory=datetime.utcnow)
updated_at: datetime = Field(default_factory=datetime.utcnow)

# Services
now = datetime.utcnow()
timeline.created_at = now
```

**Status:** ✅ Already using UTC  
**Action:** Replace with `now_utc_naive()` for consistency  
**Priority:** Low (working correctly)  
**Impact:** Minimal (consistency improvement)

---

#### Pattern 2: Pydantic Model Validators - Mixed ⚠️
**Files:** 3 core model files

**Current State:**
```python
# timeline.py - Has validators
@field_validator('end_date')
@classmethod
def validate_date_range(cls, v: datetime, info) -> datetime:
    if 'start_date' in info.data and v < info.data['start_date']:  # ⚠️ Timezone issue!
        raise ValueError("end_date must be after start_date")
    return v

# document.py - Has validators
# git_commit.py - Has validators
```

**Problem:** Direct datetime comparison without UTC enforcement  
**Status:** ⚠️ Needs UTC validators  
**Action:** Add `@field_validator` with `ensure_utc()`  
**Priority:** High (prevents future timezone bugs)

---

#### Pattern 3: Dashboard Date Inputs - Naive ⚠️
**Files:** Multiple dashboard views

**Current Usage:**
```python
# timeline_analysis.py
start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
end_date = st.date_input("End Date", value=datetime(2025, 12, 31))

# temporal_rag_query.py
as_of_date = st.date_input(
    "As Of Date",
    value=datetime.now() - timedelta(days=30)
)
```

**Problem:** Creates naive datetime objects  
**Status:** ⚠️ Needs UTC conversion before API calls  
**Action:** Convert to UTC-aware before sending to API  
**Priority:** Medium (API handles it, but better to be explicit)

---

#### Pattern 4: API Route Date Parsing - Mixed ⚠️
**Files:** Multiple API route files

**Current Usage:**
```python
# Some routes get datetime from Pydantic (validated)
# Some routes parse strings manually
# Some routes accept datetime objects directly

# temporal_rag.py
request.start_date  # Pydantic datetime - timezone unknown
request.end_date    # Pydantic datetime - timezone unknown
```

**Problem:** No consistent UTC enforcement at API boundary  
**Status:** ⚠️ Needs UTC validators in request models  
**Action:** Add validators to all request models  
**Priority:** High (API boundary is critical)

---

#### Pattern 5: Repository Date Comparisons - Fixed ✅ (Partial)
**Files:** `timeline_repository.py`, others

**Current Status:**
```python
# Already fixed in some places
start_naive = ensure_utc_naive(start_date)
end_naive = ensure_utc_naive(end_date)

# But not all repositories updated yet
```

**Status:** ✅ Pattern established, needs rollout  
**Action:** Apply to all repository date queries  
**Priority:** Medium (prevents timezone comparison errors)

---

#### Pattern 6: ChromaDB Metadata - Fixed ✅
**Files:** `job_processor.py`

**Current Status:**
```python
# Already using datetime_to_utc_timestamp()
chroma_metadata["git_date"] = datetime_to_utc_timestamp(commit_date)
```

**Status:** ✅ Working correctly  
**Action:** Verify all ChromaDB writes use helper  
**Priority:** Low (validation only)

---

### Summary of Findings

| Pattern | Status | Files Affected | Priority | Effort |
|---------|--------|----------------|----------|--------|
| `datetime.utcnow()` calls | ✅ Good | 86 | Low | 1 hr |
| Pydantic validators | ⚠️ Needs UTC | 3 core + 15 routes | High | 2 hrs |
| Dashboard date inputs | ⚠️ Naive | 5 views | Medium | 1 hr |
| API route parsing | ⚠️ Mixed | 15 routes | High | 2 hrs |
| Repository queries | ⚠️ Partial | 10 repos | Medium | 1.5 hrs |
| ChromaDB writes | ✅ Fixed | 2 files | Low | 0.5 hr |
| **Total** | - | **~136 files** | - | **8 hrs** |

---

## 🎯 Enriched Implementation Plan

### Phase 0: Foundation (Already Complete) ✅

**Deliverables:**
- [x] Core UTC utilities (`src/utils/datetime_utils.py`)
- [x] Critical bug fixes (period comparison)
- [x] Documentation (56 pages)

**Time:** 3 hours (completed)

---

### Phase 1: Pydantic Model Validators (High Priority) 🔴

**Objective:** Add UTC validators to all Pydantic models with datetime fields

**Target Files:**
1. `src/models/timeline.py` (Timeline, TimelineCreate, TimePeriod, TimePeriodCreate)
2. `src/models/document.py` (Document, DocumentCreate)
3. `src/models/git_commit.py` (GitCommit, GitCommitCreate)
4. API route request models (15 files)

**Implementation Pattern:**
```python
from pydantic import field_validator
from ..utils.datetime_utils import ensure_utc

class Timeline(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_utc_dates(cls, v):
        """Ensure dates are UTC-aware."""
        if isinstance(v, str):
            from ..utils.datetime_utils import parse_datetime_flexible
            return parse_datetime_flexible(v)
        return ensure_utc(v)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Ensure end_date is after start_date (with UTC-safe comparison)."""
        if 'start_date' in info.data:
            from ..utils.datetime_utils import safe_datetime_comparison
            if not safe_datetime_comparison(info.data['start_date'], v, "<"):
                raise ValueError("end_date must be after start_date")
        return v
```

**Files to Update:**

**Core Models (3 files):**
- [ ] `src/models/timeline.py` (6 datetime fields)
- [ ] `src/models/document.py` (4 datetime fields)
- [ ] `src/models/git_commit.py` (2 datetime fields)

**API Request Models (15 files):**
- [ ] `src/api/routes/temporal_rag.py` (PointInTimeRequest, ComparisonRequest)
- [ ] `src/api/routes/timeline.py` (TimelineCreateRequest)
- [ ] `src/api/routes/admin.py` (IngestionRequest, QueryRequest)
- [ ] `src/api/routes/temporal_versioning.py` (AsOfQueryRequest, TimelineQueryRequest)
- [ ] `src/api/routes/maintenance.py` (CompareVersionsRequest)
- [ ] `src/api/routes/documentation.py` (DocRunRequest)
- [ ] `src/api/routes/multi_pass.py` (MultiPassRequest)
- [ ] `src/api/routes/discovery.py` (DiscoveryRequest)
- [ ] `src/api/routes/orchestration.py` (OrchestrationRequest)
- [ ] `src/api/routes/reports.py` (ReportRequest)
- [ ] `src/api/routes/consolidation.py` (ConsolidationRequest)
- [ ] `src/api/routes/dynamic_rag.py` (DynamicRAGRequest)
- [ ] Additional route files as needed

**Testing:**
```python
# Test naive datetime handling
def test_timeline_naive_datetime():
    timeline = Timeline(
        name="Test",
        start_date=datetime(2025, 1, 1),  # Naive
        end_date=datetime(2025, 12, 31),  # Naive
        ...
    )
    assert timeline.start_date.tzinfo == timezone.utc
    assert timeline.end_date.tzinfo == timezone.utc

# Test aware datetime handling
def test_timeline_aware_datetime():
    est = pytz.timezone('America/New_York')
    timeline = Timeline(
        name="Test",
        start_date=est.localize(datetime(2025, 1, 1)),  # EST
        end_date=est.localize(datetime(2025, 12, 31)),  # EST
        ...
    )
    assert timeline.start_date.tzinfo == timezone.utc
    assert timeline.end_date.tzinfo == timezone.utc
    # Verify conversion happened
    assert timeline.start_date.hour != 0  # Shifted from EST to UTC
```

**Acceptance Criteria:**
- [ ] All datetime fields have UTC validators
- [ ] Validators handle naive datetimes (assume UTC with warning)
- [ ] Validators handle non-UTC datetimes (convert to UTC)
- [ ] Date range comparisons use safe_datetime_comparison()
- [ ] Tests pass with naive, aware, and non-UTC inputs
- [ ] No breaking changes to API contracts

**Estimated Time:** 2 hours  
**Priority:** 🔴 High  
**Risk:** Low (backward compatible)

---

### Phase 2: Repository Layer Updates (Medium Priority) 🟡

**Objective:** Ensure all repository date queries use UTC-safe comparisons

**Target Files (10 files):**
- [ ] `src/storage/repositories/timeline_repository.py` ✅ (already done)
- [ ] `src/storage/repositories/document_repository.py`
- [ ] `src/storage/repositories/git_commit_repository.py`
- [ ] `src/storage/repositories/ingestion_job_repository.py`
- [ ] `src/storage/repositories/embedding_repository.py`
- [ ] `src/services/timeline/timeline_manager.py`
- [ ] `src/services/timeline/document_placer.py`
- [ ] `src/services/timeline/gap_analyzer.py`
- [ ] `src/services/timeline/drift_detector.py`
- [ ] `src/services/maintenance/consistency_checker.py`

**Implementation Pattern:**
```python
from ...utils.datetime_utils import ensure_utc_naive

async def get_by_date_range(
    self,
    start_date: datetime,
    end_date: datetime
) -> List[Model]:
    """Get records in date range (UTC-safe)."""
    # Convert to naive UTC for PostgreSQL comparison
    start_naive = ensure_utc_naive(start_date)
    end_naive = ensure_utc_naive(end_date)
    
    result = await self.session.execute(
        select(self.model_class)
        .where(
            and_(
                self.model_class.date >= start_naive,
                self.model_class.date <= end_naive
            )
        )
    )
    return list(result.scalars().all())
```

**Acceptance Criteria:**
- [ ] All date range queries use ensure_utc_naive()
- [ ] All date comparisons in WHERE clauses normalized
- [ ] Tests verify UTC handling
- [ ] No timezone comparison errors in logs

**Estimated Time:** 1.5 hours  
**Priority:** 🟡 Medium  
**Risk:** Low (defensive improvement)

---

### Phase 3: Dashboard Date Handling (Medium Priority) 🟡

**Objective:** Ensure dashboard converts user inputs to UTC before API calls

**Target Files (5 files):**
- [ ] `dashboard_views/timeline_analysis.py`
- [ ] `dashboard_views/temporal_rag_query.py`
- [ ] `dashboard_views/timeline_viewer.py`
- [ ] `dashboard_views/documentation_browser.py`
- [ ] `dashboard_views/config_viewer.py`

**Implementation Pattern:**
```python
import streamlit as st
from datetime import datetime, time, timezone

def convert_date_input_to_utc(date_value):
    """Convert Streamlit date_input to UTC-aware datetime."""
    # Streamlit date_input returns date object
    # Combine with midnight time and make UTC-aware
    dt = datetime.combine(date_value, time.min)
    return dt.replace(tzinfo=timezone.utc)

# Usage in dashboard
start_date = st.date_input("Start Date")
start_datetime_utc = convert_date_input_to_utc(start_date)

# Send to API
response = requests.post(
    f"{api_base_url}/api/v1/timeline/create",
    json={
        "name": name,
        "start_date": start_datetime_utc.isoformat(),  # Includes +00:00
        "end_date": end_datetime_utc.isoformat()
    }
)
```

**Acceptance Criteria:**
- [ ] All date inputs converted to UTC before API calls
- [ ] ISO format includes timezone indicator (+00:00 or Z)
- [ ] User sees dates in local timezone (optional enhancement)
- [ ] API receives UTC-aware datetimes

**Estimated Time:** 1 hour  
**Priority:** 🟡 Medium  
**Risk:** Low (API already handles it)

---

### Phase 4: Consistency Improvements (Low Priority) 🟢

**Objective:** Replace `datetime.utcnow()` with `now_utc_naive()` for consistency

**Target Files:** 86 files

**Implementation Pattern:**
```python
# Before
from datetime import datetime
created_at = datetime.utcnow()

# After
from ..utils.datetime_utils import now_utc_naive
created_at = now_utc_naive()
```

**Strategy:**
- Find and replace: `datetime.utcnow()` → `now_utc_naive()`
- Add import: `from ..utils.datetime_utils import now_utc_naive`
- Verify tests still pass

**Acceptance Criteria:**
- [ ] All `datetime.utcnow()` replaced
- [ ] Imports updated
- [ ] Tests pass
- [ ] No functional changes

**Estimated Time:** 1 hour (automated)  
**Priority:** 🟢 Low  
**Risk:** Very Low (cosmetic improvement)

---

### Phase 5: Validation & Testing (Medium Priority) 🟡

**Objective:** Comprehensive timezone testing and validation

**Test Suite:**

**1. Unit Tests for UTC Utilities:**
```python
# tests/utils/test_datetime_utils.py
def test_ensure_utc_naive_datetime():
    """Naive datetimes assumed UTC."""
    naive = datetime(2025, 10, 26, 12, 0, 0)
    result = ensure_utc(naive)
    assert result.tzinfo == timezone.utc
    assert result.hour == 12  # Not converted

def test_ensure_utc_non_utc_datetime():
    """Non-UTC datetimes converted."""
    import pytz
    est = pytz.timezone('America/New_York')
    est_dt = est.localize(datetime(2025, 10, 26, 12, 0, 0))
    result = ensure_utc(est_dt)
    assert result.tzinfo == timezone.utc
    assert result.hour == 17  # EST→UTC (+5 in Oct)

def test_safe_datetime_comparison():
    """Safe comparison with mixed timezones."""
    naive = datetime(2025, 10, 26)
    aware = datetime(2025, 10, 27, tzinfo=timezone.utc)
    assert safe_datetime_comparison(naive, aware, "<")
```

**2. Integration Tests for Pydantic Models:**
```python
# tests/models/test_timeline_validators.py
def test_timeline_create_with_naive_datetimes():
    """Timeline accepts naive datetimes."""
    timeline = TimelineCreate(
        name="Test",
        service_name="test",
        repo_path="/test",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31)
    )
    assert timeline.start_date.tzinfo == timezone.utc
    assert timeline.end_date.tzinfo == timezone.utc

def test_timeline_create_with_timezone_datetimes():
    """Timeline converts non-UTC to UTC."""
    import pytz
    est = pytz.timezone('America/New_York')
    timeline = TimelineCreate(
        name="Test",
        service_name="test",
        repo_path="/test",
        start_date=est.localize(datetime(2025, 1, 1, 0, 0, 0)),
        end_date=est.localize(datetime(2025, 12, 31, 23, 59, 59))
    )
    assert timeline.start_date.tzinfo == timezone.utc
    # Verify conversion (EST is UTC-5)
    assert timeline.start_date.hour == 5
```

**3. End-to-End API Tests:**
```python
# tests/api/test_temporal_rag_timezone.py
def test_temporal_comparison_with_naive_dates():
    """API accepts naive dates without errors."""
    response = client.post(
        "/api/v1/rag/temporal/comparison",
        json={
            "question": "test",
            "start_date": "2025-09-01T00:00:00",  # No timezone
            "end_date": "2025-10-01T00:00:00",
            "service_name": "ecosystem-mcp"
        }
    )
    assert response.status_code == 200  # No timezone error

def test_temporal_comparison_with_timezone_dates():
    """API handles timezone dates correctly."""
    response = client.post(
        "/api/v1/rag/temporal/comparison",
        json={
            "question": "test",
            "start_date": "2025-09-01T00:00:00-05:00",  # EST
            "end_date": "2025-10-01T00:00:00-05:00",
            "service_name": "ecosystem-mcp"
        }
    )
    assert response.status_code == 200
```

**4. Timezone Edge Case Tests:**
```python
# tests/utils/test_timezone_edge_cases.py
def test_daylight_saving_transition():
    """Handle DST transitions correctly."""
    import pytz
    est = pytz.timezone('America/New_York')
    # Before DST ends (EDT, UTC-4)
    before = est.localize(datetime(2025, 10, 26, 1, 30, 0))
    # After DST ends (EST, UTC-5)
    after = est.localize(datetime(2025, 11, 10, 1, 30, 0))
    
    before_utc = ensure_utc(before)
    after_utc = ensure_utc(after)
    
    # Different UTC times despite same local time
    assert before_utc.hour != after_utc.hour

def test_leap_second_handling():
    """Handle leap seconds gracefully."""
    # Test datetime near leap second
    dt = datetime(2016, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    result = ensure_utc(dt)
    assert result.tzinfo == timezone.utc
```

**Acceptance Criteria:**
- [ ] Unit test coverage > 90% for datetime utils
- [ ] Integration tests for all models
- [ ] End-to-end API tests for temporal operations
- [ ] Edge case tests (DST, leap seconds, boundaries)
- [ ] All tests passing

**Estimated Time:** 2 hours  
**Priority:** 🟡 Medium  
**Risk:** None (tests only)

---

### Phase 6: Documentation & Monitoring (Low Priority) 🟢

**Objective:** Complete documentation and add monitoring

**1. Developer Documentation:**
```markdown
# UTC Standards (docs/UTC_STANDARDS.md)

## Core Principles
1. Store ALL datetimes in UTC (naive in PostgreSQL, timestamps in ChromaDB)
2. Convert at API boundaries (Pydantic validators)
3. Use utility functions (never manual conversions)
4. Log warnings for assumptions

## Usage Patterns

### Pydantic Models
```python
from ..utils.datetime_utils import ensure_utc

@field_validator('my_date', mode='before')
@classmethod
def ensure_utc_date(cls, v):
    return ensure_utc(v)
```

### Repository Queries
```python
from ...utils.datetime_utils import ensure_utc_naive

start_naive = ensure_utc_naive(start_date)
end_naive = ensure_utc_naive(end_date)
query = select(Model).where(Model.date.between(start_naive, end_naive))
```

### ChromaDB Metadata
```python
from ...utils.datetime_utils import datetime_to_utc_timestamp

metadata["git_date"] = datetime_to_utc_timestamp(commit_date)
```
```

**2. API Documentation Updates:**
- Update OpenAPI/Swagger specs with timezone expectations
- Add examples showing ISO 8601 with timezone
- Document that naive datetimes are assumed UTC

**3. Monitoring:**
```python
# Add to health check
async def check_timezone_consistency():
    """Verify timezone handling is working."""
    # Sample recent documents
    # Check for suspicious patterns
    # Alert if issues found
    pass
```

**Acceptance Criteria:**
- [ ] Developer guide created
- [ ] API docs updated
- [ ] Monitoring added to health checks
- [ ] Team trained on standards

**Estimated Time:** 1.5 hours  
**Priority:** 🟢 Low  
**Risk:** None (documentation)

---

## 📊 Implementation Timeline

### Sprint 1: Critical Fixes (High Priority) - 4 hours
- Phase 1: Pydantic Model Validators (2 hrs)
- Phase 2: Repository Layer Updates (1.5 hrs)
- Initial Testing (0.5 hr)

### Sprint 2: Dashboard & Testing (Medium Priority) - 3.5 hours
- Phase 3: Dashboard Date Handling (1 hr)
- Phase 5: Validation & Testing (2 hrs)
- Bug fixes from testing (0.5 hr)

### Sprint 3: Polish & Documentation (Low Priority) - 2.5 hours
- Phase 4: Consistency Improvements (1 hr)
- Phase 6: Documentation & Monitoring (1.5 hrs)

**Total Time:** 10 hours (across 3 sprints)

---

## 🎯 Success Metrics

### Phase Completion
- [ ] Sprint 1: Critical timezone bugs prevented
- [ ] Sprint 2: Dashboard handles timezones correctly
- [ ] Sprint 3: Complete UTC standardization

### Quality Metrics
- [ ] Zero timezone comparison errors in logs
- [ ] Test coverage > 90% for datetime code
- [ ] All API endpoints accept naive and aware datetimes
- [ ] Dashboard sends UTC-aware datetimes

### Documentation
- [ ] Developer guide complete
- [ ] API docs updated
- [ ] Team trained
- [ ] Monitoring in place

---

## 🚀 Execution Strategy

### Sprint 1 (This Session)
1. ✅ Start Phase 1: Core model validators
2. ✅ Test with existing temporal RAG tests
3. ✅ Deploy and validate

### Sprint 2 (Next Session)
1. Complete Phase 1: All API request models
2. Phase 2: Repository updates
3. Phase 3: Dashboard updates
4. Phase 5: Comprehensive testing

### Sprint 3 (Final Session)
1. Phase 4: Consistency improvements
2. Phase 6: Documentation
3. Final validation
4. Production deployment

---

**Ready to begin Sprint 1?** Let's start with Phase 1: Pydantic Model Validators

