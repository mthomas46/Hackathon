**Date:** October 24, 2025  
**Status:** Frontend Complete - Backend Work Required  
**Coverage:** Discovery, Orchestration, Reports, Temporal RAG, Doc Maintenance  

# Backend Requirements - Iteration 3

## Executive Summary

This document outlines the backend implementation requirements identified during Iteration 3 of the dashboard enhancement project. The frontend has been fully implemented for Discovery & Orchestration and Report Generation features, but several backend endpoints require fixes or implementation.

---

## 🎯 Priority 1: Critical Issues (Immediate Attention)

### 1.1 PostgreSQL Temporal Function Missing
**Endpoint:** `/api/v1/versioning/as-of`  
**Status:** ❌ Fails with database error  
**Error:** `UndefinedFunctionError: function get_all_documents_as_of(unknown) does not exist`

**Impact:** HIGH - Temporal RAG "Query As Of" feature completely non-functional

**Requirements:**
- Implement PostgreSQL function `get_all_documents_as_of(timestamp)`
- Function should return document versions as they existed at a specific point in time
- Must handle timezone conversions properly
- Should include proper indexing for performance

**Estimated Effort:** 2-3 hours

**Implementation Notes:**
```sql
CREATE OR REPLACE FUNCTION get_all_documents_as_of(query_time TIMESTAMP WITH TIME ZONE)
RETURNS TABLE (
    document_id UUID,
    content TEXT,
    metadata JSONB,
    version_id UUID,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_to TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id AS document_id,
        dv.content,
        dv.metadata,
        dv.id AS version_id,
        dv.valid_from,
        dv.valid_to
    FROM documents d
    INNER JOIN document_versions dv ON d.id = dv.document_id
    WHERE dv.valid_from <= query_time
      AND (dv.valid_to IS NULL OR dv.valid_to > query_time);
END;
$$ LANGUAGE plpgsql;
```

---

### 1.2 Orchestration Metrics Asyncio Error
**Endpoint:** `/api/v1/orchestration/metrics`  
**Status:** ⚠️ 500 Internal Server Error  
**Error:** `Failed to get metrics: asyncio.run() cannot be called from a running event loop`

**Impact:** MEDIUM - Metrics dashboard shows error but doesn't break functionality

**Requirements:**
- Fix asyncio.run() call in orchestration metrics endpoint
- Should use `await` instead of `asyncio.run()` within async context
- Ensure proper async/await pattern throughout orchestration service

**Estimated Effort:** 30 minutes

**Implementation Notes:**
```python
# BAD - within async endpoint:
result = asyncio.run(get_metrics())

# GOOD - within async endpoint:
result = await get_metrics()
```

---

### 1.3 Temporal Timeline Endpoint Method Mismatch
**Endpoint:** `/api/v1/versioning/timeline`  
**Status:** ⚠️ Returns "Method Not Allowed" or 404  
**Error:** Endpoint expects different HTTP method or query parameters

**Impact:** MEDIUM - Timeline visualization feature non-functional

**Requirements:**
- Verify correct HTTP method (GET vs POST)
- Document expected query parameters
- Implement if endpoint is missing
- Should return document change timeline with timestamps

**Estimated Effort:** 30 minutes

---

## 📊 Priority 2: Documentation Maintenance Endpoints (8-12 hours)

All documentation maintenance features have complete frontend implementations but require backend API endpoints.

### 2.1 Staleness Detection API
**Endpoint:** `/api/v1/maintenance/staleness/detect`  
**Status:** ❌ Not Implemented  

**Requirements:**
- Analyze documentation last modified dates
- Compare with referenced code/APIs
- Flag docs older than configured threshold
- Return staleness score (0-100) per document
- Support batch processing for large doc sets

**Parameters:**
```json
{
  "threshold_days": 90,
  "check_code_references": true,
  "include_metadata": true
}
```

**Response:**
```json
{
  "stale_documents": [
    {
      "document_id": "uuid",
      "title": "Getting Started",
      "last_modified": "2024-01-15",
      "staleness_score": 85,
      "days_old": 283,
      "reasons": ["Referenced API endpoints changed", "Code examples outdated"]
    }
  ],
  "summary": {
    "total_checked": 150,
    "stale_count": 23,
    "average_staleness": 42.3
  }
}
```

**Estimated Effort:** 3-4 hours

---

### 2.2 Coverage Analysis API
**Endpoint:** `/api/v1/maintenance/coverage/analyze`  
**Status:** ❌ Not Implemented

**Requirements:**
- Analyze codebase to find undocumented features
- Cross-reference code with documentation
- Generate coverage percentage
- Identify documentation gaps

**Parameters:**
```json
{
  "repo_path": "/path/to/repo",
  "include_private": false,
  "analysis_depth": "function"
}
```

**Response:**
```json
{
  "coverage": {
    "overall": 67.5,
    "by_category": {
      "api_endpoints": 85.2,
      "functions": 45.3,
      "classes": 72.1
    }
  },
  "undocumented": [
    {
      "type": "function",
      "name": "process_temporal_query",
      "file": "api/versioning.py",
      "line": 145
    }
  ],
  "suggestions": [
    "Document process_temporal_query function",
    "Add examples for versioning API"
  ]
}
```

