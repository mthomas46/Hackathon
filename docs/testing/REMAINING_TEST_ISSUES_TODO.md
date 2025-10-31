**Date:** October 24, 2025  
**Status:** Remaining Test Issues - TODO List  
**Coverage:** Unit, Integration, E2E, Functional Tests  

---

# 📋 REMAINING TEST ISSUES - COMPREHENSIVE TODO LIST

## Overview

After achieving 90% overall pass rate, this document tracks the remaining 2.8% of test issues that need resolution. All issues are categorized, prioritized, and have estimated fix times.

**Total Remaining:** ~15 tests out of 538 (2.8%)

---

## 🔴 HIGH PRIORITY (Fix First)

### TODO 1: Fix Unit Test - Progress Tracker API Mismatch
**File:** `tests/unit/test_progress_tracker.py`  
**Tests Affected:** 3 tests  
**Status:** ❌ FAILED  
**Priority:** HIGH  
**Estimated Time:** 30 minutes  

**Issue:**
```
AttributeError: 'ProgressTracker' object has no attribute 'update_progress'. 
Did you mean: 'plan_progress'?
```

**Root Cause:**
- Test uses `update_progress()` method
- Actual API has `plan_progress()` method
- API has changed, tests not updated

**Failing Tests:**
1. `TestProgressTrackerBasic::test_update_progress`
2. `TestProgressCalculation::test_progress_percentage_calculation`
3. `TestProgressCalculation::test_progress_with_failures`

**Fix Strategy:**
1. Review `ProgressTracker` class API in `src/services/orchestration/progress_tracker.py`
2. Update test method calls from `update_progress()` to `plan_progress()`
3. Update test assertions to match new API response format
4. Verify all progress tracker tests pass

**Files to Modify:**
- `tests/unit/test_progress_tracker.py` (update method calls)

---

### TODO 2: Fix E2E Test - CircuitBreaker Import Error
**File:** `tests/e2e/test_full_system.py`  
**Tests Affected:** 2 tests  
**Status:** ❌ FAILED  
**Priority:** HIGH  
**Estimated Time:** 15 minutes  

**Issue:**
```
ImportError: cannot import name 'CircuitBreakerError' from 'src.utils.circuit_breaker'
AssertionError: Circuit breaker missing state
```

**Root Cause:**
- Exception class renamed from `CircuitBreakerError` to `CircuitBreakerOpenError`
- State attribute moved from `breaker.state` to `breaker.stats.state`
- Same issues we fixed in unit tests, but E2E tests not updated

**Failing Tests:**
1. `TestApplicationLifecycle::test_all_imports_resolve`
2. `TestCircuitBreakers::test_ollama_client_has_circuit_breaker`

**Fix Strategy:**
1. Update import: `from src.utils.circuit_breaker import CircuitBreakerOpenError`
2. Update state check: `breaker.stats.state` instead of `breaker.state`
3. Apply same fixes we used in unit tests

**Files to Modify:**
- `tests/e2e/test_full_system.py` (update imports and state access)

---

### TODO 3: Fix E2E Test - Timeline Workflow Errors
**File:** `tests/e2e/test_complete_workflow.py`  
**Tests Affected:** 3 tests  
**Status:** ❌ ERROR  
**Priority:** HIGH  
**Estimated Time:** 1 hour  

**Issue:**
- Timeline creation to query workflow fails
- Gap detection workflow fails
- Drift detection and refresh workflow fails

**Root Cause:**
- Need to investigate error details (currently showing as ERROR, not FAILED)
- Likely database/fixture setup issues
- May be related to temporal confidence auto-adjust changes

**Failing Tests:**
1. `TestCompleteWorkflow::test_timeline_creation_to_query_workflow`
2. `TestCompleteWorkflow::test_gap_detection_workflow`
3. `TestCompleteWorkflow::test_drift_detection_and_refresh_workflow`

**Fix Strategy:**
1. Run tests individually with full traceback to see actual errors
2. Check if database fixtures are properly set up
3. Verify timeline manager initialization
4. Update tests to match new temporal confidence behavior

**Files to Modify:**
- `tests/e2e/test_complete_workflow.py` (TBD based on error details)

