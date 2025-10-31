**Date:** October 24, 2025  
**Status:** Skipped Tests Analysis & Recovery Plan  
**Coverage:** 315 Skipped Tests Across Unit, Integration, Functional  

# Skipped Tests Analysis & Recovery Plan

## Executive Summary

Current test suite has 315 skipped tests that were disabled due to:
1. API changes (outdated test expectations)
2. Missing imports/modules
3. Infrastructure dependencies
4. Fixture issues

**Goal:** Systematically enable skipped tests by:
- Leveraging existing codebase
- Refactoring tests to match current APIs
- Adding missing infrastructure
- Fixing import/fixture issues

## Current Status

```
Total Tests: 990
Passing: 670 (67.7%)
Failing: 5 (0.5%) - known missing endpoints
Skipped: 315 (31.8%)
```

## Skipped Tests Breakdown

### Unit Tests (~155 skipped)
**Categories:**
1. **Cache Decorator (6 tests)** - Old caching API
2. **Data Isolation (9 tests)** - TestDataMarker dict vs model
3. **Dependency Manager (all)** - API restructured
4. **Enhanced Model Router (2 classes)** - CodeDetector changes
5. **Hierarchical Context (2 classes)** - Service model changes
6. **Processing Planner (all)** - create_plan signature changed
7. **Progress Tracker (1 class)** - Edge case handling
8. **Repository Scanner (1 class)** - Private methods removed
9. **Resilience (1 class)** - CircuitBreaker config changed
10. **Resource Allocator (all)** - deallocate method removed
11. **Snapshot Processor (all)** - Binary detection changed
12. **Stack Detector (2 tests)** - Framework patterns updated

### Integration Tests (~160 skipped)
**Categories:**
1. **End-to-End Tests (4 files)** - Require running server
   - caching_integration
   - complete_api_coverage
   - container_management
   - documents_endpoints
2. **Fixture Issues (3 files)** - Missing fixtures
   - context_aware_rag
   - dynamic_rag_api
   - hardening
3. **API Changes (1 file)** - Object vs dict
   - discovery_to_execution

### Functional Tests (~110 skipped)
**Categories:**
1. **Documentation Runs (5 classes)** - API changed
   - TestDocumentAssociation
   - TestRunStatusManagement
   - TestRunComparison
   - TestRunCleanup
   - TestRunExport
2. **Error Recovery (all)** - Import errors, infrastructure
3. **Full Pipeline (2 classes)** - Relative import errors
4. **Temporal Versioning (6 classes)** - Missing imports
5. **Timeline Workflow (1 test)** - Requires Ollama

## Recovery Strategy

### Phase 1: Quick Wins (Low Effort, High Impact)
**Target: ~50 tests**

1. **Fix Import Issues**
   - Add missing imports for ContentAddressableStorage
   - Fix relative import errors
   - Add missing module imports

2. **Update Simple API Changes**
   - Stack Detector framework patterns
   - Enhanced Model Router CodeDetector
   - Progress Tracker edge cases

3. **Fix Fixture Issues**
   - Create missing fixtures (client, mock_rag, mock_context)
   - Update fixture signatures

### Phase 2: API Refactoring (Medium Effort)
**Target: ~100 tests**

1. **Data Isolation Tests**
   - Refactor to use DocumentModel attributes instead of dict
   - Update TestDataMarker to work with models

2. **Dependency Manager**
   - Update to current API
   - Fix method signatures

3. **Processing Planner**
   - Update create_plan signature
   - Fix ProcessingPlan object vs dict

4. **Documentation Runs**
   - Implement missing methods or update tests
   - Fix RunStatus enum

### Phase 3: Infrastructure & Complex Refactors (High Effort)
**Target: ~100 tests**

1. **Cache Decorator**
   - Update to current caching API
   - Fix Redis integration

2. **End-to-End Tests**
   - Create test fixtures that don't require running server
   - Use TestClient instead of httpx

3. **Error Recovery**
   - Fix ollama_client imports
   - Fix psycopg2.pool issues

4. **Temporal Versioning**
   - Add ContentAddressableStorage implementation
   - Fix TemporalVersionManager

### Phase 4: Optional/Low Priority
**Target: ~65 tests**

1. **Resource Allocator** - deallocate method removed (may not be needed)
2. **Snapshot Processor** - Binary detection changed (may not be needed)
3. **Resilience** - CircuitBreaker config (working differently now)

## Implementation Plan

### Week 1: Phase 1 (Quick Wins)
- Day 1-2: Fix import issues
- Day 3-4: Update simple API changes
- Day 5: Fix fixture issues

### Week 2: Phase 2 (API Refactoring)
- Day 1-2: Data Isolation & Dependency Manager
- Day 3-4: Processing Planner & Documentation Runs
- Day 5: Testing & validation

### Week 3: Phase 3 (Infrastructure)
- Day 1-2: Cache Decorator & End-to-End Tests
- Day 3-4: Error Recovery & Temporal Versioning
- Day 5: Testing & validation

## Success Metrics

**Target Goals:**
- Enable 200+ skipped tests (63% recovery)
- Maintain 100% pass rate for enabled tests
- Comprehensive documentation for remaining skips
- Zero new bugs introduced

**Stretch Goals:**
- Enable 250+ skipped tests (79% recovery)
- Achieve 95%+ overall pass rate
- Complete infrastructure for all test types

## Risk Assessment

**Low Risk:**
- Import fixes
- Simple API updates
- Fixture creation

**Medium Risk:**
- API refactoring (may break existing code)
- Data model changes
- Method signature updates

**High Risk:**
- Infrastructure changes (cache, database)
- End-to-end test setup
- Complex refactors

## Next Steps

1. Start with Phase 1: Quick Wins
2. Create tracking document for progress
3. Commit after each major milestone
4. Document any API changes discovered
5. Update this plan as we learn more

---

**Note:** This is a living document. Update as we progress through phases.