**Estimated Effort:** 4-5 hours

---

### 2.3 Consistency Checking API
**Endpoint:** `/api/v1/maintenance/consistency/check`  
**Status:** ❌ Not Implemented

**Requirements:**
- Check for conflicting information across docs
- Verify cross-references are valid
- Check terminology consistency
- Validate code examples compile/run

**Parameters:**
```json
{
  "check_cross_references": true,
  "validate_code_examples": true,
  "check_terminology": true
}
```

**Response:**
```json
{
  "inconsistencies": [
    {
      "type": "conflicting_information",
      "documents": ["doc1_id", "doc2_id"],
      "description": "API endpoint path differs between docs",
      "severity": "high"
    }
  ],
  "broken_links": 5,
  "invalid_code_examples": 3,
  "terminology_issues": 12
}
```

**Estimated Effort:** 4-5 hours

---

### 2.4 Quality Scoring API
**Endpoint:** `/api/v1/maintenance/quality/score`  
**Status:** ❌ Not Implemented

**Requirements:**
- Calculate documentation quality scores
- Check readability metrics
- Verify completeness
- Assess structure and organization

**Estimated Effort:** 2-3 hours

---

### 2.5 Dependency Tracking API
**Endpoint:** `/api/v1/maintenance/dependencies/track`  
**Status:** ❌ Not Implemented

**Requirements:**
- Track documentation dependencies on code
- Monitor for breaking changes
- Alert when referenced code changes

**Estimated Effort:** 3-4 hours

---

## 🎯 Priority 3: Discovery & Orchestration Enhancements (6-8 hours)

Most endpoints exist but return empty data or have limited functionality.

### 3.1 Discovery Scan Enhancement
**Endpoint:** `/api/v1/discovery/scan`  
**Status:** ✅ Working (validates input)  
**Enhancement Needed:** Full implementation with actual file scanning

**Current:** Validates repo_path exists  
**Needed:** 
- Actually scan repository directories
- Detect file types and services
- Generate processing plans
- Return comprehensive scan results

**Estimated Effort:** 3-4 hours

---

### 3.2 Processing Plan Management
**Endpoint:** `/api/v1/discovery/plans`  
**Status:** ⚠️ Returns empty array  
**Enhancement Needed:** Store and retrieve plans

**Requirements:**
- Persist plans to database
- Support CRUD operations
- Link to scan results
- Track plan execution history

**Estimated Effort:** 2-3 hours

---

### 3.3 Orchestration Monitoring
**Endpoints:** 
- `/api/v1/orchestration/status/{plan_id}` ✅ Exists
- `/api/v1/orchestration/progress/{plan_id}` ✅ Exists
- `/api/v1/orchestration/monitor/{plan_id}` ✅ Exists

**Status:** Likely working but no test data  
**Enhancement Needed:** Implement worker monitoring, resource tracking

**Estimated Effort:** 2-3 hours

---

## 📊 Priority 4: Report Generation Backend (4-6 hours)

### 4.1 Analysis Report Generator
**Endpoint:** `/api/v1/analysis/reports/{plan_id}`  
**Status:** ❌ Returns empty or minimal data

**Requirements:**
- Generate comprehensive analysis reports
- Support multiple export formats (Markdown, HTML, JSON, PDF)
- Include metrics, charts data, recommendations
- Support customizable report sections

**Estimated Effort:** 3-4 hours

---

### 4.2 Architecture Analysis
**Endpoint:** `/api/v1/analysis/architecture/{plan_id}`  
**Status:** ❌ Needs implementation

**Requirements:**
- Analyze system architecture from code
- Identify layers and components
- Detect design patterns
- Generate architecture diagrams (data for visualization)

**Estimated Effort:** 4-5 hours

---

### 4.3 Service & Stack Analysis
**Endpoints:**
- `/api/v1/analysis/services/{plan_id}` ⚠️ Limited
- `/api/v1/analysis/stack/{plan_id}` ⚠️ Limited

**Requirements:**
- Deep service analysis (dependencies, size, type)
- Technology stack detection
- Version identification
- Dependency graph generation

**Estimated Effort:** 2-3 hours

---

## 📈 Implementation Roadmap

### Week 1: Critical Fixes
- [ ] Fix PostgreSQL temporal function (Priority 1.1)
- [ ] Fix orchestration metrics asyncio error (Priority 1.2)
- [ ] Fix temporal timeline endpoint (Priority 1.3)
- **Estimated:** 3-4 hours
- **Impact:** HIGH - Enables temporal features

### Week 2: Documentation Maintenance
- [ ] Implement staleness detection API (Priority 2.1)
- [ ] Implement coverage analysis API (Priority 2.2)
- [ ] Implement consistency checking API (Priority 2.3)
- **Estimated:** 11-14 hours
- **Impact:** MEDIUM - New functionality, high value