---

## 🟡 MEDIUM PRIORITY

### TODO 4: Fix Functional Test - Documentation Run API Mismatch
**File:** `tests/functional/test_documentation_runs.py`  
**Tests Affected:** 5 tests  
**Status:** ❌ FAILED  
**Priority:** MEDIUM  
**Estimated Time:** 1 hour  

**Issue:**
```
AttributeError: 'DocumentationRunModel' object has no attribute 'repo_path'
AttributeError: 'DocumentationRunModel' object has no attribute 'snapshot_id'
AttributeError: 'DocumentationRunRepository' object has no attribute 'get_run'
AttributeError: 'DocumentationRunRepository' object has no attribute 'get_runs_by_repo'
```

**Root Cause:**
- Model attributes renamed: `repo_path` → `repo_id`
- Model attributes removed: `snapshot_id` no longer exists
- Repository methods renamed: `get_run()` → different method name
- Repository methods renamed: `get_runs_by_repo()` → different method name

**Failing Tests:**
1. `TestDocumentationRunCreation::test_create_documentation_run`
2. `TestDocumentationRunCreation::test_create_run_with_snapshot_id`
3. `TestDocumentationRunRetrieval::test_get_run_by_id`
4. `TestDocumentationRunRetrieval::test_get_runs_by_repo_path`
5. `TestDocumentationRunRetrieval::test_get_runs_by_status`

**Fix Strategy:**
1. Review `DocumentationRunModel` in `src/storage/models_documentation.py`
2. Review `DocumentationRunRepository` API
3. Update test to use `repo_id` instead of `repo_path`
4. Remove or update `snapshot_id` test
5. Update repository method calls to match current API
6. Ensure `repository_context` fixture is used (foreign key requirement)

**Files to Modify:**
- `tests/functional/test_documentation_runs.py` (update model attributes and method calls)

---

### TODO 5: Fix Integration Test - API Endpoint Fixture Issues
**File:** `tests/integration/test_api_endpoints.py`  
**Tests Affected:** 7 tests (5 skipped, 2 errors)  
**Status:** ⏭️ SKIPPED / ❌ ERROR  
**Priority:** MEDIUM  
**Estimated Time:** 2 hours  

**Issue:**
```
TypeError: Client.__init__() got an unexpected keyword argument 'app'
ERROR: test_logs_list_endpoint
ERROR: test_ollama_status_endpoint
```

**Root Cause:**
- TestClient fixture setup issue (already attempted fix, needs deeper investigation)
- Two additional tests have errors beyond fixture issue
- May need to use async_test_client instead of test_client

**Affected Tests:**
1. `test_health_endpoint` (SKIPPED)
2. `test_root_endpoint` (SKIPPED)
3. `test_openapi_docs` (SKIPPED)
4. `test_openapi_json` (SKIPPED)
5. `test_query_endpoint_structure` (SKIPPED)
6. `test_logs_list_endpoint` (ERROR)
7. `test_ollama_status_endpoint` (ERROR)

**Fix Strategy:**
1. Investigate TestClient vs AsyncClient usage
2. Check if these tests should use `async_test_client` fixture instead
3. Review Starlette/FastAPI version compatibility
4. Consider rewriting tests to use `httpx.AsyncClient` with `ASGITransport`
5. Get full error details for the 2 ERROR tests

**Files to Modify:**
- `tests/integration/test_api_endpoints.py` (rewrite to use async client)
- `tests/integration/conftest.py` (potentially adjust fixture)

---

### TODO 6: Fix Integration Test - Cache Analytics Response Format
**File:** `tests/integration/test_cache_analytics_routes.py`  
**Tests Affected:** 3 tests  
**Status:** ❌ FAILED  
**Priority:** MEDIUM  
**Estimated Time:** 30 minutes  

**Issue:**
```
AssertionError: assert ('hit_rate' in data or 'miss_rate' in data)
AssertionError: assert ('rate' in data or 'percentage' in data)
AssertionError: assert ('average_latency' in data or 'throughput' in data)
```

