# Phase 2: Split main.py into Route Modules

**Goal**: Reduce main.py from 4,326 lines to ~100-200 lines  
**Approach**: Extract endpoint groups into logical router modules  
**Estimated Time**: 8-12 hours  
**Status**: 🔄 IN PROGRESS

---

## Current State

- **Total Lines**: 4,326
- **Total Endpoints**: 62
- **Structure**: Monolithic single file
- **Maintainability**: ❌ Very Low

---

## Target State

- **main.py Lines**: ~100-200
- **Route Modules**: 10 focused modules
- **Structure**: Clean separation of concerns
- **Maintainability**: ✅ High

---

## Route Module Structure

### 1. **presentation/routes/status_routes.py** (3 endpoints)
- `GET /` - Root endpoint
- `GET /api/analysis/status` - Service status
- `POST /api/analysis/analyze` - Basic analysis
- `GET /health` - Health check

### 2. **presentation/routes/analysis_routes.py** (19 endpoints)
- `POST /analyze` - Main analysis endpoint
- `POST /analyze/semantic-similarity`
- `POST /analyze/sentiment`
- `POST /analyze/tone`
- `POST /analyze/quality`
- `POST /analyze/trends` + portfolio variant
- `POST /analyze/risk` + portfolio variant
- `POST /analyze/maintenance/forecast` + portfolio variant
- `POST /analyze/quality/degradation` + portfolio variant
- `POST /analyze/change/impact` + portfolio variant
- `POST /analyze/generate-report`
- `POST /analyze/pull-request`
- `POST /analyze/test-pr-analysis`

### 3. **presentation/routes/remediation_routes.py** (2 endpoints)
- `POST /remediate`
- `POST /remediate/preview`

### 4. **presentation/routes/workflow_routes.py** (4 endpoints)
- `POST /workflows/events`
- `GET /workflows/{workflow_id}`
- `GET /workflows/queue/status`
- `POST /workflows/webhook/config`

### 5. **presentation/routes/repository_routes.py** (5 endpoints)
- `POST /repositories/analyze`
- `POST /repositories/connectivity`
- `POST /repositories/connectors/config`
- `GET /repositories/connectors`
- `GET /repositories/frameworks`

### 6. **presentation/routes/distributed_routes.py** (12 endpoints)
- `POST /distributed/tasks`
- `POST /distributed/tasks/batch`
- `GET /distributed/tasks/{task_id}`
- `DELETE /distributed/tasks/{task_id}`
- `GET /distributed/workers`
- `GET /distributed/stats`
- `POST /distributed/workers/scale`
- `POST /distributed/start`
- `PUT /distributed/load-balancing/strategy`
- `GET /distributed/queue/status`
- `PUT /distributed/load-balancing/config`
- `GET /distributed/load-balancing/config`

### 7. **presentation/routes/report_routes.py** (5 endpoints)
- `POST /reports/generate`
- `POST /reports/document-dump`
- `GET /reports/confluence/consolidation`
- `GET /reports/jira/staleness`
- `POST /reports/findings/notify-owners`

### 8. **presentation/routes/findings_routes.py** (2 endpoints)
- `GET /findings`
- `GET /detectors`

### 9. **presentation/routes/integration_routes.py** (5 endpoints)
- `GET /integration/health`
- `POST /integration/analyze-with-prompt`
- `POST /integration/natural-language-analysis`
- `GET /integration/prompts/categories`
- `POST /integration/log-analysis`

### 10. **presentation/routes/pr_confidence_routes.py** (5 endpoints)
- `POST /architecture/analyze`
- `POST /pr-confidence/analyze`
- `GET /pr-confidence/history/{pr_id}`
- `GET /pr-confidence/statistics`
- `GET /api/v1/analysis/status`

---

## Implementation Plan

### Step 1: Create Route Module Template ✅
- Create directory structure
- Set up APIRouter instances
- Define shared imports

### Step 2: Extract Status Routes (EASIEST) ✅
- Move root & status endpoints
- Test basic routing
- Validate approach

### Step 3: Extract Remaining Routes (BULK)
- Extract analysis routes (largest - 19 endpoints)
- Extract distributed routes (second largest - 12 endpoints)
- Extract report routes (5 endpoints)
- Extract integration routes (5 endpoints)
- Extract repository routes (5 endpoints)
- Extract PR confidence routes (5 endpoints)
- Extract workflow routes (4 endpoints)
- Extract remediation routes (2 endpoints)
- Extract findings routes (2 endpoints)

### Step 4: Update main.py
- Remove extracted endpoints
- Import and include all routers
- Keep only app initialization
- Add middleware setup
- Keep shared utilities

### Step 5: Validate
- Check all endpoints still accessible
- Run any working tests
- Verify no regressions

---

## Benefits

1. ✅ **Maintainability**: Each route module is focused and manageable
2. ✅ **Testability**: Easier to test individual route groups
3. ✅ **Readability**: Clear separation of concerns
4. ✅ **Scalability**: Easy to add new endpoints to appropriate modules
5. ✅ **Team Development**: Multiple developers can work on different modules

---

## Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Extract one module at a time
- Keep endpoint signatures identical
- Test after each extraction

### Risk 2: Import Issues
**Mitigation**:
- Use consistent import patterns
- Centralize shared utilities
- Document dependencies

### Risk 3: Router Registration Order
**Mitigation**:
- Maintain consistent router registration order
- Document any order dependencies
- Test all endpoints after integration

---

## Progress Tracker

- [x] Create plan
- [ ] Create route module template
- [ ] Extract status_routes.py
- [ ] Extract analysis_routes.py
- [ ] Extract distributed_routes.py
- [ ] Extract report_routes.py
- [ ] Extract integration_routes.py
- [ ] Extract repository_routes.py
- [ ] Extract pr_confidence_routes.py
- [ ] Extract workflow_routes.py
- [ ] Extract remediation_routes.py
- [ ] Extract findings_routes.py
- [ ] Update main.py
- [ ] Validate all endpoints
- [ ] Run tests
- [ ] Create PHASE_2_COMPLETE.md report

---

## Success Criteria

- ✅ main.py reduced to < 200 lines
- ✅ All 62 endpoints moved to appropriate route modules
- ✅ All imports working correctly
- ✅ Service starts without errors
- ✅ All endpoints still accessible

---

**Plan Created**: 2025-10-10  
**Estimated Completion**: 8-12 hours  
**Priority**: 🔴 CRITICAL  
**Impact**: ⭐⭐⭐⭐⭐ Very High (21x line reduction)