### Week 3: Discovery & Orchestration
- [ ] Enhance discovery scan (Priority 3.1)
- [ ] Implement plan management (Priority 3.2)
- [ ] Enhance orchestration monitoring (Priority 3.3)
- **Estimated:** 7-10 hours
- **Impact:** HIGH - Core workflow functionality

### Week 4: Report Generation
- [ ] Implement report generators (Priority 4.1)
- [ ] Implement architecture analysis (Priority 4.2)
- [ ] Implement service/stack analysis (Priority 4.3)
- **Estimated:** 9-12 hours
- **Impact:** MEDIUM - Analytics and insights

---

## 🔍 Testing Requirements

Once backend implementation is complete, the following tests should be added:

### Unit Tests
- [ ] Test temporal PostgreSQL functions
- [ ] Test staleness detection logic
- [ ] Test coverage analysis algorithm
- [ ] Test consistency checking

### Integration Tests
- [ ] Test discovery scan end-to-end
- [ ] Test orchestration workflow
- [ ] Test report generation
- [ ] Test temporal RAG queries

### E2E Tests
- [ ] Full discovery → orchestration → report workflow
- [ ] Temporal query scenarios
- [ ] Documentation maintenance workflows

---

## 📊 API Endpoint Status Summary

| Category | Endpoint | Status | Priority |
|----------|----------|--------|----------|
| **Temporal RAG** |
| | `/api/v1/versioning/as-of` | ❌ PostgreSQL Error | P1 |
| | `/api/v1/versioning/timeline` | ⚠️ Method Issue | P1 |
| | `/api/v1/versioning/changes` | ✅ Working | - |
| | `/api/v1/versioning/activity-summary` | ✅ Working | - |
| **Doc Maintenance** |
| | `/api/v1/maintenance/staleness/*` | ❌ Not Implemented | P2 |
| | `/api/v1/maintenance/coverage/*` | ❌ Not Implemented | P2 |
| | `/api/v1/maintenance/consistency/*` | ❌ Not Implemented | P2 |
| | `/api/v1/maintenance/quality/*` | ❌ Not Implemented | P2 |
| | `/api/v1/maintenance/dependencies/*` | ❌ Not Implemented | P2 |
| **Discovery** |
| | `/api/v1/discovery/scan` | ⚠️ Partial | P3 |
| | `/api/v1/discovery/plans` | ⚠️ Empty Data | P3 |
| | `/api/v1/discovery/plans/{id}` | ⚠️ Empty Data | P3 |
| **Orchestration** |
| | `/api/v1/orchestration/execute/{id}` | ✅ Exists | P3 |
| | `/api/v1/orchestration/status/{id}` | ✅ Exists | P3 |
| | `/api/v1/orchestration/progress/{id}` | ✅ Exists | P3 |
| | `/api/v1/orchestration/monitor/{id}` | ✅ Exists | P3 |
| | `/api/v1/orchestration/metrics` | ⚠️ Asyncio Error | P1 |
| | `/api/v1/orchestration/alerts` | ✅ Working | - |
| **Reports** |
| | `/api/v1/analysis/reports/{id}` | ⚠️ Limited | P4 |
| | `/api/v1/analysis/architecture/{id}` | ⚠️ Limited | P4 |
| | `/api/v1/analysis/services/{id}` | ⚠️ Limited | P4 |
| | `/api/v1/analysis/stack/{id}` | ⚠️ Limited | P4 |
| | `/api/v1/analysis/contexts` | ⚠️ Empty Data | P4 |

**Legend:**
- ✅ Working: Fully functional
- ⚠️ Partial: Endpoint exists but limited/buggy
- ❌ Not Implemented: Missing entirely

---

## 💡 Recommendations

1. **Immediate Action:** Fix Priority 1 issues to enable temporal features (3-4 hours)

2. **High Value:** Implement Documentation Maintenance APIs (Priority 2) - these are unique features that add significant value

3. **Core Workflow:** Complete Discovery & Orchestration (Priority 3) for end-to-end functionality

4. **Analytics:** Implement Report Generation (Priority 4) for insights and analysis

5. **Testing:** Add comprehensive tests for all new functionality

6. **Documentation:** Update API documentation with all new endpoints and examples

---

## 📚 Resources

- Frontend Implementation: Complete ✅
  - `dashboard_views/temporal_rag_query.py`
  - `dashboard_views/doc_maintenance.py`
  - `dashboard_views/discovery_orchestration.py`
  - `dashboard_views/reports_generator.py`

- API Tracker: `utils/api_tracker.py` (helps debug backend issues)

- Feature List: `ECOSYSTEM_MCP_MASTER_FEATURE_LIST.md`

---

## 📞 Contact & Next Steps

**Frontend Status:** ✅ COMPLETE  
**Backend Status:** 🚧 IN PROGRESS  
**Estimated Total Backend Work:** 30-42 hours

**Next Steps:**
1. Review and prioritize backend work
2. Assign to backend team
3. Set up CI/CD for new endpoints
4. Schedule QA testing once implemented
5. Update documentation

---

*Generated: October 24, 2025*  
*Dashboard Version: 1.0.0*  
*Iteration: 3*