**Root Cause:**
- API response format has changed
- Tests expect top-level `hit_rate` field
- Actual response has nested structure: `data['caches']['document_cache']['overall']['hit_rate']`
- Tests expect endpoints that return 404 (Not Found)

**Failing Tests:**
1. `TestCacheAnalytics::test_get_cache_analytics`
2. `TestCacheAnalytics::test_get_cache_hit_rate`
3. `TestCacheAnalytics::test_get_cache_performance`

**Fix Strategy:**
1. Review actual API response structure from cache analytics endpoint
2. Update test assertions to match nested response format
3. Check if some endpoints no longer exist (404 responses)
4. Update test to navigate nested structure: `data['caches'][cache_name]['overall']['hit_rate']`

**Files to Modify:**
- `tests/integration/test_cache_analytics_routes.py` (update assertions)

---

## 🟢 LOW PRIORITY (Can Defer)

### TODO 7: Investigate Excluded Test Files
**Files:** 6 test files  
**Status:** 🚫 EXCLUDED  
**Priority:** LOW  
**Estimated Time:** 4-8 hours total  

**Excluded Files:**
1. `tests/unit/test_dependency_manager.py` - Import error (relative import)
2. `tests/unit/test_hierarchical_context.py` - Module not found
3. `tests/unit/test_cache_decorator.py` - Outdated API
4. `tests/unit/test_data_isolation.py` - Environment detection issues
5. `tests/unit/test_enhanced_model_router.py` - Code detection logic
6. `tests/unit/test_processing_planner.py` - Tests hang during execution

**Documentation:**
- See `EXCLUDED_TEST_FILES_DOCUMENTATION.md` for detailed analysis
- Each file has action plan and priority
- Can be addressed in separate sprint

**Fix Strategy:**
- Follow action plans in `EXCLUDED_TEST_FILES_DOCUMENTATION.md`
- Phase 1: Quick wins (1-2 hours)
- Phase 2: Medium effort (2-4 hours)
- Phase 3: Low priority (1-2 hours)

---

### TODO 8: Review Skipped Tests Across All Categories
**Tests:** 36 skipped tests  
**Status:** ⏭️ SKIPPED  
**Priority:** LOW  
**Estimated Time:** 2-4 hours  

**Categories:**
- Unit tests: Some skipped due to missing dependencies
- Integration tests: 5 skipped (documented in TODO 5)
- E2E tests: 6 skipped
- Functional tests: 25 skipped

**Fix Strategy:**
1. Review each skipped test to understand skip reason
2. Categorize skips:
   - Missing infrastructure (Redis, PostgreSQL, etc.)
   - Test design issues
   - Intentionally skipped (slow tests, etc.)
3. For infrastructure skips: Document requirements
4. For design issues: Fix or remove tests
5. For intentional skips: Ensure proper markers and documentation

**Files to Review:**
- All test files with `@pytest.mark.skip` decorators
- Check skip reasons and validate they're still relevant

---

## 📊 SUMMARY STATISTICS

### By Priority
| Priority | Tests | Estimated Time |
|----------|-------|----------------|
| HIGH | 8 tests | 2.75 hours |
| MEDIUM | 15 tests | 4 hours |
| LOW | 42 items | 6-12 hours |
| **Total** | **65 items** | **12.75-18.75 hours** |

### By Category
| Category | Failed | Errors | Skipped | Total |
|----------|--------|--------|---------|-------|
| Unit | 3 | 0 | 0 | 3 |
| Integration | 3 | 2 | 5 | 10 |
| E2E | 2 | 3 | 6 | 11 |
| Functional | 5 | 0 | 25 | 30 |
| Excluded | 0 | 0 | 6 | 6 |
| **Total** | **13** | **5** | **42** | **60** |

### By Type
| Type | Count | % of Total |
|------|-------|------------|
| API Mismatch | 8 | 50% |
| Import/Module Issues | 2 | 12.5% |
| Response Format | 3 | 18.75% |
| Fixture Issues | 7 | 43.75% |
| Unknown (Need Investigation) | 3 | 18.75% |

---

## 🎯 RECOMMENDED EXECUTION ORDER

### Sprint 1: Quick Wins (3-4 hours)
1. ✅ TODO 1: Fix progress tracker API mismatch (30 min)
2. ✅ TODO 2: Fix CircuitBreaker import in E2E (15 min)
3. ✅ TODO 6: Fix cache analytics response format (30 min)
4. ✅ TODO 4: Fix documentation run API mismatch (1 hour)

**Expected Result:** +11 tests passing (from 90% to 92%)

### Sprint 2: Medium Effort (3-4 hours)
5. ✅ TODO 3: Fix timeline workflow errors (1 hour)
6. ✅ TODO 5: Fix API endpoint fixture issues (2 hours)

**Expected Result:** +10 tests passing (from 92% to 94%)

### Sprint 3: Comprehensive Cleanup (6-12 hours)
7. ✅ TODO 7: Investigate excluded test files (4-8 hours)
8. ✅ TODO 8: Review all skipped tests (2-4 hours)

**Expected Result:** 95-100% pass rate

---

## 📈 PROGRESS TRACKING

### Current Status
- ✅ Overall Pass Rate: 90%
- ✅ Unit Tests: 98.8%
- ✅ Integration Tests: 83%
- ✅ E2E Tests: 86%
- ✅ Functional Tests: 79%

### Target Status (After Sprint 1)
- 🎯 Overall Pass Rate: 92%
- 🎯 Unit Tests: 99.3%
- 🎯 Integration Tests: 86%
- 🎯 E2E Tests: 86%
- 🎯 Functional Tests: 100%

### Ultimate Goal (After All Sprints)
- 🏆 Overall Pass Rate: 95-100%
- 🏆 All critical tests passing
- 🏆 All skips documented and justified
- 🏆 Zero excluded files

---

## 💡 KEY INSIGHTS

### Common Patterns
1. **API Evolution:** Many failures due to renamed methods/attributes
2. **Import Changes:** CircuitBreaker API changes affect multiple test files
3. **Response Format:** API responses have nested structures, tests expect flat
4. **Fixture Issues:** TestClient setup needs investigation

### Prevention Strategies
1. **API Versioning:** Consider versioning APIs to avoid breaking tests
2. **Deprecation Warnings:** Add warnings before removing/renaming methods
3. **Test Maintenance:** Regular test runs to catch API changes early
4. **Documentation:** Keep test documentation in sync with code changes

---

## 🚀 NEXT STEPS

### Immediate (Today)
1. Start with TODO 1 (progress tracker) - Quick win
2. Move to TODO 2 (CircuitBreaker) - Another quick win
3. Tackle TODO 6 (cache analytics) - Easy fix

### This Week
4. Complete TODO 4 (documentation runs)
5. Investigate TODO 3 (timeline workflows)
6. Start TODO 5 (API endpoint fixtures)

### Next Week
7. Address excluded files (TODO 7)
8. Review all skipped tests (TODO 8)
9. Final validation and documentation

---

## ✅ SUCCESS CRITERIA

### Definition of Done
- [ ] All HIGH priority TODOs completed
- [ ] At least 95% overall pass rate achieved
- [ ] All failures have documented root causes
- [ ] All skips have justified reasons
- [ ] Excluded files have action plans
- [ ] Test suite runs in <5 minutes
- [ ] No hanging or blocking tests
- [ ] All fixes committed to git with clear messages

### Quality Gates
- [ ] No test failures in critical paths
- [ ] All API mismatch issues resolved
- [ ] All import/module issues resolved
- [ ] Fixture issues investigated and documented
- [ ] Response format issues fixed

---

## 📝 NOTES

### Lessons Learned
1. API changes need coordinated test updates
2. CircuitBreaker refactor affected multiple test files
3. Model attribute renames need comprehensive search/replace
4. TestClient fixture needs version-specific handling

### Future Improvements
1. Add API change detection in CI/CD
2. Create test helper for common patterns
3. Standardize fixture naming and usage
4. Add test coverage metrics to track progress

---

**Status:** 📋 TODO LIST READY  
**Next Action:** Start with TODO 1 (progress tracker)  
**Estimated Total Time:** 12.75-18.75 hours  
**Expected Outcome:** 95-100% pass rate

